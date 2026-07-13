"""/field-manual funnel-page tests — network-free (site feed primed from a
fixture; the field-manual data and the vetting catalog read from committed
JSON on disk or from tmp files)."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from botsite import app as app_module
from botsite import catalog
from botsite import data_source as ds
from botsite import field_manual

# Minimal site.json fixture so _base_ctx/lifespan never touch the network.
FIXTURE = {
    "meta": {"build": {"commit": "abcdef1234", "subject": "test build", "committed_at": "2026-07-09T00:00:00Z"}},
    "counts": {"commands": 0, "features": 0, "games": 0},
    "catalogue": [],
    "commands": [],
    "bot_changelog": [],
}

VENTURE_SHA = "0679327a463c063dcd9fc62b33ffb9a3789fa7d3"


def _catalog_entry(**overrides):
    base = {
        "slug": field_manual.BOOK_SLUG,
        "title": "Agent Fleet Field Manual",
        "category": "digital product / eBook (field manual)",
        "kind": "digital-product",
        "price": "$39 one-time",
        "status": "publish-ready",
        "status_note": "Publish-ready up to the owner gate.",
        "url": None,
        "source": "venture-lab docs/publishing/vetting/agent-fleet-field-manual.md @ 2c039e3",
        "as_of": "2026-07-13",
    }
    base.update(overrides)
    return base


def _write_catalog(tmp_path, monkeypatch, entries):
    reg = tmp_path / "catalog.json"
    reg.write_text(json.dumps(entries), encoding="utf-8")
    monkeypatch.setattr(catalog, "CATALOG_JSON_PATH", reg)


@pytest.fixture()
def client():
    ds.clear_cache()
    ds.prime_cache(FIXTURE)
    ds.set_client(ds.make_client())  # never actually hit (cache is warm)
    with TestClient(app_module.app) as c:
        yield c
    ds.clear_cache()


# --------------------------------------------------------------------------- #
# The page, against the committed data (no url today → honest CTA)
# --------------------------------------------------------------------------- #
def test_page_renders_with_clarity_hero(client):
    r = client.get("/field-manual")
    assert r.status_code == 200
    assert 'class="sb-page-hero"' in r.text
    assert "<h1>Agent Fleet Field Manual</h1>" in r.text
    assert 'class="sb-lead"' in r.text
    assert "eleven-chapter field manual" in r.text
    assert "free" in r.text.lower()


def test_page_carries_the_pitch(client):
    r = client.get("/field-manual")
    assert r.status_code == 200
    assert "The scar tissue of running an agent fleet" in r.text
    assert "$39" in r.text
    assert "Born-red work tracking" in r.text
    assert "Born-Red Session Cards" in r.text  # chapter list renders
    assert "What it is NOT (honest)" in r.text
    assert "Not a framework tutorial" in r.text


def test_page_carries_the_free_chapter(client):
    r = client.get("/field-manual")
    assert r.status_code == 200
    assert "The D1 Lesson: Never Claim a Payment Path Works Without Executing It" in r.text
    assert "customer_details.email" in r.text
    assert "{CHECKOUT_SESSION_ID}" in r.text
    assert "thirteen passing tests" in r.text
    assert "vendored" in r.text


def test_page_shows_excerpt_provenance(client):
    r = client.get("/field-manual")
    assert r.status_code == 200
    assert "menno420/venture-lab" in r.text
    assert "docs/launch/agent-fleet-field-manual/chapter-01-the-d1-lesson.md" in r.text
    assert VENTURE_SHA in r.text
    assert "retrieved 2026-07-13" in r.text


def test_page_cross_links_to_store_and_catalog(client):
    r = client.get("/field-manual")
    assert r.status_code == 200
    assert 'href="/products"' in r.text
    assert 'href="/products/catalog"' in r.text


def test_honest_cta_when_catalog_has_no_url(client):
    """The committed catalog entry has url: null today — the page must say
    the publish click is queued to the owner and render NO buy link."""
    r = client.get("/field-manual")
    assert r.status_code == 200
    assert "not purchasable yet" in r.text
    assert "queued to the owner" in r.text
    assert "Buy —" not in r.text
    assert "gumroad.com" not in r.text  # no invented store link, anywhere


def test_nav_reaches_the_page(client):
    r = client.get("/")
    assert r.status_code == 200
    assert 'href="/field-manual"' in r.text


# --------------------------------------------------------------------------- #
# CTA flips automatically when the committed catalog gains a url
# --------------------------------------------------------------------------- #
def test_buy_link_appears_when_catalog_entry_goes_live(client, monkeypatch, tmp_path):
    _write_catalog(tmp_path, monkeypatch, [
        _catalog_entry(status="live", url="https://example.gumroad.com/l/field-manual"),
    ])
    r = client.get("/field-manual")
    assert r.status_code == 200
    assert 'href="https://example.gumroad.com/l/field-manual?ref=fleet-store"' in r.text
    assert "Buy — $39 one-time" in r.text
    assert "not purchasable yet" not in r.text


def test_buy_link_appears_the_moment_a_url_exists_even_before_status_flips(client, monkeypatch, tmp_path):
    """The wiring is on the url itself: a catalog entry that gains a real
    url shows it as the buy link even if the status field lags."""
    _write_catalog(tmp_path, monkeypatch, [
        _catalog_entry(status="publish-ready", url="https://example.gumroad.com/l/field-manual"),
    ])
    r = client.get("/field-manual")
    assert r.status_code == 200
    assert 'href="https://example.gumroad.com/l/field-manual?ref=fleet-store"' in r.text
    assert "Buy — $39 one-time" in r.text


def test_honest_fallback_when_entry_missing_from_catalog(client, monkeypatch, tmp_path):
    _write_catalog(tmp_path, monkeypatch, [])
    r = client.get("/field-manual")
    assert r.status_code == 200
    assert "not in the committed catalog" in r.text
    assert "Buy —" not in r.text
    # Cross-links survive every CTA state.
    assert 'href="/products"' in r.text
    assert 'href="/products/catalog"' in r.text


# --------------------------------------------------------------------------- #
# Degradation — missing/corrupt data never crashes the page
# --------------------------------------------------------------------------- #
def test_page_degrades_on_missing_data_file(client, monkeypatch, tmp_path):
    monkeypatch.setattr(field_manual, "FIELD_MANUAL_JSON_PATH", tmp_path / "does-not-exist.json")
    r = client.get("/field-manual")
    assert r.status_code == 200
    assert "Pitch unavailable right now" in r.text
    assert "Free chapter unavailable right now" in r.text


def test_page_degrades_on_corrupt_data_file(client, monkeypatch, tmp_path):
    corrupt = tmp_path / "field_manual.json"
    corrupt.write_text("{ this is not json", encoding="utf-8")
    monkeypatch.setattr(field_manual, "FIELD_MANUAL_JSON_PATH", corrupt)
    r = client.get("/field-manual")
    assert r.status_code == 200
    assert "Pitch unavailable right now" in r.text
    assert "Free chapter unavailable right now" in r.text


# --------------------------------------------------------------------------- #
# Loader unit tests
# --------------------------------------------------------------------------- #
def test_committed_data_is_honest():
    """The committed field_manual.json loads: pitch + 11 chapters (exactly
    the kit's 2 marked free), a non-empty excerpt whose provenance pins the
    venture-lab source at the recorded sha."""
    got = field_manual.load_field_manual()
    book, excerpt = got["book"], got["excerpt"]
    assert book is not None and excerpt is not None
    assert book["slug"] == field_manual.BOOK_SLUG
    assert len(book["chapters"]) == 11
    assert sum(1 for c in book["chapters"] if c["free"]) == 2
    assert "@ 0679327" in book["source"]
    assert excerpt["provenance"] == {
        "repo": "menno420/venture-lab",
        "path": "docs/launch/agent-fleet-field-manual/chapter-01-the-d1-lesson.md",
        "commit": VENTURE_SHA,
        "retrieved": "2026-07-13",
    }
    assert len(excerpt["blocks"]) >= 15
    assert all(field_manual._valid_block(b) for b in excerpt["blocks"])


def test_loader_skips_invalid_blocks_and_chapters(tmp_path):
    src = tmp_path / "fm.json"
    src.write_text(json.dumps({
        "book": {
            "slug": "s", "title": "t", "subtitle": "st", "tagline": "tg",
            "description": "d", "who_for": "w", "source": "src", "as_of": "2026-07-13",
            "bullets": ["ok", "", 7],
            "chapters": [
                {"num": "01", "title": "Ch", "line": "L", "free": True},
                {"num": "02", "title": "Bad free", "line": "L", "free": "yes"},
                {"title": "no num", "line": "L", "free": False},
            ],
            "not_claims": ["honest", None],
        },
        "excerpt": {
            "title": "Ex", "chapter": "01",
            "provenance": {"repo": "r", "path": "p", "commit": "c", "retrieved": "2026-07-13"},
            "blocks": [
                {"type": "p", "text": "keep"},
                {"type": "p", "text": ""},
                {"type": "ul", "items": []},
                {"type": "ol", "items": ["one", 2]},
                {"type": "video", "text": "nope"},
                "not a dict",
            ],
        },
    }), encoding="utf-8")
    got = field_manual.load_field_manual(src)
    assert got["book"]["bullets"] == ["ok"]
    assert [c["num"] for c in got["book"]["chapters"]] == ["01"]
    assert got["book"]["not_claims"] == ["honest"]
    assert got["excerpt"]["blocks"] == [{"type": "p", "text": "keep"}]


def test_loader_rejects_excerpt_without_provenance_or_body(tmp_path):
    src = tmp_path / "fm.json"
    src.write_text(json.dumps({
        "book": None,
        "excerpt": {"title": "Ex", "blocks": [{"type": "p", "text": "body"}]},
    }), encoding="utf-8")
    assert field_manual.load_field_manual(src)["excerpt"] is None
    src.write_text(json.dumps({
        "excerpt": {
            "title": "Ex",
            "provenance": {"repo": "r", "path": "p", "commit": "c", "retrieved": "d"},
            "blocks": [],
        },
    }), encoding="utf-8")
    assert field_manual.load_field_manual(src)["excerpt"] is None


def test_loader_degrades_on_missing_and_corrupt_files(tmp_path):
    assert field_manual.load_field_manual(tmp_path / "nope.json") == {"book": None, "excerpt": None}
    bad = tmp_path / "bad.json"
    bad.write_text("[1, 2", encoding="utf-8")
    assert field_manual.load_field_manual(bad) == {"book": None, "excerpt": None}
    a_list = tmp_path / "list.json"
    a_list.write_text("[]", encoding="utf-8")
    assert field_manual.load_field_manual(a_list) == {"book": None, "excerpt": None}


def test_buy_url_only_from_a_real_catalog_url():
    assert field_manual.buy_url(None) is None
    assert field_manual.buy_url({"url": None}) is None
    assert field_manual.buy_url({"url": "  "}) is None
    assert field_manual.buy_url({"url": "https://x.example/buy"}) == "https://x.example/buy?ref=fleet-store"
    assert field_manual.buy_url({"url": "https://x.example/buy?a=1"}) == "https://x.example/buy?a=1&ref=fleet-store"
    # A live entry already carries the ref via the catalog loader.
    assert field_manual.buy_url({"url": "https://x.example/buy", "link_url": "https://x.example/buy?ref=fleet-store"}) == "https://x.example/buy?ref=fleet-store"


def test_committed_catalog_entry_exists_and_has_no_url_yet():
    """Pin the honest present state: the book is in the committed catalog,
    publish-ready, url-less — the exact state the honest CTA renders."""
    entry = field_manual.catalog_entry()
    assert entry is not None
    assert entry["status"] == "publish-ready"
    assert entry["url"] is None
    assert field_manual.buy_url(entry) is None
