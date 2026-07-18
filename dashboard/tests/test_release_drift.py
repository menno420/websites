"""Release-drift parity on /status (dashboard slice).

The review service bakes release-drift to review/data/releases.json (top-level
{generated_at, note, entries:[...], drift_count}; each entry carries a producer
``drift`` bool). This dashboard surface NEVER recomputes drift and never imports
review's package — it re-renders the already-baked signal over the raw feed.

These tests pin the pure shaper (honest degrade, never re-derives the flag) and
the /status route (drift entries + count surface when present; no card when clean).
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from dashboard import app as app_module
from dashboard import control_plane as cp
from dashboard import data_source as ds

from dashboard.tests.test_dashboard import (
    ARCADE_FIXTURE,
    CONSOLE_FIXTURE,
    DASHBOARD_FIXTURE,
)

# A releases mirror with exactly one drifting entry (X) and one clean entry (Y).
RELEASES_FIXTURE = {
    "generated_at": "2026-07-18T00:00:00Z",
    "note": "baked by review",
    "drift_count": 1,
    "entries": [
        {"slug": "x", "name": "X", "source_repo": "menno420/x", "expected_tag": "v1",
         "live_tag": None, "drift": True, "reason": "live tag behind expected"},
        {"slug": "y", "name": "Y", "source_repo": "menno420/y", "expected_tag": "v2",
         "live_tag": "v2", "drift": False, "reason": ""},
    ],
}


# --- pure shaper ----------------------------------------------------------
def test_release_drift_filters_to_drifting_entries():
    """Only producer-flagged drift entries survive; count == len; generated_at kept.
    Never re-derives the flag (Y is drift=False, so it is dropped)."""
    out = ds.release_drift(RELEASES_FIXTURE)
    assert out["count"] == 1
    assert [e["name"] for e in out["entries"]] == ["X"]
    assert out["generated_at"] == "2026-07-18T00:00:00Z"


def test_release_drift_minimal_shape():
    """A bare {entries:[...]} without generated_at degrades generated_at to ''."""
    out = ds.release_drift(
        {"entries": [
            {"name": "X", "drift": True, "expected_tag": "v1", "live_tag": None},
            {"name": "Y", "drift": False},
        ]}
    )
    assert out["count"] == 1
    assert out["entries"][0]["name"] == "X"
    assert out["generated_at"] == ""


@pytest.mark.parametrize("bad", [None, {}, {"entries": []}, {"entries": None}])
def test_release_drift_empty_and_none_safe(bad):
    """Missing/empty/None input degrades to an empty list, count 0, never raises."""
    out = ds.release_drift(bad)
    assert out == {"entries": [], "count": 0, "generated_at": ""} or (
        out["count"] == 0 and out["entries"] == []
    )


# --- /status route --------------------------------------------------------
def _client(releases):
    ds.clear_cache()
    cp.controller.clear()
    ds.prime_cache(ds.DASHBOARD_JSON_URL, DASHBOARD_FIXTURE)
    ds.prime_cache(ds.CONSOLE_JSON_URL, CONSOLE_FIXTURE)
    ds.prime_cache(ds.ARCADE_JSON_URL, ARCADE_FIXTURE)
    ds.prime_cache(ds.RELEASES_JSON_URL, releases)
    ds.set_client(ds.make_client())
    return TestClient(app_module.app)


def test_status_shows_release_drift_card_when_drifting():
    """A drifting mirror surfaces the count + the drifting entry's name on /status."""
    with _client(RELEASES_FIXTURE) as c:
        r = c.get("/status")
        assert r.status_code == 200
        assert "1 release drifting" in r.text
        assert "X" in r.text
        assert "expected v1 vs live none" in r.text
        # The clean entry (Y) is not surfaced as a drift row.
        assert "review's committed release mirror" in r.text
    ds.clear_cache()
    cp.controller.clear()


def test_status_no_card_when_no_drift():
    """No drift -> no card (honest: never a faked zero-state card)."""
    with _client({"entries": [], "drift_count": 0}) as c:
        r = c.get("/status")
        assert r.status_code == 200
        assert "release drifting" not in r.text
        assert "review's committed release mirror" not in r.text
    ds.clear_cache()
    cp.controller.clear()
