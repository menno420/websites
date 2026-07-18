"""Release-drift parity on the console board (/) — control-plane slice.

The review service bakes release-drift to review/data/releases.json (committed in
THIS repo). The board re-renders that already-baked signal over the shared,
token-free raw path (app.releasedrift), never recomputing drift and never
importing review's package.

These tests pin the pure shaper (honest degrade, never re-derives the ``drift``
flag) and the board route (a drift chip surfaces when the producer flagged drift;
nothing when clean or when the fetch fails).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app import github, releasedrift  # noqa: E402
from app.main import app  # noqa: E402

# A releases mirror with one drifting entry (X) and one clean entry (Y).
RELEASES = {
    "generated_at": "2026-07-18T00:00:00Z",
    "note": "baked by review",
    "drift_count": 1,
    "entries": [
        {"slug": "x", "name": "X", "source_repo": "menno420/x", "expected_tag": "v1",
         "live_tag": None, "drift": True, "reason": "behind"},
        {"slug": "y", "name": "Y", "source_repo": "menno420/y", "expected_tag": "v2",
         "live_tag": "v2", "drift": False, "reason": ""},
    ],
}


def _res(ok=True, status=200, data=None, error=""):
    return {"ok": ok, "status": status, "data": data, "error": error,
            "fetched_at": "", "cached": False, "url": ""}


# --- pure shaper ----------------------------------------------------------
def test_shape_filters_to_drifting_entries():
    """Only producer-flagged drift entries survive; count == len; keeps generated_at.
    Never re-derives the flag (Y is drift=False → dropped)."""
    out = releasedrift.shape(RELEASES)
    assert out["count"] == 1
    assert [e["name"] for e in out["entries"]] == ["X"]
    assert out["generated_at"] == "2026-07-18T00:00:00Z"


def test_shape_empty_when_no_drift():
    out = releasedrift.shape({"entries": [{"name": "Y", "drift": False}], "drift_count": 0})
    assert out == {"entries": [], "count": 0, "generated_at": ""}


def test_shape_degrades_on_bad_input():
    """Missing/None/non-dict/misshaped input degrades to count 0, never raises."""
    for bad in (None, {}, "nope", 42, {"entries": None}, {"entries": ["not-a-dict"]}):
        out = releasedrift.shape(bad)
        assert out["count"] == 0 and out["entries"] == []


# --- board route ----------------------------------------------------------
def _mock(monkeypatch, releases_data=None, releases_ok=True):
    """All GitHub fetches degrade offline; the releases mirror URL is served
    (or failed) per the test so the board never hits the network."""
    async def fake_get(url, refresh=False, raw=False):
        if url == releasedrift.RELEASES_JSON_URL:
            if releases_ok and releases_data is not None:
                return _res(data=releases_data)
            return _res(ok=False, status=0, error="offline")
        return _res(ok=False, status=0, data=None, error="offline test")

    async def fake_api(repo, subpath="", refresh=False):
        return _res(ok=False, status=404, data=None, error="nf")

    async def fake_fetch(repo, path, ref="main", refresh=False):
        return _res(ok=False, status=404, data=None, error="nf")

    monkeypatch.setattr(github, "_get", fake_get)
    monkeypatch.setattr(github, "repo_api", fake_api)
    monkeypatch.setattr(github, "fetch_file", fake_fetch)


def test_board_shows_release_drift_chip_when_drifting(monkeypatch):
    _mock(monkeypatch, releases_data=RELEASES)
    with TestClient(app) as c:
        r = c.get("/")
    assert r.status_code == 200
    assert "1 release drifting" in r.text
    assert "baked from review's committed release mirror" in r.text


def test_board_no_chip_when_no_drift(monkeypatch):
    _mock(monkeypatch, releases_data={"entries": [], "drift_count": 0})
    with TestClient(app) as c:
        r = c.get("/")
    assert r.status_code == 200
    assert "release" not in r.text or "drifting" not in r.text
    assert "committed release mirror" not in r.text


def test_board_no_chip_when_fetch_fails(monkeypatch):
    """A failed releases fetch degrades to no chip — never a faked drift indicator."""
    _mock(monkeypatch, releases_ok=False)
    with TestClient(app) as c:
        r = c.get("/")
    assert r.status_code == 200
    assert "drifting" not in r.text
    assert "committed release mirror" not in r.text
