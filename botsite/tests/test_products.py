"""Fleet store tests — network-free (site feed primed from a fixture, product
registry read from the committed JSON on disk or from tmp files)."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from botsite import app as app_module
from botsite import data_source as ds
from botsite import products

# Minimal site.json fixture so _base_ctx/lifespan never touch the network.
FIXTURE = {
    "meta": {"build": {"commit": "abcdef1234", "subject": "test build", "committed_at": "2026-07-09T00:00:00Z"}},
    "counts": {"commands": 0, "features": 0, "games": 0},
    "catalogue": [],
    "commands": [],
    "bot_changelog": [],
}

# The one live product's Gumroad URL (live since 2026-07-12).
SWTK_URL = "https://mennomagic01.gumroad.com/l/stripe-webhook-test-kit"

ALL_NAMES = (
    "Stripe Webhook Test Kit v0.1",
    "Membership-Site Boilerplate Kit v0.2",
    "Agent-Workflow Template Pack v0.1",
    "Agent Fleet Field Manual v0.1",
)


@pytest.fixture()
def client():
    ds.clear_cache()
    ds.prime_cache(FIXTURE)
    ds.set_client(ds.make_client())  # never actually hit (cache is warm)
    with TestClient(app_module.app) as c:
        yield c
    ds.clear_cache()


def test_products_lists_all_products_with_prices(client):
    r = client.get("/products")
    assert r.status_code == 200
    for name in ALL_NAMES:
        assert name in r.text
    assert "$29 one-time" in r.text
    assert "$49 one-time" in r.text
    assert "Pay what you want — $19 suggested" in r.text
    assert "$39 one-time" in r.text


def test_products_lede_states_what_the_page_is(client):
    """Clarity: a first-time visitor learns this is the fleet's storefront."""
    r = client.get("/products")
    assert r.status_code == 200
    assert "product storefront" in r.text
    assert "built by the agent" in r.text
    assert "Gumroad" in r.text


def test_products_live_buy_link_carries_ref(client):
    """The one live product renders a buy link with the attribution ref."""
    r = client.get("/products")
    assert r.status_code == 200
    assert f'href="{SWTK_URL}?ref=fleet-store"' in r.text
    assert "Buy on Gumroad" in r.text


def test_products_coming_soon_have_no_buy_links(client):
    """Coming-soon products render honest status notes and never a Gumroad
    href — the only Gumroad link on the page is the one live product's."""
    r = client.get("/products")
    assert r.status_code == 200
    assert r.text.count("gumroad.com") == 1
    assert r.text.count("Buy on Gumroad") == 1
    assert "Publish click queued to the owner — not yet purchasable." in r.text
    assert "coming soon" in r.text


def test_products_source_and_as_of_notes(client):
    r = client.get("/products")
    assert r.status_code == 200
    assert "@ e01fa01, as of 2026-07-13" in r.text
    assert "venture-lab docs/launch/stripe-webhook-test-kit/LISTING.md" in r.text


def test_nav_includes_products(client):
    r = client.get("/")
    assert 'href="/products"' in r.text
    assert "Products" in r.text


def test_products_degrades_on_missing_file(client, monkeypatch, tmp_path):
    monkeypatch.setattr(products, "PRODUCTS_JSON_PATH", tmp_path / "does-not-exist.json")
    r = client.get("/products")
    assert r.status_code == 200
    assert "No products registered yet" in r.text


def test_products_degrades_on_corrupt_file(client, monkeypatch, tmp_path):
    corrupt = tmp_path / "products.json"
    corrupt.write_text("{ this is not json", encoding="utf-8")
    monkeypatch.setattr(products, "PRODUCTS_JSON_PATH", corrupt)
    r = client.get("/products")
    assert r.status_code == 200
    assert "No products registered yet" in r.text


def test_loader_skips_invalid_entries(tmp_path):
    """Entries missing required fields (or with bad enum values) are skipped, not fatal."""
    reg = tmp_path / "products.json"
    reg.write_text(json.dumps([
        {"slug": "ok", "name": "OK Kit", "tagline": "t", "description": "d",
         "price": "$1", "availability": "coming-soon", "url": None,
         "source": "venture-lab x @ e01fa01", "as_of": "2026-07-13", "status_note": "n"},
        {"slug": "no-name", "tagline": "t", "description": "d",
         "price": "$1", "availability": "coming-soon", "url": None,
         "source": "venture-lab x @ e01fa01", "as_of": "2026-07-13"},
        {"slug": "bad-availability", "name": "Bad", "tagline": "t", "description": "d",
         "price": "$1", "availability": "vaporware", "url": None,
         "source": "venture-lab x @ e01fa01", "as_of": "2026-07-13"},
        "not even a dict",
    ]), encoding="utf-8")
    got = products.load_products(reg)
    assert [p["slug"] for p in got] == ["ok"]


def test_loader_never_presents_live_without_url(tmp_path):
    reg = tmp_path / "products.json"
    reg.write_text(json.dumps([
        {"slug": "claims-live", "name": "Claims Live", "tagline": "t", "description": "d",
         "price": "$1", "availability": "live", "url": None,
         "source": "venture-lab x @ e01fa01", "as_of": "2026-07-13", "status_note": "n"},
    ]), encoding="utf-8")
    (product,) = products.load_products(reg)
    assert product["is_live"] is False
    assert product["has_link"] is False
    assert product["link_url"] is None


def test_loader_adds_attribution_ref(tmp_path):
    reg = tmp_path / "products.json"
    reg.write_text(json.dumps([
        {"slug": "really-live", "name": "Really Live", "tagline": "t", "description": "d",
         "price": "$1", "availability": "live", "url": "https://example.com/buy",
         "source": "venture-lab x @ e01fa01", "as_of": "2026-07-13", "status_note": ""},
    ]), encoding="utf-8")
    (product,) = products.load_products(reg)
    assert product["is_live"] is True and product["has_link"] is True
    assert product["link_url"] == "https://example.com/buy?ref=fleet-store"


def test_committed_registry_is_honest():
    """The committed registry loads all four products; exactly one is live
    (SWTK, with its Gumroad URL), the coming-soon three carry no URL and an
    honest status note, and every entry cites its venture-lab source."""
    got = products.load_products()
    assert [p["slug"] for p in got] == [
        "stripe-webhook-test-kit",
        "membership-site-boilerplate-kit",
        "agent-workflow-template-pack",
        "agent-fleet-field-manual",
    ]
    live = [p for p in got if p["availability"] == "live"]
    assert len(live) == 1
    (swtk,) = live
    assert swtk["slug"] == "stripe-webhook-test-kit"
    assert swtk["url"] == SWTK_URL
    assert swtk["is_live"] is True and swtk["has_link"] is True
    assert swtk["link_url"] == f"{SWTK_URL}?ref=fleet-store"
    for p in got:
        assert p["source"].strip()
        assert "venture-lab" in p["source"]
        if p["availability"] == "live":
            assert p["url"]
        else:
            assert p["availability"] == "coming-soon"
            assert p["url"] is None
            assert p["has_link"] is False
            assert p["status_note"]  # every coming-soon product explains itself
