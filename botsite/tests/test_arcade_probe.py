"""Arcade URL drift probe tests (live+download availabilities) — NETWORK-FREE.

Every fetch goes through ``httpx.MockTransport`` (or a client whose handler
fails the test if it is ever reached). The real network fetch runs only via
``scripts/healthcheck.py`` / the healthcheck.yml schedule — never inside the
required ``quality`` gate this file rides in.
"""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from botsite import arcade_probe


def _entry(slug: str, availability: str = "live", url: str | None = "https://example.com/") -> dict:
    return {
        "slug": slug, "name": slug.title(), "tagline": "t", "description": "d",
        "maturity": "beta", "availability": availability, "url": url,
        "source_repo": "menno420/x", "status_note": "n",
    }


def _registry(tmp_path: Path, entries: list[dict]) -> Path:
    path = tmp_path / "arcade.json"
    path.write_text(json.dumps(entries), encoding="utf-8")
    return path


def _client(handler) -> httpx.Client:
    """A client identical in shape to the probe's real one (redirects
    followed), but running on MockTransport — no socket is ever opened."""
    return httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=True)


def _never_called(request: httpx.Request) -> httpx.Response:
    raise AssertionError(f"network fetch attempted for {request.url}")


# --- probe_url verdicts ---------------------------------------------------------


def test_200_is_ok():
    with _client(lambda req: httpx.Response(200, text="hi")) as c:
        ok, note = arcade_probe.probe_url("https://example.com/", c)
    assert ok is True
    assert note == "200"


@pytest.mark.parametrize("status", [404, 500, 302])
def test_non_200_final_status_is_flagged(status):
    with _client(lambda req: httpx.Response(status)) as c:
        ok, note = arcade_probe.probe_url("https://example.com/", c)
    assert ok is False
    assert note == f"HTTP {status}"


def test_redirect_to_200_is_ok():
    """follow_redirects is deliberate: a live game behind a 301/308 is still
    live — the FINAL response must be 200."""
    def handler(req: httpx.Request) -> httpx.Response:
        if req.url.path == "/old":
            return httpx.Response(301, headers={"location": "https://example.com/new"})
        return httpx.Response(200)

    with _client(handler) as c:
        ok, note = arcade_probe.probe_url("https://example.com/old", c)
    assert ok is True and note == "200"


