"""/fleet.json shape contract — pinned key sets for machine consumers.

The `/fleet.json` payload is machine-read by the manager (outstanding work,
claim state, wake-clock health, kit adoption) and reused inside `/queue` and
`/orders`. It was extended three times on 2026-07-10 alone — an accidental
key rename would break those consumers SILENTLY today. This file pins the
exact shape the same way the dashboard pins superbot's console.json
(pinned-contract lesson): any key added, removed, or renamed goes RED here
by name, so the contract is changed consciously — update these sets in the
SAME PR that changes the payload, and say so in the PR body.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app import github  # noqa: E402
from app.main import app  # noqa: E402

# --- the pinned contract ---------------------------------------------------

# coverage added 2026-07-12 (fleet coverage-chip PR): seat-package
# role-coverage rollup (projects.coverage_rollup) — the /fleet chip's data.
TOP_KEYS = {"lanes", "summary", "stale_hours", "lane_source", "registry_url",
            "coverage"}

# lane_status() output minus body_html (the JSON route strips rendered HTML).
# status_file_url / current_state_url added 2026-07-12 (console-home PR):
# in-app /journal/{repo}/file deep-links, None outside the render allow-set.
LANE_KEYS = {
    "lane", "repo", "status_path", "model", "note", "github_url", "repo_url",
    "status_file_url", "current_state_url",
    "last_commit", "open_prs", "missing", "fetch_error", "unreadable",
    "project", "fields", "health", "freshness",
    "orders_info", "routine_info", "landing_info",
}

HEALTH_KEYS = {"kind", "badge", "label"}
FRESHNESS_KEYS = {"ok", "iso", "age_hours", "age_human", "stale"}
ORDERS_INFO_KEYS = {"ok", "acked", "done", "outstanding", "claimed", "claimed_at"}
ROUTINE_INFO_KEYS = {
    "present", "armed", "silent", "no_fire_recorded", "cron", "fired_age_human",
}
LANDING_INFO_KEYS = {"present", "kind", "attention", "branch"}

SUMMARY_KEYS = {
    "total", "healthy", "stale", "broken", "errored", "no_file",
    "stranded", "silent_routines", "outstanding_orders", "kit_versions",
}
KIT_VERSION_ITEM_KEYS = {"version", "count"}

COVERAGE_KEYS = {
    "state", "reason", "seats", "complete", "incomplete",
    "incomplete_names", "unlistable", "unlistable_names",
}

# ---------------------------------------------------------------------------

_ENRICHED = (
    "# lane · status\n"
    "updated: 2026-07-10T20:30Z\n"
    "health: green (fine)\n"
    "kit: v1.7.1 · check: green · engaged: yes\n"
    "routine: armed · cron 0 */4 * * * · last-fired 2026-07-10T20:00Z\n"
    "landing: all-merged\n"
    "deployed: abc1234 · verified 2026-07-10T20:15Z\n"
    "orders: acked=001-002 done=001 claimed-by: 002 lane 2026-07-10T21:07Z\n"
)


def _mock(monkeypatch):
    async def fake_fetch(repo, path, ref="main", refresh=False):
        if path.startswith("control/status"):
            return {"ok": True, "status": 200, "data": _ENRICHED, "error": "",
                    "fetched_at": "", "cached": False, "url": ""}
        return {"ok": False, "status": 404, "data": None, "error": "nf",
                "fetched_at": "", "cached": False, "url": ""}

    async def fake_api(repo, subpath="", refresh=False):
        return {"ok": False, "status": 404, "data": None, "error": "nf",
                "fetched_at": "", "cached": False, "url": ""}

    monkeypatch.setattr(github, "fetch_file", fake_fetch)
    monkeypatch.setattr(github, "repo_api", fake_api)


def _payload(monkeypatch):
    _mock(monkeypatch)
    r = TestClient(app).get("/fleet.json")
    assert r.status_code == 200
    return r.json()


def test_top_level_and_summary_shape(monkeypatch):
    d = _payload(monkeypatch)
    assert set(d.keys()) == TOP_KEYS, (
        f"top-level contract drift: {sorted(set(d) ^ TOP_KEYS)}"
    )
    assert set(d["summary"].keys()) == SUMMARY_KEYS, (
        f"summary contract drift: {sorted(set(d['summary']) ^ SUMMARY_KEYS)}"
    )
    for item in d["summary"]["kit_versions"]:
        assert set(item.keys()) == KIT_VERSION_ITEM_KEYS
    assert set(d["coverage"].keys()) == COVERAGE_KEYS, (
        f"coverage contract drift: {sorted(set(d['coverage']) ^ COVERAGE_KEYS)}"
    )
    # This fixture 404s every repo_api call, so the registry listing is
    # unreadable — the rollup must be an honest unknown, never a zero.
    assert d["coverage"]["state"] == "unknown"


def test_lane_shape_including_parsed_structures(monkeypatch):
    d = _payload(monkeypatch)
    assert d["lanes"], "no lanes rendered — the contract test needs one"
    for lane in d["lanes"]:
        assert set(lane.keys()) == LANE_KEYS, (
            f"lane contract drift ({lane['lane']}): "
            f"{sorted(set(lane) ^ LANE_KEYS)}"
        )
        assert "body_html" not in lane  # rendered HTML never ships in JSON
        assert set(lane["health"].keys()) == HEALTH_KEYS
        assert set(lane["freshness"].keys()) == FRESHNESS_KEYS
        assert set(lane["orders_info"].keys()) == ORDERS_INFO_KEYS, (
            f"orders_info drift: "
            f"{sorted(set(lane['orders_info']) ^ ORDERS_INFO_KEYS)}"
        )
        assert set(lane["routine_info"].keys()) == ROUTINE_INFO_KEYS, (
            f"routine_info drift: "
            f"{sorted(set(lane['routine_info']) ^ ROUTINE_INFO_KEYS)}"
        )
        assert set(lane["landing_info"].keys()) == LANDING_INFO_KEYS, (
            f"landing_info drift: "
            f"{sorted(set(lane['landing_info']) ^ LANDING_INFO_KEYS)}"
        )


def test_contract_holds_for_degraded_lanes_too(monkeypatch):
    """A missing/errored lane carries the SAME key set (defaults, honest
    empties) — consumers never need per-state key handling."""

    async def all_404(repo, path, ref="main", refresh=False):
        return {"ok": False, "status": 404, "data": None, "error": "nf",
                "fetched_at": "", "cached": False, "url": ""}

    async def fake_api(repo, subpath="", refresh=False):
        return {"ok": False, "status": 404, "data": None, "error": "nf",
                "fetched_at": "", "cached": False, "url": ""}

    monkeypatch.setattr(github, "fetch_file", all_404)
    monkeypatch.setattr(github, "repo_api", fake_api)
    d = TestClient(app).get("/fleet.json").json()
    for lane in d["lanes"]:
        assert set(lane.keys()) == LANE_KEYS
        assert lane["missing"] is True
        assert set(lane["orders_info"].keys()) == ORDERS_INFO_KEYS
        assert set(lane["routine_info"].keys()) == ROUTINE_INFO_KEYS
        assert set(lane["landing_info"].keys()) == LANDING_INFO_KEYS
