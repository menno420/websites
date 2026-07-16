"""Catalog sha-drift probe tests — NETWORK-FREE.

Every fetch goes through ``httpx.MockTransport``. The real network fetch
runs only via ``scripts/healthcheck.py`` / the healthcheck.yml schedule —
never inside the required ``quality`` gate this file rides in (same
doctrine as ``test_arcade_probe.py``).
"""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from botsite import catalog_sha_drift as csd

RAW = "https://raw.githubusercontent.com/menno420"


def _entry(slug: str, source: str) -> dict:
    return {
        "slug": slug, "title": slug.title(), "category": "c", "kind": "digital-product",
        "price": "$0", "status": "live", "status_note": "n", "source": source,
        "as_of": "2026-07-13",
    }


def _registry(tmp_path: Path, entries: list[dict]) -> Path:
    path = tmp_path / "catalog.json"
    path.write_text(json.dumps(entries), encoding="utf-8")
    return path


def _client(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=True)


# --- parse_source grammar -------------------------------------------------------


def test_parse_source_well_formed():
    assert csd.parse_source(
        "venture-lab docs/publishing/vetting/foo.md @ 2c039e3"
    ) == ("venture-lab", "docs/publishing/vetting/foo.md", "2c039e3")


@pytest.mark.parametrize(
    "source",
    [
        "",
        "free text with no pin",
        "venture-lab docs/publishing/vetting/foo.md",  # no "@ sha"
        "venture-lab docs/publishing/vetting/foo.md @ not-hex",
        "venture-lab @ 2c039e3",  # missing path
    ],
)
def test_parse_source_rejects_non_pinned_shapes(source):
    assert csd.parse_source(source) is None


# --- probe_catalog_sha_drift verdicts -------------------------------------------


def test_unchanged_since_pin_is_ok(tmp_path: Path):
    path = _registry(
        tmp_path, [_entry("foo", "venture-lab docs/vetting/foo.md @ abc1234")]
    )

    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="same content")

    with _client(handler) as c:
        result = csd.probe_catalog_sha_drift(path, client=c)
    assert result["ok"] is True
    assert result["flagged"] == []
    assert result["rows"][0]["note"] == "unchanged since pin"


def test_changed_since_pin_is_flagged(tmp_path: Path):
    path = _registry(
        tmp_path, [_entry("foo", "venture-lab docs/vetting/foo.md @ abc1234")]
    )

    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=("pinned" if "abc1234" in str(req.url) else "changed"))

    with _client(handler) as c:
        result = csd.probe_catalog_sha_drift(path, client=c)
    assert result["ok"] is False
    assert len(result["flagged"]) == 1
    assert "changed upstream" in result["flagged"][0]["note"]


def test_pinned_sha_unreachable_is_flagged(tmp_path: Path):
    path = _registry(
        tmp_path, [_entry("foo", "venture-lab docs/vetting/foo.md @ abc1234")]
    )

    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(404 if "abc1234" in str(req.url) else 200, text="x")

    with _client(handler) as c:
        result = csd.probe_catalog_sha_drift(path, client=c)
    assert result["ok"] is False
    assert "pinned sha unreachable" in result["flagged"][0]["note"]
    assert "HTTP 404" in result["flagged"][0]["note"]


def test_main_unreachable_is_flagged(tmp_path: Path):
    path = _registry(
        tmp_path, [_entry("foo", "venture-lab docs/vetting/foo.md @ abc1234")]
    )

    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200 if "abc1234" in str(req.url) else 404, text="x")

    with _client(handler) as c:
        result = csd.probe_catalog_sha_drift(path, client=c)
    assert result["ok"] is False
    assert "main unreachable" in result["flagged"][0]["note"]


def test_non_pinned_source_is_skipped_not_flagged(tmp_path: Path):
    path = _registry(tmp_path, [_entry("foo", "free text, no pin here")])

    with _client(lambda req: (_ for _ in ()).throw(AssertionError("no fetch expected"))) as c:
        result = csd.probe_catalog_sha_drift(path, client=c)
    assert result["ok"] is True  # nothing flagged — a skip is not a failure
    assert result["flagged"] == []
    assert result["skipped"] == [{"slug": "foo", "source": "free text, no pin here"}]


def test_empty_registry_is_flagged(tmp_path: Path):
    path = _registry(tmp_path, [])
    with _client(lambda req: (_ for _ in ()).throw(AssertionError("no fetch expected"))) as c:
        result = csd.probe_catalog_sha_drift(path, client=c)
    assert result["ok"] is False
    assert "ZERO entries" in result["note"]


def test_mixed_registry_end_to_end(tmp_path: Path):
    """One drifted, one clean, one unpinned — flagged/ok/skipped sort correctly."""
    path = _registry(
        tmp_path,
        [
            _entry("drifted", "venture-lab docs/vetting/drifted.md @ aaa1111"),
            _entry("clean", "venture-lab docs/vetting/clean.md @ bbb2222"),
            _entry("unpinned", "no pin on this one"),
        ],
    )

    def handler(req: httpx.Request) -> httpx.Response:
        url = str(req.url)
        if "aaa1111" in url:
            return httpx.Response(200, text="old")
        if "bbb2222" in url:
            return httpx.Response(200, text="clean content")
        if "drifted.md" in url:  # drifted's /main/ fetch
            return httpx.Response(200, text="new")
        if "clean.md" in url:  # clean's /main/ fetch
            return httpx.Response(200, text="clean content")
        raise AssertionError(f"unexpected fetch: {url}")

    with _client(handler) as c:
        result = csd.probe_catalog_sha_drift(path, client=c)
    assert [r["slug"] for r in result["flagged"]] == ["drifted"]
    assert [s["slug"] for s in result["skipped"]] == ["unpinned"]
    assert result["ok"] is False
