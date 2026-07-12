"""Tester-task URL liveness guard tests (open-task product_urls) — NETWORK-FREE.

Every fetch goes through ``httpx.MockTransport`` (or a client whose handler
fails the test if it is ever reached). The real network fetch runs only via
``scripts/healthcheck.py`` / the healthcheck.yml schedule — never inside the
required ``quality`` gate this file rides in.

The per-URL verdict logic (redirect chains, timeout wording, malformed-URL
detection …) is IMPORTED from ``botsite/arcade_probe.py`` and unit-tested in
``botsite/tests/test_arcade_probe.py``; this file pins the tester-task
catalog semantics on top of it.
"""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from botsite import arcade_probe, testing_probe


def _task(task_id: str, status: str = "open", url: str | None = "https://example.com/") -> dict:
    return {
        "id": task_id, "type": "site-review", "title": task_id.title(),
        "product_url": url, "brief": "b", "payout_usd": 10,
        "est_minutes": 30, "slots_total": 3, "status": status, "note": "",
    }


def _catalog(tmp_path: Path, tasks: list[dict]) -> Path:
    path = tmp_path / "testing_tasks.json"
    path.write_text(json.dumps({"tasks": tasks}), encoding="utf-8")
    return path


def _client(handler) -> httpx.Client:
    """A client identical in shape to the probe's real one (redirects
    followed), but running on MockTransport — no socket is ever opened."""
    return httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=True)


def _never_called(request: httpx.Request) -> httpx.Response:
    raise AssertionError(f"network fetch attempted for {request.url}")


# --- shared verdict logic pin -----------------------------------------------------


def test_verdicts_are_the_arcade_probes_not_a_fork():
    """The guard's whole guarantee mirrors the arcade probe's; pin that the
    per-URL verdict function IS the arcade one, not a diverging copy."""
    assert testing_probe.probe_url is arcade_probe.probe_url
    assert testing_probe.TIMEOUT_S == arcade_probe.TIMEOUT_S


# --- probe_task_urls summaries ----------------------------------------------------


def test_open_task_200_is_healthy_no_finding(tmp_path):
    cat = _catalog(tmp_path, [_task("t1", "open", "https://example.com/app")])
    with _client(lambda req: httpx.Response(200)) as c:
        result = testing_probe.probe_task_urls(cat, client=c)
    assert result["ok"] is True
    (row,) = result["rows"]
    assert row["id"] == "t1" and row["status"] == "open"
    assert row["ok"] is True and row["note"] == "200"
    assert result["flagged"] == []
    assert result["note"] == (
        "1 open-task URL(s) probed, 0 flagged, 0 other-status tasks not probed"
    )


def test_open_task_non_200_is_flagged(tmp_path):
    cat = _catalog(tmp_path, [_task("t1", "open", "https://example.com/gone")])
    with _client(lambda req: httpx.Response(404)) as c:
        result = testing_probe.probe_task_urls(cat, client=c)
    assert result["ok"] is False
    (row,) = result["flagged"]
    assert row["id"] == "t1" and row["note"] == "HTTP 404"


def test_open_task_redirect_chain_to_200_is_healthy(tmp_path):
    """Railway idiom: hosting moves interpose 301/308 freely — a chain
    ending in 200 is healthy, follow_redirects already covers it."""
    cat = _catalog(tmp_path, [_task("t1", "open", "https://example.com/old")])

    def handler(req: httpx.Request) -> httpx.Response:
        if req.url.path == "/old":
            return httpx.Response(308, headers={"location": "https://example.com/new"})
        return httpx.Response(200)

    with _client(handler) as c:
        result = testing_probe.probe_task_urls(cat, client=c)
    assert result["ok"] is True
    (row,) = result["rows"]
    assert row["ok"] is True and row["note"] == "200"


