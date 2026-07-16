"""Fleet Arcade tests — network-free (site feed primed from a fixture, arcade
registry read from the committed JSON on disk or from tmp files)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from botsite import app as app_module
from botsite import arcade
from botsite import data_source as ds

# Minimal site.json fixture so _base_ctx/lifespan never touch the network.
FIXTURE = {
    "meta": {"build": {"commit": "abcdef1234", "subject": "test build", "committed_at": "2026-07-09T00:00:00Z"}},
    "counts": {"commands": 0, "features": 0, "games": 0},
    "catalogue": [],
    "commands": [],
    "bot_changelog": [],
}

# games-web's documented (404) Pages URL — must never be rendered as a link.
DEAD_PAGES_URL = "https://menno420.github.io/product-forge/"

# mineverse's live Railway deployment (ORDER 022; cold-verified 200).
MINEVERSE_URL = "https://web-production-97636.up.railway.app"


@pytest.fixture()
def client():
    ds.clear_cache()
    ds.prime_cache(FIXTURE)
    ds.set_client(ds.make_client())  # never actually hit (cache is warm)
    with TestClient(app_module.app) as c:
        yield c
    ds.clear_cache()


def test_arcade_lists_all_games_with_maturity_badges(client):
    r = client.get("/arcade")
    assert r.status_code == 200
    for name in ("Lumen Drift", "mineverse", "games-web"):
        assert name in r.text
    # maturity badges render (one playable, two beta in the committed registry)
    assert ">playable<" in r.text
    assert ">beta<" in r.text
    assert "sb-badge-ok" in r.text and "sb-badge-info" in r.text


def test_arcade_no_dead_links(client):
    """Only really-reachable games get anchors: the 404 games-web Pages URL must
    not appear as an href (or at all), and the two unavailable games render
    honest status notes instead of links."""
    r = client.get("/arcade")
    assert r.status_code == 200
    assert f'href="{DEAD_PAGES_URL}' not in r.text
    assert DEAD_PAGES_URL not in r.text
    # honest status notes show for the two still-unavailable games
    assert "pending" in r.text.lower()


def test_arcade_mineverse_live_link(client):
    """mineverse is live (ORDER 022): the card renders a playable link to the
    Railway deployment with the attribution ref appended."""
    r = client.get("/arcade")
    assert r.status_code == 200
    assert f'href="{MINEVERSE_URL}?ref=fleet-arcade"' in r.text
    assert "Play now" in r.text


def test_arcade_source_repo_links(client):
    r = client.get("/arcade")
    for repo in ("menno420/gba-homebrew", "menno420/superbot-mineverse", "menno420/product-forge"):
        assert f'href="https://github.com/{repo}"' in r.text


def test_arcade_lede_defines_the_fleet(client):
    """Clarity: a first-time visitor learns what 'the fleet' is from the lede."""
    r = client.get("/arcade")
    assert r.status_code == 200
    assert "family of bots, sites, and" in r.text
    assert "built around SuperBot" in r.text


def test_nav_includes_arcade(client):
    r = client.get("/")
    assert 'href="/arcade"' in r.text
    assert "Arcade" in r.text


def test_arcade_degrades_on_missing_file(client, monkeypatch, tmp_path):
    monkeypatch.setattr(arcade, "ARCADE_JSON_PATH", tmp_path / "does-not-exist.json")
    r = client.get("/arcade")
    assert r.status_code == 200
    assert "No games registered yet" in r.text


def test_arcade_degrades_on_corrupt_file(client, monkeypatch, tmp_path):
    corrupt = tmp_path / "arcade.json"
    corrupt.write_text("{ this is not json", encoding="utf-8")
    monkeypatch.setattr(arcade, "ARCADE_JSON_PATH", corrupt)
    r = client.get("/arcade")
    assert r.status_code == 200
    assert "No games registered yet" in r.text


def test_loader_skips_invalid_entries(tmp_path):
    """Entries missing required fields (or with bad enum values) are skipped, not fatal."""
    reg = tmp_path / "arcade.json"
    reg.write_text(json.dumps([
        {"slug": "ok", "name": "OK Game", "tagline": "t", "description": "d",
         "maturity": "beta", "availability": "unavailable", "url": None,
         "source_repo": "menno420/x", "status_note": "n"},
        {"slug": "no-name", "tagline": "t", "description": "d",
         "maturity": "beta", "availability": "unavailable", "url": None,
         "source_repo": "menno420/x"},
        {"slug": "bad-maturity", "name": "Bad", "tagline": "t", "description": "d",
         "maturity": "vaporware", "availability": "unavailable", "url": None,
         "source_repo": "menno420/x"},
        "not even a dict",
    ]), encoding="utf-8")
    games = arcade.load_games(reg)
    assert [g["slug"] for g in games] == ["ok"]


def test_loader_never_presents_live_without_url(tmp_path):
    reg = tmp_path / "arcade.json"
    reg.write_text(json.dumps([
        {"slug": "claims-live", "name": "Claims Live", "tagline": "t", "description": "d",
         "maturity": "playable", "availability": "live", "url": None,
         "source_repo": "menno420/x", "status_note": "n"},
    ]), encoding="utf-8")
    (game,) = arcade.load_games(reg)
    assert game["is_live"] is False
    assert game["has_link"] is False
    assert game["link_url"] is None


def test_loader_adds_attribution_ref(tmp_path):
    reg = tmp_path / "arcade.json"
    reg.write_text(json.dumps([
        {"slug": "really-live", "name": "Really Live", "tagline": "t", "description": "d",
         "maturity": "playable", "availability": "live", "url": "https://example.com/play",
         "source_repo": "menno420/x", "status_note": ""},
    ]), encoding="utf-8")
    (game,) = arcade.load_games(reg)
    assert game["is_live"] is True and game["has_link"] is True
    assert game["link_url"] == "https://example.com/play?ref=fleet-arcade"


def test_has_link_covers_exactly_the_linked_availabilities(tmp_path):
    """Behavior pin on ``LINKED_AVAILABILITIES`` (the single source of truth
    shared with the drift probe): a URL-bearing entry gets ``has_link`` and a
    ``link_url`` for EVERY linked availability and for NO other one."""
    reg = tmp_path / "arcade.json"
    reg.write_text(json.dumps([
        {"slug": f"g-{a}", "name": a.title(), "tagline": "t", "description": "d",
         "maturity": "beta", "availability": a, "url": "https://example.com/g",
         "source_repo": "menno420/x", "status_note": "n"}
        for a in arcade.AVAILABILITIES
    ]), encoding="utf-8")
    games = arcade.load_games(reg)
    assert len(games) == len(arcade.AVAILABILITIES)
    for game in games:
        linked = game["availability"] in arcade.LINKED_AVAILABILITIES
        assert game["has_link"] is linked
        assert (game["link_url"] is not None) is linked


def test_committed_registry_is_honest():
    """The committed registry loads, has all three games; mineverse is live
    (ORDER 022) and the other two stay honestly unavailable with notes."""
    games = arcade.load_games()
    assert [g["slug"] for g in games] == ["lumen-drift", "mineverse", "games-web"]
    by_slug = {g["slug"]: g for g in games}
    mv = by_slug["mineverse"]
    assert mv["availability"] == "live"
    assert mv["url"] == MINEVERSE_URL
    assert mv["is_live"] is True and mv["has_link"] is True
    assert mv["link_url"] == f"{MINEVERSE_URL}?ref=fleet-arcade"
    assert mv["status_note"]  # honest: read-only demo, sign-in launching
    for slug in ("lumen-drift", "games-web"):
        g = by_slug[slug]
        assert g["availability"] == "unavailable"
        assert g["url"] is None
        assert g["has_link"] is False
        assert g["status_note"]  # every unavailable game explains itself


# --------------------------------------------------------------------------- #
# /arcade/{slug} detail pages — per-game story + launch-blocker panels.
# --------------------------------------------------------------------------- #

def test_arcade_detail_200_per_known_slug(client):
    """Every game in the committed registry gets a working detail page."""
    for slug, name in (("lumen-drift", "Lumen Drift"), ("mineverse", "mineverse"), ("games-web", "games-web")):
        r = client.get(f"/arcade/{slug}")
        assert r.status_code == 200
        assert name in r.text
        assert "Fleet Arcade" in r.text  # crumb/category context


def test_arcade_detail_unknown_slug_404(client):
    r = client.get("/arcade/does-not-exist")
    assert r.status_code == 404
    assert "Page not found" in r.text
    assert "does-not-exist" in r.text


def test_arcade_detail_lumen_drift_blocker_panel(client):
    """The unavailable GBA game explains itself: the structured blocker panel
    renders the named owner click recorded in the registry, plus the honest
    'how it unblocks' line."""
    r = client.get("/arcade/lumen-drift")
    assert r.status_code == 200
    assert "What&#39;s blocking launch" in r.text or "What's blocking launch" in r.text
    assert "The owner click:" in r.text
    assert "lumen-drift-v1.3" in r.text
    assert "one owner click on the release page" in r.text
    assert "How it unblocks:" in r.text
    assert "Download button" in r.text
    # honest: no play/download affordance for an unreachable game
    assert "Play now" not in r.text
    assert "?ref=fleet-arcade" not in r.text and "&ref=fleet-arcade" not in r.text


def test_arcade_detail_games_web_blocker_panel(client):
    r = client.get("/arcade/games-web")
    assert r.status_code == 200
    assert "The owner click:" in r.text
    assert "Source to GitHub Actions" in r.text
    assert "one owner settings click" in r.text
    assert "How it unblocks:" in r.text
    # the documented-but-404 Pages URL must never appear on the detail page
    assert DEAD_PAGES_URL not in r.text


def test_arcade_detail_mineverse_play_affordance(client):
    """The available game's detail page carries the same honest play link the
    catalog offers (attribution ref included) — and no blocker panel."""
    r = client.get("/arcade/mineverse")
    assert r.status_code == 200
    assert f'href="{MINEVERSE_URL}?ref=fleet-arcade"' in r.text
    assert "Play now" in r.text
    assert "blocking launch" not in r.text
    # its honest status note still shows (read-only demo)
    assert "Read-only demo" in r.text


def test_arcade_cards_link_to_detail_pages(client):
    """Every catalog card links to its detail page."""
    r = client.get("/arcade")
    assert r.status_code == 200
    for slug in ("lumen-drift", "mineverse", "games-web"):
        assert f'href="/arcade/{slug}"' in r.text


def test_loader_normalizes_valid_blocker(tmp_path):
    reg = tmp_path / "arcade.json"
    reg.write_text(json.dumps([
        {"slug": "g", "name": "G", "tagline": "t", "description": "d",
         "maturity": "beta", "availability": "unavailable", "url": None,
         "source_repo": "menno420/x", "status_note": "n",
         "blocker": {"owner_action": "  click the thing  ", "unblocks": " then it ships "}},
    ]), encoding="utf-8")
    (game,) = arcade.load_games(reg)
    assert game["blocker"] == {
        "owner_action": "click the thing", "unblocks": "then it ships",
        "ask_id": None,  # id-less blocker: valid, just without a ledger ref
    }


@pytest.mark.parametrize("blocker", [
    None,                                        # explicit null
    "just prose",                                # wrong type
    {"owner_action": "click"},                   # missing unblocks
    {"unblocks": "ships"},                       # missing owner_action
    {"owner_action": "", "unblocks": "ships"},   # empty owner_action
    {"owner_action": 42, "unblocks": "ships"},   # wrong value type
])
def test_loader_malformed_blocker_degrades_to_none(tmp_path, blocker):
    """A missing/malformed blocker is fail-soft: it normalizes to None and
    never invalidates the game entry (honesty rule: degrade, don't invent)."""
    reg = tmp_path / "arcade.json"
    reg.write_text(json.dumps([
        {"slug": "g", "name": "G", "tagline": "t", "description": "d",
         "maturity": "beta", "availability": "unavailable", "url": None,
         "source_repo": "menno420/x", "status_note": "n", "blocker": blocker},
    ]), encoding="utf-8")
    (game,) = arcade.load_games(reg)
    assert game["blocker"] is None


def test_loader_missing_blocker_is_none(tmp_path):
    reg = tmp_path / "arcade.json"
    reg.write_text(json.dumps([
        {"slug": "g", "name": "G", "tagline": "t", "description": "d",
         "maturity": "beta", "availability": "unavailable", "url": None,
         "source_repo": "menno420/x", "status_note": "n"},
    ]), encoding="utf-8")
    (game,) = arcade.load_games(reg)
    assert game["blocker"] is None


def test_game_by_slug_returns_enriched_entry_or_none():
    game = arcade.game_by_slug("mineverse")
    assert game is not None
    assert game["is_live"] is True
    assert game["detail_url"] == "/arcade/mineverse"
    assert arcade.game_by_slug("no-such-game") is None


def test_committed_registry_blockers_are_recorded_for_unavailable_games():
    """Schema guard on the committed registry: both unavailable games carry a
    structured blocker (the named owner click + how it unblocks); the live
    game carries none. Detail URLs derive from slugs."""
    by_slug = {g["slug"]: g for g in arcade.load_games()}
    for slug in ("lumen-drift", "games-web"):
        blocker = by_slug[slug]["blocker"]
        assert blocker is not None
        assert blocker["owner_action"].strip()
        assert blocker["unblocks"].strip()
        assert "owner" in blocker["owner_action"].lower()  # a NAMED owner click
    assert by_slug["mineverse"]["blocker"] is None
    for slug, g in by_slug.items():
        assert g["detail_url"] == f"/arcade/{slug}"


# --------------------------------------------------------------------------- #
# blocker.ask_id — the stable ledger join key (owner-actions ledger ASK-NNNN).
# Primary join between the public blocker panel and the owner console's
# verification chips; fail-soft everywhere, never fatal.
# --------------------------------------------------------------------------- #

def test_loader_normalizes_valid_blocker_ask_id(tmp_path):
    reg = tmp_path / "arcade.json"
    reg.write_text(json.dumps([
        {"slug": "g", "name": "G", "tagline": "t", "description": "d",
         "maturity": "beta", "availability": "unavailable", "url": None,
         "source_repo": "menno420/x", "status_note": "n",
         "blocker": {"owner_action": "click", "unblocks": "ships",
                     "ask_id": "  ASK-0042  "}},
    ]), encoding="utf-8")
    (game,) = arcade.load_games(reg)
    assert game["blocker"]["ask_id"] == "ASK-0042"


@pytest.mark.parametrize("ask_id", [
    42,                # wrong type
    "",                # empty
    "   ",             # whitespace only
    "ASK-42",          # too few digits
    "ASK-00100",       # too many digits
    "ask-0010",        # wrong case (the ledger scheme is uppercase)
    "see ASK-0010",    # id embedded in prose, not an id
    "ASK-0010 maybe",  # trailing prose
])
def test_loader_malformed_ask_id_degrades_to_none_but_keeps_blocker(tmp_path, ask_id):
    """A bad ``ask_id`` costs only the ledger ref — the blocker itself (the
    honest owner click + unblocks story) always survives (fail-soft)."""
    reg = tmp_path / "arcade.json"
    reg.write_text(json.dumps([
        {"slug": "g", "name": "G", "tagline": "t", "description": "d",
         "maturity": "beta", "availability": "unavailable", "url": None,
         "source_repo": "menno420/x", "status_note": "n",
         "blocker": {"owner_action": "click", "unblocks": "ships",
                     "ask_id": ask_id}},
    ]), encoding="utf-8")
    (game,) = arcade.load_games(reg)
    assert game["blocker"] is not None
    assert game["blocker"]["owner_action"] == "click"
    assert game["blocker"]["ask_id"] is None


def test_committed_registry_blockers_carry_their_ledger_ask_ids():
    """The committed registry joins both launch blockers to their owner-actions
    ledger rows by stable id (docs/owner/OWNER-ACTIONS.md; the same ids
    app/askverify.py's arcade probes are registered under — pinned repo-wide
    by tests/test_askverify.py's consistency test)."""
    by_slug = {g["slug"]: g for g in arcade.load_games()}
    assert by_slug["lumen-drift"]["blocker"]["ask_id"] == "ASK-0010"
    assert by_slug["games-web"]["blocker"]["ask_id"] == "ASK-0011"


def test_arcade_detail_renders_the_ledger_ref(client):
    """Both blocked games' detail panels show the stable ledger ref — the
    visible half of the ask_id join."""
    for slug, ask_id in (("lumen-drift", "ASK-0010"), ("games-web", "ASK-0011")):
        r = client.get(f"/arcade/{slug}")
        assert r.status_code == 200
        assert "Ledger ref:" in r.text
        assert f"<code>{ask_id}</code>" in r.text


def test_arcade_detail_idless_blocker_renders_panel_without_ledger_ref(
    client, monkeypatch, tmp_path
):
    """An id-less blocker still renders its full panel — just no ledger ref
    line (the fallback path: the owner console then joins by signature)."""
    reg = tmp_path / "arcade.json"
    reg.write_text(json.dumps([
        {"slug": "g", "name": "G", "tagline": "t", "description": "d",
         "maturity": "beta", "availability": "unavailable", "url": None,
         "source_repo": "menno420/x", "status_note": "n",
         "blocker": {"owner_action": "click the thing", "unblocks": "then it ships"}},
    ]), encoding="utf-8")
    monkeypatch.setattr(arcade, "ARCADE_JSON_PATH", reg)
    r = client.get("/arcade/g")
    assert r.status_code == 200
    assert "The owner click:" in r.text
    assert "click the thing" in r.text
    assert "Ledger ref:" not in r.text


# --------------------------------------------------------------------------- #
# Catalog card blocker surfacing + availability summary strip.
# The /arcade catalog cards now carry each unavailable game's blocking
# owner_action / ask_id (the same honest ledger text the detail panel shows,
# never a live verdict), and a top-of-page availability summary counts live vs
# blocked games and the distinct owner clicks among the blocked ones.
# --------------------------------------------------------------------------- #

def test_arcade_catalog_card_surfaces_blocker_owner_action_and_ask_id(client):
    """Each unavailable card on the catalog carries its blocking owner click and
    stable ledger ref — the same ledger text the /arcade/{slug} panel renders,
    now on the card itself so a visitor never has to click through to see it."""
    r = client.get("/arcade")
    assert r.status_code == 200
    assert "The owner click:" in r.text
    # lumen-drift's blocker (owner_action + ask_id) is now on the catalog card
    assert "Publish the GitHub Release lumen-drift-v1.3" in r.text
    assert "<code>ASK-0010</code>" in r.text
    # games-web's blocker too
    assert "Source to GitHub Actions" in r.text
    assert "<code>ASK-0011</code>" in r.text
    assert "Ledger ref:" in r.text


def test_arcade_catalog_no_live_verdict_leaks_to_public_page(client):
    """Hard rail: the public catalog surfaces static registry ledger text only —
    never a live askverify verdict / verification chip (those are gated-surface
    only)."""
    r = client.get("/arcade")
    assert r.status_code == 200
    lowered = r.text.lower()
    for gated in ("askverify", "verified done", "verify chip", "verification chip"):
        assert gated not in lowered


def test_arcade_catalog_summary_strip(client):
    """The top-of-page availability strip counts the committed registry: one
    live game (mineverse), two blocked (lumen-drift, games-web) on two distinct
    owner clicks (ASK-0010, ASK-0011)."""
    r = client.get("/arcade")
    assert r.status_code == 200
    assert "1 live" in r.text
    assert "2 blocked" in r.text
    assert "on 2 owner clicks" in r.text


def test_games_front_door_shows_arcade_summary_strip(client):
    """The /games front door surfaces the Fleet Arcade's launch-readiness at a
    glance — the SAME live/blocked/distinct-owner-clicks summary the /arcade
    catalog carries (reusing arcade.availability_summary over the committed
    registry: 1 live, 2 blocked, 2 distinct owner clicks) — and cross-links to
    /arcade."""
    r = client.get("/games")
    assert r.status_code == 200
    assert "Fleet Arcade" in r.text
    assert "1 live" in r.text
    assert "2 blocked" in r.text
    assert "on 2 owner clicks" in r.text
    assert 'href="/arcade"' in r.text


def test_games_arcade_summary_matches_helper(client, monkeypatch):
    """The strip on /games reflects arcade.availability_summary exactly — no
    duplicated counting. Stub the helper and assert the rendered figures track
    it (singular 'owner click' when the count is 1)."""
    monkeypatch.setattr(
        arcade,
        "availability_summary",
        lambda games: {"total": 5, "live": 4, "blocked": 1, "owner_clicks": 1},
    )
    r = client.get("/games")
    assert r.status_code == 200
    assert "4 live" in r.text
    assert "1 blocked" in r.text
    assert "on 1 owner click" in r.text
    assert "on 1 owner clicks" not in r.text


def test_games_front_door_no_live_verdict_leaks(client):
    """Same hard rail as /arcade: the /games summary is static registry text
    only — never a live askverify verdict / verification chip."""
    r = client.get("/games")
    assert r.status_code == 200
    lowered = r.text.lower()
    for gated in ("askverify", "verified done", "verification chip"):
        assert gated not in lowered


def test_arcade_summary_counts_live_blocked_and_distinct_owner_clicks():
    """The pure helper counts live vs blocked games and the DISTINCT owner
    clicks among the blocked ones (deduplicated by ask_id / owner_action)."""
    games = [
        {"has_link": True},   # live 1
        {"has_link": True},   # live 2
        {"has_link": False, "blocker": {"owner_action": "click A", "ask_id": "ASK-0001"}},
        {"has_link": False, "blocker": {"owner_action": "click B", "ask_id": "ASK-0002"}},
        # same ask_id as an earlier blocked game -> one distinct owner click
        {"has_link": False, "blocker": {"owner_action": "click A again", "ask_id": "ASK-0001"}},
        # blocked with no recorded blocker -> contributes no owner click
        {"has_link": False, "blocker": None, "status_note": "pending"},
    ]
    summary = arcade.availability_summary(games)
    assert summary == {"total": 6, "live": 2, "blocked": 4, "owner_clicks": 2}


def test_arcade_summary_dedupes_idless_clicks_by_owner_action():
    """Blockers without an ask_id dedupe by owner_action text instead — two
    blocked games naming the same click count as one owner click."""
    games = [
        {"has_link": False, "blocker": {"owner_action": "flip the switch"}},
        {"has_link": False, "blocker": {"owner_action": "flip the switch"}},
        {"has_link": False, "blocker": {"owner_action": "press the button"}},
    ]
    summary = arcade.availability_summary(games)
    assert summary["blocked"] == 3
    assert summary["owner_clicks"] == 2


def test_arcade_summary_over_committed_registry():
    """The helper agrees with the committed registry read through the loader:
    1 live, 2 blocked, 2 distinct owner clicks."""
    summary = arcade.availability_summary(arcade.load_games())
    assert summary["total"] == 3
    assert summary["live"] == 1
    assert summary["blocked"] == 2
    assert summary["owner_clicks"] == 2


@pytest.mark.parametrize("bad", [
    None,                      # non-iterable
    42,                        # non-iterable
    ["not a dict", 7, None],   # non-dict entries are skipped, never fatal
])
def test_arcade_summary_fail_soft_on_malformed_input(bad):
    """Fail-soft: a non-iterable input or non-dict entries never raise — they
    degrade to honest zero / skip (the 'degrade, don't invent' doctrine)."""
    summary = arcade.availability_summary(bad)
    assert set(summary) == {"total", "live", "blocked", "owner_clicks"}
    assert all(isinstance(v, int) and v >= 0 for v in summary.values())


def test_arcade_summary_malformed_blocker_contributes_no_owner_click():
    """A blocked game with a malformed (non-dict) blocker counts as blocked but
    adds no owner click — never invents a click it cannot name."""
    games = [
        {"has_link": False, "blocker": "just prose"},
        {"has_link": False, "blocker": {"owner_action": "  "}},  # blank -> no click
    ]
    summary = arcade.availability_summary(games)
    assert summary == {"total": 2, "live": 0, "blocked": 2, "owner_clicks": 0}
