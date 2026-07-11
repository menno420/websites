"""Fleet pages + fleetdata domain tests. Network-free; time-frozen: every
age-measuring assertion injects ``now=`` or uses extreme stamps (epoch /
far-future) so nothing here ever time-bombs (the 08:45Z lesson)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from review import fleetdata
from review.app import app

client = TestClient(app)

NOW = datetime(2026, 7, 12, 12, 0, 0, tzinfo=timezone.utc)  # frozen


def _fixture_fleet() -> dict:
    return {
        "generated_at": "2026-07-12T06:00:00Z",
        "registry": {
            "ok": True,
            "reason": "",
            "url": "https://github.com/menno420/fleet-manager/blob/main/scripts/gen_roster.py",
            "total_seats": 3,
            "repo_seats": 2,
            "registry_only_seats": ["coordinator (no repo)"],
        },
        "lanes": [
            {
                "lane": "websites",
                "repo": "websites",
                "disposition": "live",
                "repo_url": "https://github.com/menno420/websites",
                "heartbeat": {
                    "available": True,
                    "fields": {
                        "updated": "2026-07-12T11:00:00Z",
                        "health": "green (main HEAD abc)",
                        "orders": "acked=001-011 done=001-009",
                        "kit": "v1.11.0 · check: green",
                        "last-shipped": "#139 — advisory",
                    },
                    "source_url": "https://github.com/menno420/websites/blob/main/control/status.md",
                },
            },
            {
                "lane": "darkrepo",
                "repo": "darkrepo",
                "disposition": "archived",
                "repo_url": "https://github.com/menno420/darkrepo",
                "heartbeat": {"available": False, "reason": "HTTP 404 — no control/status.md on main (or repo not public)"},
            },
            {
                "lane": "coordinator (no repo)",
                "repo": None,
                "disposition": "registry-only",
                "heartbeat": {"available": False, "reason": "registry-only seat — no repo, nothing to mirror"},
            },
        ],
    }


# ---------------------------------------------------------------------------
# Domain: loaders degrade honestly
# ---------------------------------------------------------------------------
def test_load_fleet_missing(tmp_path: Path):
    res = fleetdata.load_fleet(tmp_path / "nope.json")
    assert res["ok"] is False and "missing" in res["error"]


def test_load_fleet_malformed(tmp_path: Path):
    p = tmp_path / "bad.json"
    p.write_text(json.dumps({"hello": 1}), encoding="utf-8")
    res = fleetdata.load_fleet(p)
    assert res["ok"] is False and "malformed" in res["error"]


def test_load_stats_missing_is_calm(tmp_path: Path):
    res = fleetdata.load_stats(tmp_path / "nope.json")
    assert res["ok"] is False
    assert "no stats mirrored yet" in res["error"]  # normal state, not alarm


def test_committed_fleet_mirror_loads_and_counts_are_consistent():
    """The real committed fleet.json: shape-wise assertions only (the bake
    regenerates values daily — tests must never pin them)."""
    res = fleetdata.load_fleet()
    assert res["ok"], res["error"]
    reg = res["data"]["registry"]
    lanes = res["data"]["lanes"]
    assert reg["total_seats"] == len(lanes)
    repo_backed = [ln for ln in lanes if ln.get("repo")]
    assert reg["repo_seats"] == len(repo_backed)
    assert reg["total_seats"] - reg["repo_seats"] == len(reg["registry_only_seats"])
    # every repo-backed lane records heartbeat availability honestly
    for ln in repo_backed:
        hb = ln["heartbeat"]
        assert hb["available"] in (True, False)
        if not hb["available"]:
            assert hb["reason"].strip()


# ---------------------------------------------------------------------------
# Domain: parsers (pure, frozen)
# ---------------------------------------------------------------------------
def test_freshness_frozen_now():
    fr = fleetdata.freshness("2026-07-12T11:00:00Z", now=NOW, stale_hours=12)
    assert fr["ok"] and fr["stale"] is False and fr["age_human"] == "1h ago"
    fr2 = fleetdata.freshness("2026-07-10T11:00:00Z", now=NOW, stale_hours=12)
    assert fr2["stale"] is True


def test_freshness_unparseable_is_honest():
    fr = fleetdata.freshness("not a date", now=NOW)
    assert fr["ok"] is False and fr["age_human"] == "age unknown" and fr["stale"] is False


def test_orders_summary():
    o = fleetdata.orders_summary("acked=001-011 done=001-009")
    assert o["ok"] and o["acked"] == 11 and o["done"] == 9
    assert o["outstanding"] == ["010", "011"]
    assert fleetdata.orders_summary("free text")["ok"] is False


def test_kit_version_and_health():
    assert fleetdata.kit_version("v1.11.0 · check: green") == "v1.11.0"
    assert fleetdata.kit_version("prose only") == ""
    assert fleetdata.health_kind("green (main)") == "green"
    assert fleetdata.health_kind("red-by-design: skeleton") == "red-by-design"
    assert fleetdata.health_kind("red: broken") == "broken"
    assert fleetdata.health_kind("") == "unknown"


def test_fleet_overview_counts_from_fixture():
    ov = fleetdata.fleet_overview(_fixture_fleet(), {}, now=NOW)
    assert ov["counts"]["total_seats"] == 3
    assert ov["counts"]["repo_seats"] == 2
    assert ov["counts"]["registry_only"] == 1
    assert ov["counts"]["heartbeats_mirrored"] == 1
    assert ov["counts"]["live"] == 1 and ov["counts"]["archived"] == 1
    # live sorts before archived and registry-only
    assert ov["lanes"][0]["lane"] == "websites"


def test_lane_detail_found_and_missing():
    fleet = _fixture_fleet()
    lane = fleetdata.lane_detail(fleet, {"repos": {"websites": {"ok": True, "pushed_at": "2026-07-12T10:00:00Z"}}}, "websites", now=NOW)
    assert lane is not None
    assert lane["orders"]["outstanding"] == ["010", "011"]
    assert lane["kit"] == "v1.11.0"
    assert lane["stats"]["ok"] is True
    assert fleetdata.lane_detail(fleet, {}, "no-such-repo", now=NOW) is None


# ---------------------------------------------------------------------------
# Routes against the real committed mirror
# ---------------------------------------------------------------------------
def test_fleet_page_renders_registry_counts_dynamically():
    res = fleetdata.load_fleet()
    assert res["ok"]
    reg = res["data"]["registry"]
    r = client.get("/fleet")
    assert r.status_code == 200
    # the page shows the registry's own counts — never a hardcoded fleet size
    assert f"{reg['repo_seats']} repo-backed" in r.text
    assert "seats in the registry" in r.text
    assert "as of" in r.text  # honest as-of stamp present
    # gaps are labeled, not faked
    if any(
        ln.get("repo") and not ln["heartbeat"]["available"] for ln in res["data"]["lanes"]
    ):
        assert "No heartbeat mirrored" in r.text


def test_fleet_detail_renders_own_lane():
    r = client.get("/fleet/websites")
    assert r.status_code == 200
    assert "menno420/websites" in r.text
    assert "control/status.md" in r.text
    assert "Ask via a prefilled GitHub issue" in r.text


def test_fleet_detail_unknown_repo_404():
    assert client.get("/fleet/definitely-not-a-repo").status_code == 404


def test_fleet_json_machine_view():
    body = client.get("/fleet.json").json()
    assert body["fleet"]["ok"] is True
    assert isinstance(body["fleet"]["data"]["lanes"], list)
    # stats may legitimately be absent until the first CI bake — but the
    # payload must say so honestly either way
    assert body["stats"]["ok"] in (True, False)
    if not body["stats"]["ok"]:
        assert body["stats"]["error"]


def test_fleet_page_degrades_when_mirror_missing(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(fleetdata, "FLEET_PATH", tmp_path / "gone.json")
    r = client.get("/fleet")
    assert r.status_code == 200
    assert "Fleet mirror unavailable" in r.text
    # and the detail page 404s honestly instead of erroring
    assert client.get("/fleet/websites").status_code == 404


def test_fleet_page_staleness_banner_epoch_stamp(monkeypatch, tmp_path: Path):
    """A mirror baked at the epoch always renders the stale banner —
    deterministic forever (no wall-clock coupling)."""
    fleet = _fixture_fleet()
    fleet["generated_at"] = "1970-01-01T00:00:00Z"
    p = tmp_path / "fleet.json"
    p.write_text(json.dumps(fleet), encoding="utf-8")
    monkeypatch.setattr(fleetdata, "FLEET_PATH", p)
    r = client.get("/fleet")
    assert r.status_code == 200
    assert "This mirror is stale" in r.text


def test_fleet_page_no_stale_banner_far_future_stamp(monkeypatch, tmp_path: Path):
    """A far-future bake stamp never trips the banner — the counterpart
    direction, also deterministic forever."""
    fleet = _fixture_fleet()
    fleet["generated_at"] = "9999-01-01T00:00:00Z"
    p = tmp_path / "fleet.json"
    p.write_text(json.dumps(fleet), encoding="utf-8")
    monkeypatch.setattr(fleetdata, "FLEET_PATH", p)
    r = client.get("/fleet")
    assert r.status_code == 200
    assert "This mirror is stale" not in r.text
