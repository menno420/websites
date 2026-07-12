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
    """All three games are unavailable today — no play/download anchor may render,
    and the 404 games-web Pages URL must not appear as an href (or at all)."""
    r = client.get("/arcade")
    assert r.status_code == 200
    assert f'href="{DEAD_PAGES_URL}' not in r.text
    assert DEAD_PAGES_URL not in r.text
    assert "Play now" not in r.text
    assert "ref=fleet-arcade" not in r.text  # no outbound game link means no attribution ref either
    # honest status notes show instead
    assert "pending" in r.text.lower()


def test_arcade_source_repo_links(client):
    r = client.get("/arcade")
    for repo in ("menno420/gba-homebrew", "menno420/superbot-mineverse", "menno420/product-forge"):
        assert f'href="https://github.com/{repo}"' in r.text


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


def test_committed_registry_is_honest():
    """The committed registry loads, has all three games, and (today) zero live links."""
    games = arcade.load_games()
    assert [g["slug"] for g in games] == ["lumen-drift", "mineverse", "games-web"]
    for g in games:
        assert g["availability"] == "unavailable"
        assert g["url"] is None
        assert g["has_link"] is False
        assert g["status_note"]  # every unavailable game explains itself
