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

# games-web's GitHub Pages deployment — LIVE since 2026-07-18 (ASK-0011: the
# owner ran product-forge's Pages deploy; the site answers 200 with the real
# character-sheet app). The old dead-URL pin is retired: this URL is now a real
# outbound link, not a URL that must never appear.
GAMES_WEB_URL = "https://menno420.github.io/product-forge/"

# lumen-drift's published GitHub Release page — the download target since
# 2026-07-18 (ASK-0010: the owner published lumen-drift-v1.3; availability is
# now "download").
LUMEN_DRIFT_URL = "https://github.com/menno420/gba-homebrew/releases/tag/lumen-drift-v1.3"

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


def test_arcade_all_committed_games_are_reachable_after_the_flip(client):
    """Both launch blockers cleared 2026-07-18 (ASK-0010 lumen-drift release +
    ASK-0011 games-web Pages): every committed game now renders a real outbound
    link with the attribution ref — games-web's Pages URL, once the dead-URL
    pin, is now a live Play link, and lumen-drift a Download link. No blocker
    panel or 'pending' note survives on the catalog."""
    r = client.get("/arcade")
    assert r.status_code == 200
    # the formerly-dead games-web Pages URL is now a real outbound Play link
    assert f'href="{GAMES_WEB_URL}?ref=fleet-arcade"' in r.text
    # lumen-drift's published release is now a Download link
    assert f'href="{LUMEN_DRIFT_URL}?ref=fleet-arcade"' in r.text
    # nothing is blocked any more: no owner-click panel, no pending note
    assert "The owner click:" not in r.text
    assert "pending" not in r.text.lower()


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


def test_arcade_links_back_to_games(client):
    """A2: the /arcade catalog cross-links to the in-chat /games surface, so a
    visitor who lands on the arcade first can reach the in-chat games — the two
    overlapping surfaces are mutually reachable, not a one-way dead end."""
    r = client.get("/arcade")
    assert r.status_code == 200
    assert 'href="/games"' in r.text


def test_games_links_to_arcade(client):
    """A2 (the already-shipped direction): the /games page cross-links to the
    /arcade catalog. Both halves of the cross-link are asserted so a regression
    on either surface is caught."""
    r = client.get("/games")
    assert r.status_code == 200
    assert 'href="/arcade"' in r.text


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
    """The committed registry loads with all three games, and after the
    2026-07-18 flip every one is reachable: mineverse live (ORDER 022),
    games-web live (ASK-0011 Pages deploy), lumen-drift download (ASK-0010
    published release). Each renders an outbound link with the attribution ref
    and keeps an honest status note; none carries a blocker."""
    games = arcade.load_games()
    assert [g["slug"] for g in games] == ["lumen-drift", "mineverse", "games-web"]
    by_slug = {g["slug"]: g for g in games}

    mv = by_slug["mineverse"]
    assert mv["availability"] == "live"
    assert mv["url"] == MINEVERSE_URL
    assert mv["is_live"] is True and mv["has_link"] is True
    assert mv["link_url"] == f"{MINEVERSE_URL}?ref=fleet-arcade"

    gw = by_slug["games-web"]
    assert gw["availability"] == "live"
    assert gw["url"] == GAMES_WEB_URL
    assert gw["is_live"] is True and gw["has_link"] is True
    assert gw["link_url"] == f"{GAMES_WEB_URL}?ref=fleet-arcade"

    ld = by_slug["lumen-drift"]
    assert ld["availability"] == "download"
    assert ld["url"] == LUMEN_DRIFT_URL
    # a download game is has_link (a Download button) but NOT is_live
    assert ld["is_live"] is False and ld["has_link"] is True
    assert ld["link_url"] == f"{LUMEN_DRIFT_URL}?ref=fleet-arcade"

    for g in games:
        assert g["status_note"]  # every game still explains itself honestly
        assert g["blocker"] is None  # no launch blockers remain


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


