"""gen_fleet.py — the fleet-mirror bake. Every test here drives a PURE
transform (``parse_registry`` / ``parse_heartbeat`` / ``bake_seats`` / the
registry-only ``bake_lane`` branch) or the fail-soft ``main`` paths with the
one network seam (``_fetch``) stubbed — no live registry fetch, no git
transport, no raw heartbeat pull. Expectations come from the generator's own
code (KNOWN_KEYS, FIELD_CAP, PRIVATE_LANES, the SEATS structure)."""

from __future__ import annotations

import json

from review import gen_fleet


# ---------------------------------------------------------------------------
# parse_registry — the LANES literal out of gen_roster.py source
# ---------------------------------------------------------------------------

def test_parse_registry_extracts_lane_dicts_and_drops_non_dicts():
    text = (
        "# some preamble\n"
        "LANES = [\n"
        '    {"lane": "websites", "repo": "websites", "disposition": "live"},\n'
        '    {"lane": "coord", "repo": None, "disposition": "registry-only"},\n'
        '    "not-a-dict-entry",\n'  # kept out by the isinstance filter
        "]\n"
        "OTHER = 1\n"
    )
    entries = gen_fleet.parse_registry(text)
    assert [e["lane"] for e in entries] == ["websites", "coord"]
    assert entries[1]["repo"] is None


def test_parse_registry_absent_or_malformed_yields_empty_list():
    assert gen_fleet.parse_registry("no lanes literal here") == []
    assert gen_fleet.parse_registry("") == []
    # a LANES block whose body is not valid Python literal → [] (never raises)
    assert gen_fleet.parse_registry("LANES = [ this is not python\n]") == []


# ---------------------------------------------------------------------------
# parse_heartbeat — status.md → known-key fields (continuation, cap, scrub)
# ---------------------------------------------------------------------------

def test_parse_heartbeat_known_keys_continuation_and_colon_in_value():
    text = "\n".join([
        "# websites · status",       # comment line ignored
        "updated: 2026-07-14T10:00:00Z",
        "health: green (main)",
        "notes: first line",
        "   a wrapped continuation",  # no leading known key → appends to notes
        "orders: acked=011: done=009",  # colon inside the value survives
    ])
    fields = gen_fleet.parse_heartbeat(text)
    assert fields == {
        "updated": "2026-07-14T10:00:00Z",
        "health": "green (main)",
        "notes": "first line a wrapped continuation",
        "orders": "acked=011: done=009",
    }


def test_parse_heartbeat_unknown_leading_field_before_any_key_is_dropped():
    # a colon-bearing line whose key is unknown, with no current field open,
    # continues nothing and is discarded — it never invents a field.
    fields = gen_fleet.parse_heartbeat("mystery: value\nupdated: 2026-07-14")
    assert "mystery" not in fields
    assert fields == {"updated": "2026-07-14"}


def test_parse_heartbeat_caps_long_values_with_a_visible_mark():
    body = "x" * (gen_fleet.FIELD_CAP + 200)
    fields = gen_fleet.parse_heartbeat(f"notes: {body}")
    val = fields["notes"]
    assert val.endswith(gen_fleet._TRUNC_MARK)
    assert "truncated for the mirror" in val
    # capped to FIELD_CAP characters of content plus the mark
    assert len(val) <= gen_fleet.FIELD_CAP + len(gen_fleet._TRUNC_MARK)


def test_parse_heartbeat_scrubs_the_private_lane_from_free_text():
    fields = gen_fleet.parse_heartbeat("notes: paired with pokemon-mod-lab work")
    assert "pokemon" not in fields["notes"].lower()
    assert gen_fleet._PRIVATE_TEXT_SUB in fields["notes"]


# ---------------------------------------------------------------------------
# bake_lane — the registry-only (no repo) branch is network-free
# ---------------------------------------------------------------------------

def test_bake_lane_registry_only_needs_no_network():
    lane = gen_fleet.bake_lane({"lane": "coordinator", "repo": None,
                                "disposition": "registry-only"})
    assert lane["repo"] is None
    assert lane["heartbeat"] == {
        "available": False,
        "reason": "registry-only seat — no repo, nothing to mirror",
    }
    assert "head" not in lane  # no repo → no git-transport probe attempted


# ---------------------------------------------------------------------------
# bake_seats — the pure seat↔lane join (private exclusion, honest gaps)
# ---------------------------------------------------------------------------

def _lane(repo, updated, available=True):
    return {
        "lane": repo, "repo": repo, "disposition": "live",
        "repo_url": f"https://github.com/menno420/{repo}",
        "heartbeat": {"available": available,
                      "fields": {"updated": updated} if available else {},
                      "reason": "" if available else "HTTP 404"},
    }


def test_bake_seats_joins_present_lane_and_flags_missing_repo():
    seats = gen_fleet.bake_seats([_lane("websites", "2026-07-14T11:00:00Z")])
    assert len(seats) == len(gen_fleet.SEATS) == 8
    assert {s["seat"] for s in seats} == {s["seat"] for s in gen_fleet.SEATS}

    websites = next(s for s in seats if s["seat"] == "Websites")
    member = next(m for m in websites["repos"] if m["repo"] == "websites")
    assert member["heartbeat_available"] is True
    assert member["updated"] == "2026-07-14T11:00:00Z"

    # a seat whose repo is absent from the lane mirror records the honest gap
    fleet_mgr = next(s for s in seats if s["seat"] == "Fleet Manager")
    fm_member = next(m for m in fleet_mgr["repos"] if m["repo"] == "fleet-manager")
    assert fm_member["heartbeat_available"] is False
    assert fm_member["reason"] == "repo not in the lane registry mirror"


def test_bake_seats_excludes_the_private_lane_from_its_seat():
    # Game Lab = gba-homebrew + pokemon-mod-lab (private); only the public
    # repo may appear as a member, private one is dropped entirely.
    seats = gen_fleet.bake_seats([_lane("gba-homebrew", "2026-07-14T09:00:00Z")])
    game_lab = next(s for s in seats if s["seat"] == "Game Lab")
    assert [m["repo"] for m in game_lab["repos"]] == ["gba-homebrew"]


# ---------------------------------------------------------------------------
# main — fail-soft when the registry cannot be fetched
# ---------------------------------------------------------------------------

def test_main_keeps_the_previously_committed_mirror_when_registry_fetch_fails(
    monkeypatch, tmp_path
):
    out = tmp_path / "fleet.json"
    before = '{"generated_at": "2026-07-10T00:00:00Z", "lanes": []}\n'
    out.write_text(before, encoding="utf-8")
    monkeypatch.setattr(gen_fleet, "OUT_PATH", out)
    monkeypatch.setattr(gen_fleet, "_fetch", lambda url: (None, "HTTP 500"))
    assert gen_fleet.main() == 0
    # existing committed file left byte-identical (fail-soft; staleness banner tells)
    assert out.read_text(encoding="utf-8") == before


def test_main_first_bake_with_no_registry_writes_an_honest_empty_mirror(
    monkeypatch, tmp_path
):
    out = tmp_path / "fleet.json"  # does NOT exist yet
    monkeypatch.setattr(gen_fleet, "OUT_PATH", out)
    monkeypatch.setattr(gen_fleet, "_fetch", lambda url: (None, "Timeout: boom"))
    assert gen_fleet.main() == 0
    doc = json.loads(out.read_text(encoding="utf-8"))
    assert doc["registry"]["ok"] is False
    assert doc["registry"]["total_seats"] == 0
    assert doc["lanes"] == []
    assert "boom" in doc["registry"]["reason"]  # the honest reason, not invented