def test_open_task_timeout_is_flagged_fail_soft(tmp_path):
    cat = _catalog(tmp_path, [_task("t1", "open", "https://example.com/slow")])

    def handler(req: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("boom", request=req)

    with _client(handler) as c:
        result = testing_probe.probe_task_urls(cat, client=c)  # must not raise
    assert result["ok"] is False
    (row,) = result["flagged"]
    assert "timeout" in row["note"] and "ConnectTimeout" in row["note"]


def test_open_task_connection_error_is_flagged_fail_soft(tmp_path):
    cat = _catalog(tmp_path, [_task("t1", "open", "https://example.com/dead-host")])

    def handler(req: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=req)

    with _client(handler) as c:
        result = testing_probe.probe_task_urls(cat, client=c)
    assert result["ok"] is False
    (row,) = result["flagged"]
    assert "connection error" in row["note"]


def test_open_task_malformed_url_is_flagged_without_any_fetch(tmp_path):
    cat = _catalog(tmp_path, [_task("t1", "open", "not a url at all")])
    with _client(_never_called) as c:
        result = testing_probe.probe_task_urls(cat, client=c)
    assert result["ok"] is False
    (row,) = result["flagged"]
    assert row["id"] == "t1" and "malformed URL" in row["note"]


@pytest.mark.parametrize("url", ["", None])
def test_open_task_missing_url_is_flagged_without_any_fetch(tmp_path, url):
    """An OPEN task with no product_url sends a paying tester nowhere — a
    finding, produced without touching the network and without crashing."""
    cat = _catalog(tmp_path, [_task("t1", "open", url)])
    with _client(_never_called) as c:
        result = testing_probe.probe_task_urls(cat, client=c)
    assert result["ok"] is False
    (row,) = result["rows"]
    assert row["ok"] is False and row["url"] is None
    assert row["note"] == 'status "open" but no product_url to probe'


@pytest.mark.parametrize("status", ["coming-soon", "closed"])
def test_non_open_task_is_skipped_and_never_fetched(tmp_path, status):
    """coming-soon/closed tasks link no product on /testing — the guard
    reports them explicitly as not probed and never opens a socket for
    them, even when they carry a URL."""
    cat = _catalog(tmp_path, [_task("t1", status, "https://example.com/app")])
    with _client(_never_called) as c:
        result = testing_probe.probe_task_urls(cat, client=c)
    assert result["ok"] is True
    assert result["rows"] == [] and result["flagged"] == []
    assert result["skipped"] == [{"id": "t1", "status": status}]
    assert "1 other-status task not probed" in result["note"]


def test_mixed_catalog_buckets_every_task_honestly(tmp_path):
    """One catalog, every class at once: a healthy open, a dead open, a
    skipped coming-soon — each lands in exactly the right bucket."""
    cat = _catalog(tmp_path, [
        _task("alive", "open", "https://example.com/ok"),
        _task("dead", "open", "https://example.com/dead"),
        _task("waiting", "coming-soon", ""),
    ])

    def handler(req: httpx.Request) -> httpx.Response:
        if req.url.path == "/dead":
            return httpx.Response(503)
        return httpx.Response(200)

    with _client(handler) as c:
        result = testing_probe.probe_task_urls(cat, client=c)
    assert result["ok"] is False
    assert [r["id"] for r in result["rows"]] == ["alive", "dead"]
    assert [r["id"] for r in result["flagged"]] == ["dead"]
    by_id = {r["id"]: r for r in result["rows"]}
    assert by_id["alive"]["ok"] is True
    assert by_id["dead"]["note"] == "HTTP 503"
    assert result["skipped"] == [{"id": "waiting", "status": "coming-soon"}]
    assert "2 open-task URL(s) probed, 1 flagged" in result["note"]


def test_zero_task_catalog_is_a_flagged_condition(tmp_path):
    """A catalog that loads to nothing must ALERT — the committed catalog
    lists eight tasks; zero means the guard is blind (mirrors the arcade
    probe's zero-entries alert)."""
    cat = _catalog(tmp_path, [])
    result = testing_probe.probe_task_urls(cat, client=None)
    assert result["ok"] is False
    assert result["rows"] == [] and result["skipped"] == []
    assert "ZERO tasks" in result["note"]


def test_missing_catalog_file_degrades_to_finding_not_crash(tmp_path):
    missing = tmp_path / "does-not-exist.json"
    result = testing_probe.probe_task_urls(missing, client=None)  # must not raise
    assert result["ok"] is False
    assert result["rows"] == []
    assert "catalog failed to load" in result["note"]


def test_corrupt_catalog_file_degrades_to_finding_not_crash(tmp_path):
    corrupt = tmp_path / "testing_tasks.json"
    corrupt.write_text("{not json", encoding="utf-8")
    result = testing_probe.probe_task_urls(corrupt, client=None)  # must not raise
    assert result["ok"] is False
    assert "catalog failed to load" in result["note"]


def test_committed_catalog_open_set_matches_probe_coverage():
    """Coverage pin against the committed catalog (no network: every probed
    URL is answered by MockTransport, we only assert WHAT WOULD BE probed):
    exactly the tasks /testing shows as open — through the SAME loader the
    page renders with."""
    from botsite import testing_catalog

    tasks = testing_catalog.load_tasks()
    assert tasks, "committed catalog must not be empty"
    open_ids = [
        t["id"] for t in tasks if t.get("status") in testing_probe.PROBED_STATUSES
    ]
    with _client(lambda req: httpx.Response(200)) as c:
        result = testing_probe.probe_task_urls(client=c)
    assert [r["id"] for r in result["rows"]] == open_ids
    assert {s["id"] for s in result["skipped"]} == {
        t["id"] for t in tasks
        if t.get("status") not in testing_probe.PROBED_STATUSES
    }
    # every committed OPEN task must carry a probeable product_url —
    # a bare 200-for-everything transport means any flag is a catalog bug
    assert result["flagged"] == []


def test_route_loader_is_the_probe_loader():
    """The /testing routes and the guard must read the catalog through the
    SAME loader — coverage and page content can never disagree."""
    from botsite import testing, testing_catalog

    assert testing.load_tasks is testing_catalog.load_tasks
    assert testing.TASKS_PATH == testing_catalog.TASKS_PATH