def test_arcade_detail_lumen_drift_download_affordance(client):
    """The GBA game flipped to download (ASK-0010, 2026-07-18): its detail page
    carries a real Download button to the published release and NO blocker
    panel — the launch is no longer blocked."""
    r = client.get("/arcade/lumen-drift")
    assert r.status_code == 200
    assert f'href="{LUMEN_DRIFT_URL}?ref=fleet-arcade"' in r.text
    assert "Download" in r.text
    # honest: the blocker panel is gone now the game is reachable
    assert "What's blocking launch" not in r.text
    assert "The owner click:" not in r.text
    # a download game is not "live" — no Play affordance
    assert "Play now" not in r.text


def test_arcade_detail_games_web_play_affordance(client):
    """games-web flipped to live (ASK-0011 Pages deploy, 2026-07-18): its detail
    page carries a real Play link to the Pages site and NO blocker panel. The
    formerly-dead Pages URL is now an honest outbound link."""
    r = client.get("/arcade/games-web")
    assert r.status_code == 200
    assert f'href="{GAMES_WEB_URL}?ref=fleet-arcade"' in r.text
    assert "Play now" in r.text
    assert "What's blocking launch" not in r.text
    assert "The owner click:" not in r.text


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


def test_committed_registry_carries_no_blockers_after_the_flip():
    """Schema guard on the committed registry post-flip (2026-07-18): both
    arcade launch blockers cleared (ASK-0010 lumen-drift release + ASK-0011
    games-web Pages), so NO game carries a blocker now — every game is
    reachable. Detail URLs still derive from slugs."""
    by_slug = {g["slug"]: g for g in arcade.load_games()}
    for slug, g in by_slug.items():
        assert g["blocker"] is None, slug
        assert g["has_link"] is True, slug  # every game is reachable
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


def test_committed_registry_no_longer_carries_the_launch_blocker_ask_ids():
    """Post-flip (2026-07-18) the committed registry carries no blocker at all,
    so neither ASK-0010 nor ASK-0011 is joined from arcade.json any more (both
    moved to Decided rows P/Q in docs/owner/OWNER-ACTIONS.md; the id-consistency
    pin now lives in tests/test_askverify.py)."""
    by_slug = {g["slug"]: g for g in arcade.load_games()}
    for slug in ("lumen-drift", "games-web"):
        assert by_slug[slug]["blocker"] is None


def test_arcade_detail_renders_no_ledger_ref_after_the_flip(client):
    """With every game reachable and no blocker, no detail page renders a
    'Ledger ref:' line — the visible half of the ask_id join is gone with the
    blocker panels."""
    for slug in ("lumen-drift", "games-web", "mineverse"):
        r = client.get(f"/arcade/{slug}")
        assert r.status_code == 200
        assert "Ledger ref:" not in r.text


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

def test_arcade_catalog_cards_carry_no_blocker_after_the_flip(client):
    """Post-flip (2026-07-18) no catalog card carries a blocking owner click or
    ledger ref — both blockers cleared (ASK-0010 / ASK-0011), so the cards show
    their reachable Play/Download affordances instead of an owner-click panel."""
    r = client.get("/arcade")
    assert r.status_code == 200
    assert "The owner click:" not in r.text
    assert "Ledger ref:" not in r.text
    assert "<code>ASK-0010</code>" not in r.text
    assert "<code>ASK-0011</code>" not in r.text


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
    """The top-of-page availability strip counts the committed registry post-flip
    (2026-07-18): all three games reachable (mineverse + games-web live,
    lumen-drift download), zero blocked, so no owner-click clause renders."""
    r = client.get("/arcade")
    assert r.status_code == 200
    assert "3 live" in r.text
    assert "0 blocked" in r.text
    assert "owner click" not in r.text  # nothing blocked → no owner-click clause


def test_games_front_door_shows_arcade_summary_strip(client):
    """The /games front door surfaces the Fleet Arcade's launch-readiness at a
    glance — the SAME live/blocked/owner-clicks summary the /arcade catalog
    carries (reusing arcade.availability_summary over the committed registry,
    post-flip: 3 live, 0 blocked, 0 owner clicks) — and cross-links to
    /arcade."""
    r = client.get("/games")
    assert r.status_code == 200
    assert "Fleet Arcade" in r.text
    assert "3 live" in r.text
    assert "0 blocked" in r.text
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
    """The helper agrees with the committed registry read through the loader,
    post-flip (2026-07-18): all three games reachable, none blocked, no
    outstanding owner clicks."""
    summary = arcade.availability_summary(arcade.load_games())
    assert summary["total"] == 3
    assert summary["live"] == 3
    assert summary["blocked"] == 0
    assert summary["owner_clicks"] == 0


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


