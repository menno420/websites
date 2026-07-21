"""S6 — arcade_detail.html optional richer-detail sections (screenshots /
controls / changelog) behind fail-soft guards.

Network-free, mirroring test_arcade.py: the site feed is primed from a fixture
so the app never touches the network, and the arcade registry is read from tmp
files monkeypatched onto ``arcade.ARCADE_JSON_PATH``. The core guarantee under
test is fail-soft: a game with NO optional data renders exactly as before (no
section, no crash), and MALFORMED optional data degrades to an empty list (no
exception), never fabricated — the same "degrade, don't invent" doctrine the
optional ``blocker`` field already follows.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from botsite import app as app_module
from botsite import arcade
from botsite import data_source as ds

# Minimal site.json fixture so _base_ctx/lifespan never touch the network
# (identical shape to test_arcade.py's FIXTURE).
FIXTURE = {
    "meta": {"build": {"commit": "abcdef1234", "subject": "test build", "committed_at": "2026-07-09T00:00:00Z"}},
    "counts": {"commands": 0, "features": 0, "games": 0},
    "catalogue": [],
    "commands": [],
    "bot_changelog": [],
}


@pytest.fixture()
def client():
    ds.clear_cache()
    ds.prime_cache(FIXTURE)
    ds.set_client(ds.make_client())  # never actually hit (cache is warm)
    with TestClient(app_module.app) as c:
        yield c
    ds.clear_cache()


def _write_registry(tmp_path: Path, entry: dict) -> Path:
    """Write a one-game registry with the shared required fields plus whatever
    optional fields the test entry carries, and return its path."""
    base = {
        "slug": "g", "name": "G", "tagline": "t", "description": "d",
        "maturity": "beta", "availability": "unavailable", "url": None,
        "source_repo": "menno420/x", "status_note": "n",
    }
    base.update(entry)
    reg = tmp_path / "arcade.json"
    reg.write_text(json.dumps([base]), encoding="utf-8")
    return reg


# --------------------------------------------------------------------------- #
# Loader normalizers — pure, no client.
# --------------------------------------------------------------------------- #

def test_loader_normalizes_valid_optional_fields(tmp_path):
    reg = _write_registry(tmp_path, {
        "screenshots": [{"src": "/static/shots/a.png", "alt": "opening cave"}],
        "controls": [{"input": "A", "action": "Thrust"}, "Bare action line"],
        "changelog": [{"version": "v1.1", "note": "the echoes deepen"}],
    })
    (game,) = arcade.load_games(reg)
    assert game["screenshots"] == [{"src": "/static/shots/a.png", "alt": "opening cave"}]
    assert game["controls"] == [
        {"input": "A", "action": "Thrust"},
        {"input": "", "action": "Bare action line"},
    ]
    assert game["changelog"] == [{"version": "v1.1", "date": "", "note": "the echoes deepen"}]


def test_loader_missing_optional_fields_are_empty_lists(tmp_path):
    """A game with none of the optional fields still gets them present as []
    (so the template guards are always safe to evaluate)."""
    reg = _write_registry(tmp_path, {})
    (game,) = arcade.load_games(reg)
    assert game["screenshots"] == []
    assert game["controls"] == []
    assert game["changelog"] == []


@pytest.mark.parametrize("screenshots", [
    "not a list",                              # wrong type
    ["not a dict", 7],                         # non-dict entries dropped
    [{"alt": "no src"}],                       # missing src
    [{"src": "  ", "alt": "blank src"}],       # blank src
    [{"src": 42}],                             # non-string src
])
def test_loader_malformed_screenshots_degrade_to_empty(tmp_path, screenshots):
    reg = _write_registry(tmp_path, {"screenshots": screenshots})
    (game,) = arcade.load_games(reg)
    assert game["screenshots"] == []


@pytest.mark.parametrize("controls", [
    "not a list",                              # wrong type
    [42, None, {"input": "A"}],                # missing action / non-str
    [{"action": "  "}],                        # blank action
    [""],                                      # blank string
])
def test_loader_malformed_controls_degrade_to_empty(tmp_path, controls):
    reg = _write_registry(tmp_path, {"controls": controls})
    (game,) = arcade.load_games(reg)
    assert game["controls"] == []


@pytest.mark.parametrize("changelog", [
    "not a list",                              # wrong type
    [{"note": "orphan note"}],                 # no version or date -> dropped
    [{"version": "v1"}],                       # missing note
    [{"version": "v1", "note": "  "}],         # blank note
    ["just a string"],                         # non-dict entry
])
def test_loader_malformed_changelog_degrades_to_empty(tmp_path, changelog):
    reg = _write_registry(tmp_path, {"changelog": changelog})
    (game,) = arcade.load_games(reg)
    assert game["changelog"] == []


def test_loader_drops_only_the_malformed_entries(tmp_path):
    """A mix of good and bad entries keeps the good ones — a bad entry costs
    only itself, never the whole field."""
    reg = _write_registry(tmp_path, {
        "controls": [{"input": "A", "action": "good"}, {"input": "B"}, "also good"],
        "changelog": [
            {"version": "v1", "note": "kept"},
            {"note": "dropped, no version/date"},
            {"date": "2026-07-11", "note": "kept by date"},
        ],
    })
    (game,) = arcade.load_games(reg)
    assert game["controls"] == [
        {"input": "A", "action": "good"},
        {"input": "", "action": "also good"},
    ]
    assert game["changelog"] == [
        {"version": "v1", "date": "", "note": "kept"},
        {"version": "", "date": "2026-07-11", "note": "kept by date"},
    ]


# --------------------------------------------------------------------------- #
# Template rendering — WITH data renders the section, WITHOUT renders none.
# --------------------------------------------------------------------------- #

def test_detail_renders_all_three_sections_when_present(client, monkeypatch, tmp_path):
    reg = _write_registry(tmp_path, {
        "screenshots": [{"src": "/static/shots/opening.png", "alt": "the opening cave"}],
        "controls": [{"input": "A", "action": "Thrust upward"}],
        "changelog": [{"version": "v1.3", "note": "pause and mute added"}],
    })
    monkeypatch.setattr(arcade, "ARCADE_JSON_PATH", reg)
    r = client.get("/arcade/g")
    assert r.status_code == 200
    # screenshots section: a lazy-loaded img for the committed asset
    assert "<h3>Screenshots</h3>" in r.text
    assert 'src="/static/shots/opening.png"' in r.text
    assert 'alt="the opening cave"' in r.text
    assert 'loading="lazy"' in r.text
    # controls section: input + action rendered
    assert "<h3>Controls</h3>" in r.text
    assert "<code>A</code>" in r.text
    assert "Thrust upward" in r.text
    # changelog section: version + note rendered
    assert "<h3>Changelog</h3>" in r.text
    assert "v1.3" in r.text
    assert "pause and mute added" in r.text


def test_detail_renders_no_optional_sections_when_absent(client, monkeypatch, tmp_path):
    """The core fail-soft guarantee: a game with no optional data renders
    exactly as before — none of the three section headings appear, and the
    page does not crash."""
    reg = _write_registry(tmp_path, {})
    monkeypatch.setattr(arcade, "ARCADE_JSON_PATH", reg)
    r = client.get("/arcade/g")
    assert r.status_code == 200
    assert "<h3>Screenshots</h3>" not in r.text
    assert "<h3>Controls</h3>" not in r.text
    assert "<h3>Changelog</h3>" not in r.text


def test_detail_malformed_optional_data_renders_no_section_and_no_crash(client, monkeypatch, tmp_path):
    """Malformed optional data (screenshots as a string, changelog entries
    missing keys, controls missing action) degrades to empty — the sections are
    hidden and the page still returns 200, never a 500."""
    reg = _write_registry(tmp_path, {
        "screenshots": "not a list at all",
        "controls": [{"input": "A"}, 42],
        "changelog": [{"note": "no version"}, "junk"],
    })
    monkeypatch.setattr(arcade, "ARCADE_JSON_PATH", reg)
    r = client.get("/arcade/g")
    assert r.status_code == 200
    assert "<h3>Screenshots</h3>" not in r.text
    assert "<h3>Controls</h3>" not in r.text
    assert "<h3>Changelog</h3>" not in r.text


def test_detail_controls_only_renders_just_controls(client, monkeypatch, tmp_path):
    """Each section is independent: a game with only controls shows the controls
    section and neither of the other two."""
    reg = _write_registry(tmp_path, {"controls": ["D-pad to move"]})
    monkeypatch.setattr(arcade, "ARCADE_JSON_PATH", reg)
    r = client.get("/arcade/g")
    assert r.status_code == 200
    assert "<h3>Controls</h3>" in r.text
    assert "D-pad to move" in r.text
    assert "<h3>Screenshots</h3>" not in r.text
    assert "<h3>Changelog</h3>" not in r.text


# --------------------------------------------------------------------------- #
# Committed registry — the fields the real data actually carries (honest pin).
# --------------------------------------------------------------------------- #

def test_committed_registry_optional_fields_present_and_honest():
    """The committed registry carries the real, build-time-verified detail
    fields: every game has controls/screenshots/changelog present (possibly
    empty). mineverse documents no controls (left absent -> []); no game ships
    a screenshot (owner-held / not capturable -> [])."""
    by_slug = {g["slug"]: g for g in arcade.load_games()}
    for slug, g in by_slug.items():
        # always present so the template guards are safe
        assert isinstance(g["screenshots"], list)
        assert isinstance(g["controls"], list)
        assert isinstance(g["changelog"], list)
        # screenshots stayed absent for all four (correct fail-soft outcome)
        assert g["screenshots"] == []
    # the games with documented controls really carry them
    assert by_slug["lumen-drift"]["controls"]
    assert by_slug["gloamline"]["controls"]
    assert by_slug["games-web"]["controls"]
    # mineverse documents no controls -> honestly absent
    assert by_slug["mineverse"]["controls"] == []
    # every game has a real changelog read from its source repo
    for slug in ("lumen-drift", "gloamline", "mineverse", "games-web"):
        assert by_slug[slug]["changelog"], slug


def test_committed_detail_pages_render_the_real_sections(client):
    """The committed detail pages render the sections their real data supports
    and skip the ones they don't — a live end-to-end check over the shipped
    registry (no monkeypatch)."""
    # lumen-drift documents controls + changelog, no screenshots
    r = client.get("/arcade/lumen-drift")
    assert r.status_code == 200
    assert "<h3>Controls</h3>" in r.text
    assert "<h3>Changelog</h3>" in r.text
    assert "<h3>Screenshots</h3>" not in r.text
    # mineverse: changelog only, no controls section
    r = client.get("/arcade/mineverse")
    assert r.status_code == 200
    assert "<h3>Changelog</h3>" in r.text
    assert "<h3>Controls</h3>" not in r.text
    assert "<h3>Screenshots</h3>" not in r.text
