"""Puddle Museum page tests — network-free (site feed primed from a fixture,
museum data read from the committed JSON on disk or from tmp files)."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from botsite import app as app_module
from botsite import data_source as ds
from botsite import puddle_museum

# Minimal site.json fixture so _base_ctx/lifespan never touch the network.
FIXTURE = {
    "meta": {"build": {"commit": "abcdef1234", "subject": "test build", "committed_at": "2026-07-09T00:00:00Z"}},
    "counts": {"commands": 0, "features": 0, "games": 0},
    "catalogue": [],
    "commands": [],
    "bot_changelog": [],
}

EXHIBIT_NAMES = (
    "Sky Mirror",
    "Upside-Down Tree",
    "Worm Rescue Wing",
    "Splash Gallery",
    "Puddle of Many Colors",
    "The Whale",
)

EDITION_TITLES = (
    "The Puddle Museum",
    "Het Regenplassenmuseum",
    "Das Pfützenmuseum",
)

# A valid edition entry for loader tests, tweaked per test.
EDITION_BASE = {
    "lang": "en", "title": "T", "language": "English",
    "availability": "coming-soon", "url": None, "status_note": "n",
    "source": "venture-lab x @ 467d619", "as_of": "2026-07-13",
}

EXHIBIT_BASE = {
    "slug": "ok", "emoji": "💧", "name_en": "OK Exhibit",
    "description": "d",
    "source": "venture-lab x @ 467d619", "as_of": "2026-07-13",
}


@pytest.fixture()
def client():
    ds.clear_cache()
    ds.prime_cache(FIXTURE)
    ds.set_client(ds.make_client())  # never actually hit (cache is warm)
    with TestClient(app_module.app) as c:
        yield c
    ds.clear_cache()


def test_page_renders_with_headline_and_lede(client):
    """Clarity: 200, hero h1, and a plain-words sb-lead purpose lede."""
    r = client.get("/puddle-museum")
    assert r.status_code == 200
    assert "<h1>The Puddle Museum</h1>" in r.text
    assert 'class="sb-lead"' in r.text
    assert "picture book" in r.text
    assert "ages 4–8" in r.text


def test_all_six_exhibits_present(client):
    r = client.get("/puddle-museum")
    assert r.status_code == 200
    for name in EXHIBIT_NAMES:
        assert name in r.text
    # Trilingual names show where the packet gave them.
    assert "de Luchtspiegel" in r.text
    assert "der Himmelsspiegel" in r.text
    assert "die Wurmrettungs-Abteilung" in r.text


def test_all_three_edition_titles_present(client):
    r = client.get("/puddle-museum")
    assert r.status_code == 200
    for title in EDITION_TITLES:
        assert title in r.text


def test_no_buy_links_and_no_forms(client):
    """Honesty gate: no store exists, so the page carries zero store hrefs
    and zero forms — it is a GET-only marketing page."""
    r = client.get("/puddle-museum")
    assert r.status_code == 200
    low = r.text.lower()
    assert "amazon" not in low
    assert "gumroad" not in low
    assert 'href="https://store' not in low and "shop." not in low
    assert "<form" not in low
    assert "Get the book" not in r.text  # the buy button never renders


def test_coming_soon_and_status_notes_visible(client):
    r = client.get("/puddle-museum")
    assert r.status_code == 200
    assert "coming soon" in r.text
    assert "Manuscript complete (13 spreads) — illustration and publication are owner-gated." in r.text
    assert "In production — illustration decision pending." in r.text


def test_submissions_teaser_is_honest(client):
    r = client.get("/puddle-museum")
    assert r.status_code == 200
    assert "Submissions open soon." in r.text
    assert "moderation" in r.text
    assert "aren't provisioned yet" in r.text


def test_signature_copy_present(client):
    """The sign and the closing line, verbatim from the packet."""
    r = client.get("/puddle-museum")
    assert r.status_code == 200
    assert "THE PUDDLE MUSEUM — OPEN TODAY ONLY — ADMISSION: ONE LEAF" in r.text
    assert "skipping ropes" in r.text
    assert "You don't get to keep the exhibits. You get to keep the looking." in r.text


def test_provenance_rendered(client):
    r = client.get("/puddle-museum")
    assert r.status_code == 200
    assert "@ 467d619, as of 2026-07-13" in r.text
    assert "venture-lab docs/publishing/vetting/the-puddle-museum.md" in r.text
    assert "candidates/childrens-books/the-puddle-museum/the-puddle-museum.nl.md" in r.text


def test_nav_includes_puddle_museum(client):
    r = client.get("/")
    assert 'href="/puddle-museum"' in r.text
    assert "Puddle Museum" in r.text


def test_page_degrades_on_missing_file(client, monkeypatch, tmp_path):
    monkeypatch.setattr(puddle_museum, "MUSEUM_JSON_PATH", tmp_path / "does-not-exist.json")
    r = client.get("/puddle-museum")
    assert r.status_code == 200
    assert "No exhibits on display" in r.text
    assert "No editions registered" in r.text


def test_page_degrades_on_corrupt_file(client, monkeypatch, tmp_path):
    corrupt = tmp_path / "puddle_museum.json"
    corrupt.write_text("{ this is not json", encoding="utf-8")
    monkeypatch.setattr(puddle_museum, "MUSEUM_JSON_PATH", corrupt)
    r = client.get("/puddle-museum")
    assert r.status_code == 200
    assert "No exhibits on display" in r.text
    assert "No editions registered" in r.text


def test_loader_missing_file_returns_empty(tmp_path):
    got = puddle_museum.load_museum(tmp_path / "nope.json")
    assert got == {"exhibits": [], "editions": []}


def test_loader_corrupt_file_returns_empty(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("[not a dict either way", encoding="utf-8")
    assert puddle_museum.load_museum(bad) == {"exhibits": [], "editions": []}
    # Valid JSON of the wrong shape degrades the same way.
    bad.write_text("[1, 2, 3]", encoding="utf-8")
    assert puddle_museum.load_museum(bad) == {"exhibits": [], "editions": []}


def test_loader_skips_invalid_entries(tmp_path):
    """Entries missing required fields (or with bad enum values) are skipped,
    never fatal."""
    reg = tmp_path / "puddle_museum.json"
    reg.write_text(json.dumps({
        "exhibits": [
            EXHIBIT_BASE,
            {**EXHIBIT_BASE, "slug": "no-name", "name_en": ""},
            {**EXHIBIT_BASE, "slug": "bad-nl", "name_nl": 42},
            "not even a dict",
        ],
        "editions": [
            EDITION_BASE,
            {**EDITION_BASE, "lang": "xx", "availability": "vaporware"},
            {**EDITION_BASE, "lang": "yy", "status_note": ""},
            None,
        ],
    }), encoding="utf-8")
    got = puddle_museum.load_museum(reg)
    assert [e["slug"] for e in got["exhibits"]] == ["ok"]
    assert [e["lang"] for e in got["editions"]] == ["en"]


def test_loader_never_presents_live_without_url(tmp_path):
    reg = tmp_path / "puddle_museum.json"
    reg.write_text(json.dumps({
        "exhibits": [],
        "editions": [{**EDITION_BASE, "availability": "live", "url": None}],
    }), encoding="utf-8")
    (edition,) = puddle_museum.load_museum(reg)["editions"]
    assert edition["is_buyable"] is False


def test_committed_data_nothing_buyable():
    """The committed registry: six exhibits, three editions, every edition
    coming-soon with a null URL — nothing is buyable, every entry cites its
    venture-lab source with an as_of date."""
    got = puddle_museum.load_museum()
    assert [e["name_en"] for e in got["exhibits"]] == list(EXHIBIT_NAMES)
    assert [e["title"] for e in got["editions"]] == list(EDITION_TITLES)
    for exhibit in got["exhibits"]:
        assert "venture-lab" in exhibit["source"]
        assert exhibit["as_of"] == "2026-07-13"
    for edition in got["editions"]:
        assert edition["availability"] == "coming-soon"
        assert edition["url"] is None
        assert edition["is_buyable"] is False
        assert edition["status_note"]
        assert "venture-lab" in edition["source"]


# --------------------------------------------------------------------------- #
# blocker + ask_id — the shared schema (botsite/blockers.py, the arcade's
# PR #360 object extended to the editions 2026-07-16). Optional and
# fail-soft: a malformed blocker costs only the panel, a malformed ask_id
# only the ledger ref — never the edition.
# --------------------------------------------------------------------------- #

def test_loader_normalizes_valid_edition_blocker(tmp_path):
    reg = tmp_path / "puddle_museum.json"
    reg.write_text(json.dumps({
        "exhibits": [],
        "editions": [{**EDITION_BASE,
                      "blocker": {"owner_action": "  decide the thing  ",
                                  "unblocks": " then it ships ",
                                  "ask_id": "  ASK-0042  "}}],
    }), encoding="utf-8")
    (edition,) = puddle_museum.load_museum(reg)["editions"]
    assert edition["blocker"] == {
        "owner_action": "decide the thing", "unblocks": "then it ships",
        "ask_id": "ASK-0042",
    }


@pytest.mark.parametrize("blocker", [
    None, "just prose", {"owner_action": "click"}, {"unblocks": "ships"},
    {"owner_action": "", "unblocks": "ships"},
    {"owner_action": 42, "unblocks": "ships"},
])
def test_loader_malformed_blocker_degrades_to_none(tmp_path, blocker):
    """A missing/malformed blocker is fail-soft: it normalizes to None and
    never invalidates the edition (degrade, don't invent)."""
    reg = tmp_path / "puddle_museum.json"
    reg.write_text(json.dumps({
        "exhibits": [],
        "editions": [{**EDITION_BASE, "blocker": blocker}],
    }), encoding="utf-8")
    (edition,) = puddle_museum.load_museum(reg)["editions"]
    assert edition["lang"] == "en"  # the edition survives
    assert edition["blocker"] is None


@pytest.mark.parametrize("ask_id", [
    42, "", "   ", "ASK-42", "ASK-00100", "ask-0010",
    "see ASK-0010", "ASK-0010 maybe",
])
def test_loader_malformed_ask_id_degrades_to_none_but_keeps_blocker(tmp_path, ask_id):
    reg = tmp_path / "puddle_museum.json"
    reg.write_text(json.dumps({
        "exhibits": [],
        "editions": [{**EDITION_BASE,
                      "blocker": {"owner_action": "decide",
                                  "unblocks": "ships", "ask_id": ask_id}}],
    }), encoding="utf-8")
    (edition,) = puddle_museum.load_museum(reg)["editions"]
    assert edition["blocker"] is not None
    assert edition["blocker"]["owner_action"] == "decide"
    assert edition["blocker"]["ask_id"] is None


def test_committed_editions_all_join_the_illustration_gate():
    """All three committed editions wait on the same one owner decision —
    the §5 illustration gate, ledger row ASK-0015 (the same id the two
    parked picture books carry in catalog.json; cross-pinned repo-wide by
    tests/test_askverify.py)."""
    editions = puddle_museum.load_museum()["editions"]
    assert len(editions) == 3
    for edition in editions:
        blocker = edition["blocker"]
        assert blocker is not None, edition["lang"]
        assert blocker["owner_action"].strip()
        assert blocker["unblocks"].strip()
        assert blocker["ask_id"] == "ASK-0015", edition["lang"]


def test_page_renders_edition_blocker_panels_with_ledger_refs(client):
    """Each coming-soon edition card renders the blocker panel: the owner
    decision, how it unblocks, and the guarded ledger ref."""
    r = client.get("/puddle-museum")
    assert r.status_code == 200
    assert r.text.count("The owner click:") == 3
    assert r.text.count("How it unblocks:") == 3
    assert r.text.count("Ledger ref:") == 3
    assert r.text.count("<code>ASK-0015</code>") == 3
    assert "owner-actions ledger" in r.text
    # the honesty gate holds: still no store links, no forms
    assert "gumroad" not in r.text.lower()
    assert "<form" not in r.text.lower()


def test_page_idless_blocker_renders_panel_without_ledger_ref(
    client, monkeypatch, tmp_path
):
    reg = tmp_path / "puddle_museum.json"
    reg.write_text(json.dumps({
        "exhibits": [],
        "editions": [{**EDITION_BASE,
                      "blocker": {"owner_action": "decide the thing",
                                  "unblocks": "then it ships"}}],
    }), encoding="utf-8")
    monkeypatch.setattr(puddle_museum, "MUSEUM_JSON_PATH", reg)
    r = client.get("/puddle-museum")
    assert r.status_code == 200
    assert "The owner click:" in r.text
    assert "decide the thing" in r.text
    assert "Ledger ref:" not in r.text