# --- Owner action queue (arcade.pending_owner_actions) ---------------------- #


def test_pending_owner_actions_lists_distinct_clicks_with_games():
    """The queue names each DISTINCT owner click once, in first-seen order,
    carrying its ask_id and the games it unblocks. Two blocked games sharing an
    ask_id collapse into one entry whose ``games`` list holds both names."""
    games = [
        {"has_link": True, "name": "Live One"},
        {"has_link": False, "name": "Alpha",
         "blocker": {"owner_action": "click A", "ask_id": "ASK-0001"}},
        {"has_link": False, "name": "Bravo",
         "blocker": {"owner_action": "click B", "ask_id": "ASK-0002"}},
        {"has_link": False, "name": "Charlie",
         "blocker": {"owner_action": "click A again", "ask_id": "ASK-0001"}},
    ]
    actions = arcade.pending_owner_actions(games)
    assert actions == [
        {"owner_action": "click A", "ask_id": "ASK-0001", "games": ["Alpha", "Charlie"]},
        {"owner_action": "click B", "ask_id": "ASK-0002", "games": ["Bravo"]},
    ]


def test_pending_owner_actions_length_equals_summary_owner_clicks():
    """The queue's length tracks the summary strip's owner-click count exactly —
    the panel and the count can never disagree — over the committed registry."""
    games = arcade.load_games()
    actions = arcade.pending_owner_actions(games)
    assert len(actions) == arcade.availability_summary(games)["owner_clicks"]


def test_pending_owner_actions_dedupes_idless_clicks_by_owner_action():
    """Blockers without an ask_id dedupe by owner_action text — two games naming
    the same click collapse to one entry (ask_id None)."""
    games = [
        {"has_link": False, "name": "Alpha", "blocker": {"owner_action": "flip the switch"}},
        {"has_link": False, "name": "Bravo", "blocker": {"owner_action": "flip the switch"}},
        {"has_link": False, "name": "Charlie", "blocker": {"owner_action": "press the button"}},
    ]
    actions = arcade.pending_owner_actions(games)
    assert actions == [
        {"owner_action": "flip the switch", "ask_id": None, "games": ["Alpha", "Bravo"]},
        {"owner_action": "press the button", "ask_id": None, "games": ["Charlie"]},
    ]


def test_pending_owner_actions_skips_live_and_unnameable():
    """Only blocked games with a nameable blocker contribute: a live game, a
    non-dict blocker, and a blank owner_action all yield no queue entry."""
    games = [
        {"has_link": True, "name": "Live", "blocker": {"owner_action": "ignored"}},
        {"has_link": False, "name": "Prose", "blocker": "just prose"},
        {"has_link": False, "name": "Blank", "blocker": {"owner_action": "  "}},
        {"has_link": False, "name": "Real", "blocker": {"owner_action": "do the thing"}},
    ]
    actions = arcade.pending_owner_actions(games)
    assert actions == [
        {"owner_action": "do the thing", "ask_id": None, "games": ["Real"]},
    ]


@pytest.mark.parametrize("bad", [None, 42, ["not a dict", 7, None]])
def test_pending_owner_actions_fail_soft_on_malformed_input(bad):
    """Fail-soft: a non-iterable input or non-dict entries never raise — they
    degrade to an empty queue (the 'degrade, don't invent' doctrine)."""
    assert arcade.pending_owner_actions(bad) == []


def test_arcade_page_omits_owner_action_queue_when_nothing_is_blocked(client):
    """Post-flip (2026-07-18) no game is blocked, so the consolidated owner
    action queue panel is not rendered at all — the panel only appears when
    there are pending owner clicks (arcade.pending_owner_actions is empty here),
    and neither retired ask id leaks onto the page."""
    r = client.get("/arcade")
    assert r.status_code == 200
    assert "Owner action queue" not in r.text
    assert "ASK-0010" not in r.text
    assert "ASK-0011" not in r.text
