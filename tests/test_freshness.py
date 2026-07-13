"""Offline tests for the /freshness page (app/freshness.py).

Per-repo movement across the fleet: last commit (sha + age), last dated
session card, open PR count, heartbeat age — amber strictly PAST a
threshold (heartbeat > FLEET_STALE_HOURS, commit > COMMIT_STALE_DAYS),
honest "unknown — <reason>" on every degraded fetch, archived/hub lanes
exempt. Zero network: github._get is monkeypatched with canned envelopes
(URL-dispatch, the test_app.py idiom); route renders are frozen via
clock.NOW_OVERRIDE and direct calls pass now= (time-discipline guard).
"""

import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app import clock, config, freshness, github  # noqa: E402
from app.main import app  # noqa: E402

NOW = datetime(2026, 7, 13, 12, 0, 0, tzinfo=timezone.utc)
OWNER = config.OWNER


def _iso_minutes(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%MZ")


def _iso_seconds(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _res(url="", ok=True, status=200, data=None, error=""):
    return {"ok": ok, "status": status, "data": data, "error": error,
            "fetched_at": "", "cached": False, "url": url}


# --------------------------------------------------------------------------- #
# canned fleet: 3 registry lanes — alpha moving, beta heartbeat-stale,
# attic archived (ancient everything, exempt)
# --------------------------------------------------------------------------- #

REGISTRY = (
    "LANES = [\n"
    '    {"lane": "alpha", "repo": "alpha", "disposition": "live", "tokens": []},\n'
    '    {"lane": "beta", "repo": "beta", "disposition": "live", "tokens": []},\n'
    '    {"lane": "attic", "repo": "attic", "disposition": "archived", "tokens": []},\n'
    "]\n"
)

STATUS_ALPHA = (
    "# alpha · status\n"
    f"updated: {_iso_minutes(NOW - timedelta(hours=6))}\n"
    "health: green\n"
)
STATUS_BETA = (
    "# beta · status\n"
    f"updated: {_iso_minutes(NOW - timedelta(hours=config.FLEET_STALE_HOURS + 6))}\n"
    "health: green\n"
)
STATUS_ATTIC = (
    "# attic · status\n"
    "updated: 2026-06-01T00:00Z\n"
    "health: green\n"
)


def _commit(sha: str, date: str) -> dict:
    return {"sha": sha, "commit": {"committer": {"date": date}}}


def _happy_get(monkeypatch):
    """URL-dispatched canned envelopes for the whole 3-repo fleet."""
    commits = {
        "alpha": [_commit("aaaa1111cccc", _iso_seconds(NOW - timedelta(hours=10)))],
        "beta": [_commit("bbbb2222dddd", _iso_seconds(NOW - timedelta(hours=4)))],
        "attic": [_commit("cccc3333eeee", _iso_seconds(NOW - timedelta(days=70)))],
    }
    status = {"alpha": STATUS_ALPHA, "beta": STATUS_BETA, "attic": STATUS_ATTIC}
    pulls = {"alpha": [{"number": 1}, {"number": 2}], "beta": [], "attic": []}
    sessions = {
        "alpha": [
            {"name": "2026-07-10-bar.md"},
            {"name": "2026-07-12-foo.md"},
            {"name": "README.md"},
        ],
    }

    async def fake_get(url, refresh=False, raw=False):
        if url.endswith("/fleet-manager/main/scripts/gen_roster.py"):
            return _res(url, data=REGISTRY)
        for repo in ("alpha", "beta", "attic"):
            if url.endswith(f"/{OWNER}/{repo}/main/control/status.md"):
                return _res(url, data=status[repo])
            if f"/repos/{OWNER}/{repo}/commits" in url:
                return _res(url, data=commits[repo])
            if f"/repos/{OWNER}/{repo}/pulls" in url:
                return _res(url, data=pulls[repo])
            if url.endswith(f"/repos/{OWNER}/{repo}/contents/.sessions"):
                if repo in sessions:
                    return _res(url, data=sessions[repo])
                return _res(url, ok=False, status=404, error="Not Found")
        return _res(url, ok=False, status=404, error="Not Found")

    monkeypatch.setattr(github, "_get", fake_get)


def _offline_get(monkeypatch):
    """Everything unreachable — the fully-degraded client."""

    async def fake_get(url, refresh=False, raw=False):
        return _res(url, ok=False, status=0, error="offline test")

    monkeypatch.setattr(github, "_get", fake_get)


def _freeze(monkeypatch):
    monkeypatch.setattr(clock, "NOW_OVERRIDE", NOW)


# --------------------------------------------------------------------------- #
# (a) fully-degraded: 200, honest unknowns, no fabricated freshness
# --------------------------------------------------------------------------- #


def test_route_degrades_honestly_when_everything_is_unreachable(monkeypatch):
    _offline_get(monkeypatch)
    _freeze(monkeypatch)
    with TestClient(app) as c:
        r = c.get("/freshness")
    assert r.status_code == 200
    # registry unreachable → visible fallback notice, never a silent pretend
    assert "cached fallback" in r.text
    # every signal is an honest unknown with its reason — nothing fabricated
    assert "unknown" in r.text and "offline test" in r.text
    assert ">0 moving<" in r.text
    # no amber threshold badge can render when no age is known
    assert f"&gt;{config.FLEET_STALE_HOURS}h" not in r.text
    assert f"&gt;{freshness.COMMIT_STALE_DAYS}d" not in r.text


# --------------------------------------------------------------------------- #
# (b) happy path: rows render with expected ages + stale classification
# --------------------------------------------------------------------------- #


def test_overview_rows_classify_and_sort(monkeypatch):
    _happy_get(monkeypatch)
    out = asyncio.run(freshness.overview(now=NOW))
    assert out["lane_source"]["source"] == "registry"
    assert [r["lane"] for r in out["rows"]] == ["beta", "alpha", "attic"]

    beta, alpha, attic = out["rows"]
    # beta: fresh commit, stale heartbeat → stale via heartbeat only
    assert beta["state"] == "stale" and beta["stale"] is True
    assert beta["heartbeat_stale"] is True and beta["commit_stale"] is False
    assert beta["heartbeat"]["ok"] is True
    assert beta["heartbeat"]["age_hours"] > config.FLEET_STALE_HOURS
    # beta keeps no session trail → the exact honest reason
    assert beta["card"] == {"ok": False,
                            "reason": "no .sessions/ on main (HTTP 404)"}

    # alpha: everything fresh
    assert alpha["state"] == "moving" and alpha["stale"] is False
    assert alpha["last_commit"]["sha"] == "aaaa111"  # short sha
    assert alpha["last_commit"]["age_human"] == "10h ago"
    assert alpha["open_prs"]["display"] == "2"
    assert alpha["card"]["ok"] is True and alpha["card"]["date"] == "2026-07-12"
    assert alpha["heartbeat"]["age_human"] == "6h ago"

    # attic: ancient commit + heartbeat but archived → exempt, never amber
    assert attic["state"] == "exempt" and attic["exempt"] is True
    assert attic["stale"] is False
    assert attic["commit_stale"] is False and attic["heartbeat_stale"] is False

    assert out["summary"] == {"total": 3, "moving": 1, "stale": 1,
                              "unknown": 0, "exempt": 1}


def test_route_renders_rows_and_amber_badges(monkeypatch):
    _happy_get(monkeypatch)
    _freeze(monkeypatch)
    with TestClient(app) as c:
        r = c.get("/freshness")
    assert r.status_code == 200
    # clarity lede states purpose + the unknown/amber semantics
    assert "which fleet repos are moving, and which are stale" in r.text
    assert "live from registry" in r.text
    # per-repo cells: short sha, card date, PR count, heartbeat age
    assert "aaaa111" in r.text and "2026-07-12" in r.text
    assert "6h ago" in r.text
    # beta's stale heartbeat → amber threshold badge + the summary pill
    assert f"&gt;{config.FLEET_STALE_HOURS}h" in r.text
    assert ">1 stale<" in r.text
    # honest unknown with reason for the missing session trail
    assert "no .sessions/ on main (HTTP 404)" in r.text
    # archived lane renders the dim exempt note, not an alarm
    assert "archived seat" in r.text


# --------------------------------------------------------------------------- #
# (c) /freshness.json — pinned row/summary/top-level contract
# --------------------------------------------------------------------------- #

TOP_KEYS = {"rows", "summary", "stale_hours", "commit_stale_days",
            "lane_source", "registry_url"}
ROW_KEYS = {"lane", "repo", "repo_url", "note", "exempt",
            "last_commit", "commit_stale", "open_prs", "card",
            "heartbeat", "heartbeat_stale", "stale", "state"}
SUMMARY_KEYS = {"total", "moving", "stale", "unknown", "exempt"}


def test_freshness_json_contract(monkeypatch):
    _happy_get(monkeypatch)
    _freeze(monkeypatch)
    with TestClient(app) as c:
        r = c.get("/freshness.json")
    assert r.status_code == 200
    d = r.json()
    assert set(d.keys()) == TOP_KEYS, sorted(set(d) ^ TOP_KEYS)
    assert set(d["summary"].keys()) == SUMMARY_KEYS
    assert d["rows"], "no rows rendered — the contract test needs some"
    for row in d["rows"]:
        assert set(row.keys()) == ROW_KEYS, (
            f"row contract drift ({row['lane']}): "
            f"{sorted(set(row) ^ ROW_KEYS)}"
        )
        assert row["state"] in ("moving", "stale", "unknown", "exempt")


# --------------------------------------------------------------------------- #
# (d) boundary: exactly AT a threshold is not stale; strictly past it is
# --------------------------------------------------------------------------- #

_LANE = {"lane": "x", "repo": "x", "status_path": "control/status.md",
         "model": "unknown", "note": ""}


def _mock_repo(monkeypatch, updated=None, commit_date=None):
    """One repo with the given heartbeat stamp + commit date (both optional)."""

    async def fake_fetch(repo, path, ref="main", refresh=False):
        if path == "control/status.md" and updated is not None:
            return _res(data=f"# x · status\nupdated: {updated}\n")
        return _res(ok=False, status=404, error="Not Found")

    async def fake_api(repo, subpath="", refresh=False):
        if subpath.startswith("/commits") and commit_date is not None:
            return _res(data=[_commit("abcd1234ffff", commit_date)])
        if subpath.startswith("/pulls"):
            return _res(data=[])
        return _res(ok=False, status=404, error="nf")

    monkeypatch.setattr(github, "fetch_file", fake_fetch)
    monkeypatch.setattr(github, "repo_api", fake_api)


def test_heartbeat_exactly_at_threshold_is_not_stale(monkeypatch):
    at = _iso_minutes(NOW - timedelta(hours=config.FLEET_STALE_HOURS))
    _mock_repo(monkeypatch, updated=at,
               commit_date=_iso_seconds(NOW - timedelta(hours=1)))
    row = asyncio.run(freshness.repo_row(_LANE, NOW))
    assert row["heartbeat"]["age_hours"] == config.FLEET_STALE_HOURS
    assert row["heartbeat_stale"] is False and row["state"] == "moving"


def test_heartbeat_past_threshold_is_stale(monkeypatch):
    past = _iso_minutes(NOW - timedelta(hours=config.FLEET_STALE_HOURS, minutes=1))
    _mock_repo(monkeypatch, updated=past,
               commit_date=_iso_seconds(NOW - timedelta(hours=1)))
    row = asyncio.run(freshness.repo_row(_LANE, NOW))
    assert row["heartbeat_stale"] is True and row["state"] == "stale"


def test_commit_exactly_at_threshold_is_not_stale(monkeypatch):
    at = _iso_seconds(NOW - timedelta(days=freshness.COMMIT_STALE_DAYS))
    _mock_repo(monkeypatch, updated=_iso_minutes(NOW - timedelta(hours=1)),
               commit_date=at)
    row = asyncio.run(freshness.repo_row(_LANE, NOW))
    assert row["last_commit"]["age_hours"] == freshness.COMMIT_STALE_DAYS * 24
    assert row["commit_stale"] is False and row["state"] == "moving"


def test_commit_past_threshold_is_stale(monkeypatch):
    past = _iso_seconds(
        NOW - timedelta(days=freshness.COMMIT_STALE_DAYS, minutes=1)
    )
    _mock_repo(monkeypatch, updated=_iso_minutes(NOW - timedelta(hours=1)),
               commit_date=past)
    row = asyncio.run(freshness.repo_row(_LANE, NOW))
    assert row["commit_stale"] is True and row["state"] == "stale"


# --------------------------------------------------------------------------- #
# (e) archived/hub lanes are exempt even when everything is ancient
# --------------------------------------------------------------------------- #


def test_archived_lane_is_exempt_not_stale(monkeypatch):
    _mock_repo(monkeypatch, updated="2026-01-01T00:00Z",
               commit_date="2026-01-01T00:00:00Z")
    lane = dict(_LANE, note="archived seat (stale-by-design).")
    row = asyncio.run(freshness.repo_row(lane, NOW))
    assert row["exempt"] is True and row["state"] == "exempt"
    assert row["stale"] is False
    assert row["commit_stale"] is False and row["heartbeat_stale"] is False
    # the honest ages survive — only the alarm is dropped
    assert row["last_commit"]["ok"] is True and row["heartbeat"]["ok"] is True


def test_hub_lane_is_exempt(monkeypatch):
    _mock_repo(monkeypatch)  # no status file, no commits — all unknown
    lane = dict(
        _LANE,
        note="hub seat — no control/status.md by design (honest absence).",
    )
    row = asyncio.run(freshness.repo_row(lane, NOW))
    assert row["state"] == "exempt" and row["stale"] is False
    assert row["heartbeat"] == {
        "ok": False, "reason": "no control/status.md on main (HTTP 404)",
    }


# --------------------------------------------------------------------------- #
# unknown state: no readable signal at all → unknown, never invented
# --------------------------------------------------------------------------- #


def test_no_signals_at_all_is_unknown(monkeypatch):
    _mock_repo(monkeypatch)  # every fetch 404s
    row = asyncio.run(freshness.repo_row(_LANE, NOW))
    assert row["state"] == "unknown" and row["stale"] is False
    assert row["last_commit"]["ok"] is False
    assert row["card"]["reason"] == "no .sessions/ on main (HTTP 404)"