def test_timeout_is_flagged():
    def handler(req: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("boom", request=req)

    with _client(handler) as c:
        ok, note = arcade_probe.probe_url("https://example.com/", c)
    assert ok is False
    assert "timeout" in note and "ConnectTimeout" in note


def test_connection_error_is_flagged():
    def handler(req: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=req)

    with _client(handler) as c:
        ok, note = arcade_probe.probe_url("https://example.com/", c)
    assert ok is False
    assert "connection error" in note and "ConnectError" in note


def test_malformed_url_is_flagged_without_any_fetch():
    with _client(_never_called) as c:
        for bad in ("not-a-url", "ftp://example.com/rom", "//no-scheme", ""):
            ok, note = arcade_probe.probe_url(bad, c)
            assert ok is False, bad
            assert "malformed URL" in note


def test_unexpected_exception_degrades_to_finding_not_crash():
    """Fail-soft pin: even a surprise exception type inside the fetch becomes
    a FLAGGED finding, never a traceback out of the probe."""
    def handler(req: httpx.Request) -> httpx.Response:
        raise RuntimeError("wat")

    with _client(handler) as c:
        ok, note = arcade_probe.probe_url("https://example.com/", c)
    assert ok is False
    assert "probe error" in note and "RuntimeError" in note


# --- probe_registry_urls summaries -----------------------------------------------


def test_probed_availabilities_covered_others_skipped(tmp_path):
    """Both link-bearing availabilities (live AND download) are probed; every
    other availability is explicitly reported as skipped — never silently."""
    reg = _registry(tmp_path, [
        _entry("alive", "live", "https://example.com/game"),
        _entry("waiting", "unavailable", None),
        _entry("rom", "download", "https://example.com/rom"),
    ])
    with _client(lambda req: httpx.Response(200)) as c:
        result = arcade_probe.probe_registry_urls(reg, client=c)
    assert result["ok"] is True
    assert [r["slug"] for r in result["rows"]] == ["alive", "rom"]
    assert [r["availability"] for r in result["rows"]] == ["live", "download"]
    assert result["flagged"] == []
    # honest coverage: only the unavailable entry is NOT probed
    assert result["skipped"] == [
        {"slug": "waiting", "availability": "unavailable"},
    ]
    assert (
        "2 URL(s) probed (live+download), 0 flagged, "
        "1 other-availability entry not probed" == result["note"]
    )


def test_download_200_is_healthy(tmp_path):
    reg = _registry(tmp_path, [_entry("rom", "download", "https://example.com/rom.zip")])
    with _client(lambda req: httpx.Response(200)) as c:
        result = arcade_probe.probe_registry_urls(reg, client=c)
    assert result["ok"] is True
    (row,) = result["rows"]
    assert row["slug"] == "rom" and row["availability"] == "download"
    assert row["ok"] is True and row["note"] == "200"


def test_download_redirect_chain_to_200_is_healthy(tmp_path):
    """Release-asset idiom: GitHub 302s asset downloads to a CDN. A chain
    ending in 200 is healthy — follow_redirects already covers it."""
    reg = _registry(tmp_path, [_entry("rom", "download", "https://example.com/release")])

    def handler(req: httpx.Request) -> httpx.Response:
        if req.url.path == "/release":
            return httpx.Response(302, headers={"location": "https://cdn.example.com/rom.zip"})
        return httpx.Response(200)

    with _client(handler) as c:
        result = arcade_probe.probe_registry_urls(reg, client=c)
    assert result["ok"] is True
    (row,) = result["rows"]
    assert row["ok"] is True and row["note"] == "200"


def test_download_404_is_flagged(tmp_path):
    reg = _registry(tmp_path, [_entry("rom", "download", "https://example.com/gone.zip")])
    with _client(lambda req: httpx.Response(404)) as c:
        result = arcade_probe.probe_registry_urls(reg, client=c)
    assert result["ok"] is False
    (row,) = result["flagged"]
    assert row["slug"] == "rom" and row["availability"] == "download"
    assert row["note"] == "HTTP 404"


def test_download_timeout_is_flagged(tmp_path):
    reg = _registry(tmp_path, [_entry("rom", "download", "https://example.com/slow.zip")])

    def handler(req: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("slow", request=req)

    with _client(handler) as c:
        result = arcade_probe.probe_registry_urls(reg, client=c)
    assert result["ok"] is False
    (row,) = result["flagged"]
    assert "timeout" in row["note"]


def test_redirect_loop_is_flagged_not_hung(tmp_path):
    """A 302 pointing at itself exhausts the client's redirect budget —
    httpx raises TooManyRedirects, which degrades to a flagged finding."""
    reg = _registry(tmp_path, [_entry("loop", "download", "https://example.com/loop")])

    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(302, headers={"location": "https://example.com/loop"})

    with _client(handler) as c:
        result = arcade_probe.probe_registry_urls(reg, client=c)
    assert result["ok"] is False
    (row,) = result["flagged"]
    assert "TooManyRedirects" in row["note"]


def test_dead_live_url_is_flagged_but_never_raises(tmp_path):
    reg = _registry(tmp_path, [
        _entry("ok-game", "live", "https://example.com/ok"),
        _entry("dead-game", "live", "https://example.com/dead"),
        _entry("hung-game", "live", "https://example.com/hang"),
    ])

    def handler(req: httpx.Request) -> httpx.Response:
        if req.url.path == "/dead":
            return httpx.Response(404)
        if req.url.path == "/hang":
            raise httpx.ReadTimeout("slow", request=req)
        return httpx.Response(200)

    with _client(handler) as c:
        result = arcade_probe.probe_registry_urls(reg, client=c)
    assert result["ok"] is False
    assert len(result["rows"]) == 3
    assert [r["slug"] for r in result["flagged"]] == ["dead-game", "hung-game"]
    by_slug = {r["slug"]: r for r in result["rows"]}
    assert by_slug["ok-game"]["ok"] is True
    assert by_slug["dead-game"]["note"] == "HTTP 404"
    assert "timeout" in by_slug["hung-game"]["note"]
    assert "3 URL(s) probed (live+download), 2 flagged" in result["note"]


def test_mixed_registry_probes_live_and_download_flags_each_honestly(tmp_path):
    """One registry, every class at once: a healthy live, a dead download, a
    skipped unavailable — each lands in exactly the right bucket."""
    reg = _registry(tmp_path, [
        _entry("alive", "live", "https://example.com/game"),
        _entry("dead-rom", "download", "https://example.com/dead.zip"),
        _entry("waiting", "unavailable", None),
    ])

    def handler(req: httpx.Request) -> httpx.Response:
        if req.url.path == "/dead.zip":
            return httpx.Response(404)
        return httpx.Response(200)

    with _client(handler) as c:
        result = arcade_probe.probe_registry_urls(reg, client=c)
    assert result["ok"] is False
    assert [r["slug"] for r in result["rows"]] == ["alive", "dead-rom"]
    assert [r["slug"] for r in result["flagged"]] == ["dead-rom"]
    assert result["skipped"] == [{"slug": "waiting", "availability": "unavailable"}]


@pytest.mark.parametrize("availability", ["live", "download"])
def test_probed_entry_with_no_url_is_flagged(tmp_path, availability):
    reg = _registry(tmp_path, [_entry("linkless", availability, None)])
    with _client(_never_called) as c:
        result = arcade_probe.probe_registry_urls(reg, client=c)
    assert result["ok"] is False
    (row,) = result["rows"]
    assert row["slug"] == "linkless" and row["ok"] is False and row["url"] is None
    assert row["availability"] == availability
    assert f'availability "{availability}" but no URL to probe' == row["note"]


def test_live_entry_with_malformed_url_is_flagged(tmp_path):
    reg = _registry(tmp_path, [_entry("garbled", "live", "not a url at all")])
    with _client(_never_called) as c:
        result = arcade_probe.probe_registry_urls(reg, client=c)
    assert result["ok"] is False
    (row,) = result["flagged"]
    assert row["slug"] == "garbled"
    assert "malformed URL" in row["note"]


def test_zero_entry_registry_is_a_flagged_condition(tmp_path):
    """A registry that loads to nothing (missing/corrupt file) must ALERT —
    the committed registry lists three games; zero means the probe is blind
    (mirrors the fleet-registry zero-lanes alert)."""
    missing = tmp_path / "does-not-exist.json"
    result = arcade_probe.probe_registry_urls(missing, client=None)
    assert result["ok"] is False
    assert result["rows"] == [] and result["skipped"] == []
    assert "ZERO entries" in result["note"]


# --- single source of truth: probe coverage IS the page's linked set -------------


def test_probe_coverage_is_the_pages_linked_set():
    """THE pin this slice exists for: the probe's coverage tuple IS the page's
    link-bearing tuple (``arcade.LINKED_AVAILABILITIES``) — one object, not
    two literals that happen to agree — so a new link-bearing availability
    can never be linked on /arcade yet silently unprobed (or vice versa)."""
    from botsite import arcade

    assert arcade_probe.PROBED_AVAILABILITIES is arcade.LINKED_AVAILABILITIES
    assert set(arcade_probe.PROBED_AVAILABILITIES) == set(arcade.LINKED_AVAILABILITIES)


def test_linked_availabilities_are_valid_and_exclude_unavailable():
    """Sanity pins on the constant itself: every linked availability is a real
    registry availability, none repeats, and ``unavailable`` never links."""
    from botsite import arcade

    assert set(arcade.LINKED_AVAILABILITIES) <= set(arcade.AVAILABILITIES)
    assert len(set(arcade.LINKED_AVAILABILITIES)) == len(arcade.LINKED_AVAILABILITIES)
    assert "unavailable" not in arcade.LINKED_AVAILABILITIES


def test_probe_partitions_registry_exactly_by_linked_availabilities(tmp_path):
    """Behavior pin: with one URL-bearing entry per registry availability, the
    probed/skipped partition is EXACTLY the linked/non-linked split — driven
    by the shared constant, not by any list hardcoded here."""
    from botsite import arcade

    reg = _registry(tmp_path, [
        _entry(f"g-{a}", a, "https://example.com/g") for a in arcade.AVAILABILITIES
    ])
    with _client(lambda req: httpx.Response(200)) as c:
        result = arcade_probe.probe_registry_urls(reg, client=c)
    assert [r["slug"] for r in result["rows"]] == [
        f"g-{a}" for a in arcade.AVAILABILITIES if a in arcade.LINKED_AVAILABILITIES
    ]
    assert [s["slug"] for s in result["skipped"]] == [
        f"g-{a}" for a in arcade.AVAILABILITIES if a not in arcade.LINKED_AVAILABILITIES
    ]


def test_committed_registry_linked_set_matches_probe_coverage():
    """Coverage pin against the committed registry (no network: nothing is
    fetched, we only assert WHAT WOULD BE probed): exactly the entries the
    /arcade page renders an outbound link for (live + download)."""
    from botsite import arcade

    games = arcade.load_games()
    linked = [
        g["slug"] for g in games
        if g["availability"] in arcade_probe.PROBED_AVAILABILITIES
    ]
    with _client(lambda req: httpx.Response(200)) as c:
        result = arcade_probe.probe_registry_urls(client=c)
    assert [r["slug"] for r in result["rows"]] == linked
    assert {s["slug"] for s in result["skipped"]} == {
        g["slug"] for g in games
        if g["availability"] not in arcade_probe.PROBED_AVAILABILITIES
    }
