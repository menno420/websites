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


# ---------------------------------------------------------------------------
# The 8 standing seats (ORDER 017: consolidation reflected, from baked data)
# ---------------------------------------------------------------------------
def _fixture_seats() -> dict:
    return {
        "generated_at": "2026-07-12T14:00:00Z",
        "registry": {"ok": True, "reason": "", "url": "u",
                     "total_seats": 0, "repo_seats": 0, "registry_only_seats": []},
        "lanes": [],
        "seats": [
            {"seat": "Websites", "role": "Control plane; merge = deploy",
             "repos": [
                 {"repo": "websites", "repo_url": "https://github.com/menno420/websites",
                  "heartbeat_available": True, "updated": "2026-07-12T11:00:00Z", "reason": ""},
             ]},
            {"seat": "Game Lab", "role": "Standalone games",
             "repos": [
                 {"repo": "gba-homebrew", "repo_url": "https://github.com/menno420/gba-homebrew",
                  "heartbeat_available": True, "updated": "2026-07-12T09:00:00Z", "reason": ""},
                 {"repo": "pokemon-mod-lab", "repo_url": "",
                  "heartbeat_available": False, "updated": "",
                  "reason": "HTTP 404 — no control/status.md on main (or repo not public)"},
             ]},
        ],
        "seats_sources": [{"label": "decision doc", "url": "https://github.com/menno420/superbot/blob/x/d.md"}],
        "consolidation": {
            "summary": "peaked at ~15 Projects; consolidation decided 2026-07-11, canonicalized 2026-07-12T03:15Z",
            "peak": "~15", "decided": "2026-07-11", "canonicalized": "2026-07-12T03:15:10Z",
            "evidence": [{"label": "e", "url": "https://github.com/menno420/superbot/blob/x/e.md"}],
        },
    }


def test_seats_view_freshest_member_wins_and_gaps_stay_honest():
    sv = fleetdata.seats_view(_fixture_seats(), now=NOW)
    assert sv["ok"] is True
    game_lab = next(s for s in sv["seats"] if s["seat"] == "Game Lab")
    # seat-level reading = the freshest member (09:00 → 3h at the frozen NOW)
    assert game_lab["last_heartbeat"]["age_human"] == "3h ago"
    # the private member is an honest gap, never invented
    poke = next(m for m in game_lab["repos"] if m["repo"] == "pokemon-mod-lab")
    assert poke["heartbeat_available"] is False
    assert poke["freshness"]["ok"] is False
    assert "404" in poke["reason"]


def test_seats_view_absent_section_is_honest():
    """A pre-consolidation mirror (no seats key) yields ok=False — the page
    skips the section rather than inventing a structure."""
    sv = fleetdata.seats_view({"lanes": []}, now=NOW)
    assert sv["ok"] is False and sv["seats"] == []


def test_committed_mirror_carries_the_eight_standing_seats():
    """The committed fleet.json reflects the 07-11/07-12 consolidation:
    exactly 8 standing seats, each member repo carrying an honest heartbeat
    record (values regenerate daily and are never pinned here)."""
    res = fleetdata.load_fleet()
    assert res["ok"], res["error"]
    seats = res["data"].get("seats") or []
    assert len(seats) == 8
    names = {s["seat"] for s in seats}
    assert names == {
        "Fleet Manager", "Venture Lab", "SuperBot World", "SuperBot 2.0",
        "Ideas Lab", "Game Lab", "Self Improvement", "Websites",
    }
    for s in seats:
        for m in s["repos"]:
            assert m["heartbeat_available"] in (True, False)
            if not m["heartbeat_available"]:
                assert m["reason"].strip()
    cons = res["data"].get("consolidation") or {}
    # the precise, evidence-honest phrasing (never an exact "15")
    assert cons.get("peak") == "~15"
    assert cons.get("decided") == "2026-07-11"
    assert cons.get("canonicalized", "").startswith("2026-07-12T03:15")


def test_fleet_page_renders_eight_seats_and_consolidation():
    r = client.get("/fleet")
    assert r.status_code == 200
    assert "The 8 standing seats" in r.text
    for name in ("Fleet Manager", "Venture Lab", "SuperBot World", "SuperBot 2.0",
                 "Ideas Lab", "Game Lab", "Self Improvement", "Websites"):
        assert name in r.text
    # consolidation phrased precisely, commit-linked
    assert "peaked at ~15 Projects" in r.text
    assert "canonicalized 2026-07-12T03:15Z" in r.text
    assert "639b0f09d7e99056cb8be83abc733edc198f1728" in r.text
    # the private Game Lab member is an honest labeled gap
    assert "not measurable" in r.text


# ---------------------------------------------------------------------------
# Latest-commit head records (git-transport probe, ORDER 017 comprehensive
# refresh: every repo's latest committed state in the mirror)
# ---------------------------------------------------------------------------
def test_committed_mirror_heads_cover_every_repo_backed_lane():
    """Every repo-backed lane carries a head record: ok=True with a real
    40-hex sha, or ok=False with the honest reason. Values regenerate at
    every bake and are never pinned here."""
    res = fleetdata.load_fleet()
    assert res["ok"], res["error"]
    for ln in res["data"]["lanes"]:
        if not ln.get("repo"):
            continue
        head = ln.get("head")
        assert head is not None, f"lane {ln['lane']} missing its head probe"
        if head["ok"]:
            assert len(head["sha"]) == 40 and int(head["sha"], 16) >= 0
        else:
            assert head["reason"].strip()


def test_lane_view_passes_head_through_and_page_renders_it():
    fleet = _fixture_fleet()
    fleet["lanes"][0]["head"] = {
        "ok": True, "sha": "a" * 40, "committed_at": "2026-07-12T10:00:00+00:00",
        "source": "anonymous git transport (ls-remote + depth-1 fetch)",
    }
    lane = fleetdata.lane_view(fleet["lanes"][0], {}, now=NOW)
    assert lane["head"]["sha"] == "a" * 40
    # a pre-probe mirror (no head key) stays an empty dict, not a KeyError
    assert fleetdata.lane_view(fleet["lanes"][1], {}, now=NOW)["head"] == {}
    # and the real page renders the probe line from the committed mirror
    r = client.get("/fleet")
    assert "latest commit" in r.text
    assert "git transport, at bake time" in r.text
