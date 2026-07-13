"""SWTK gotchas companion page tests — network-free (site feed primed from a
fixture, gotchas data read from the committed JSON on disk or from tmp files)."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from botsite import app as app_module
from botsite import data_source as ds
from botsite import stripe_gotchas

# Minimal site.json fixture so _base_ctx/lifespan never touch the network.
FIXTURE = {
    "meta": {"build": {"commit": "abcdef1234", "subject": "test build", "committed_at": "2026-07-09T00:00:00Z"}},
    "counts": {"commands": 0, "features": 0, "games": 0},
    "catalogue": [],
    "commands": [],
    "bot_changelog": [],
}

# The kit's Gumroad URL (live since 2026-07-12) — per the committed registry.
SWTK_URL = "https://mennomagic01.gumroad.com/l/stripe-webhook-test-kit"

VENTURE_LAB_SHA = "0679327a463c063dcd9fc62b33ffb9a3789fa7d3"

ALL_TITLES = (
    "customer_email is null on checkout.session.completed",
    "success_url only expands {CHECKOUT_SESSION_ID}",
    "Verify the Stripe-Signature header",
    "Enforce the 300-second timestamp tolerance",
    "Sign/verify over the RAW request bytes",
    "Return 2xx fast, and process idempotently",
)


@pytest.fixture()
def client():
    ds.clear_cache()
    ds.prime_cache(FIXTURE)
    ds.set_client(ds.make_client())  # never actually hit (cache is warm)
    with TestClient(app_module.app) as c:
        yield c
    ds.clear_cache()


def test_page_renders_all_six_gotchas(client):
    r = client.get("/stripe-gotchas")
    assert r.status_code == 200
    assert "Stripe Webhook Gotchas" in r.text
    for title in ALL_TITLES:
        assert title in r.text
    # symptom → fix shape renders for every gotcha
    assert r.text.count("Symptom:") == 6
    assert r.text.count("Fix:") == 6


def test_lede_states_what_the_page_is(client):
    """Clarity: a first-time visitor learns this is the free companion
    checklist to the Stripe Webhook Test Kit, sourced from the kit's own
    material — no hype."""
    r = client.get("/stripe-gotchas")
    assert r.status_code == 200
    assert "free companion checklist" in r.text
    assert "Stripe Webhook Test Kit" in r.text
    assert "kit's own material" in r.text


def test_buy_cta_carries_exact_ref_link(client):
    """The live kit renders exactly one Gumroad buy link with attribution."""
    r = client.get("/stripe-gotchas")
    assert r.status_code == 200
    assert f'href="{SWTK_URL}?ref=fleet-store"' in r.text
    assert r.text.count("gumroad.com") == 1
    assert "$29 one-time" in r.text


def test_cta_is_honest_about_the_kit(client):
    """The CTA states the kit's four checks and its own honest limits."""
    r = client.get("/stripe-gotchas")
    assert r.status_code == 200
    for check in ("fire", "fire --forge", "check-email", "lint-url"):
        assert check in r.text
    assert "Honest limits:" in r.text
    assert "not a substitute for stripe listen" in r.text


def test_cross_links_present(client):
    r = client.get("/stripe-gotchas")
    assert r.status_code == 200
    assert 'href="/products"' in r.text
    assert 'href="/field-manual"' in r.text
    assert 'href="/agent-pr-check"' in r.text


def test_page_shows_provenance(client):
    r = client.get("/stripe-gotchas")
    assert r.status_code == 200
    assert VENTURE_LAB_SHA in r.text
    assert "candidates/stripe-webhook-test-kit/GOTCHAS.md" in r.text


def test_nav_includes_stripe_gotchas(client):
    r = client.get("/")
    assert 'href="/stripe-gotchas"' in r.text
    assert "Stripe Gotchas" in r.text


def test_degrades_on_missing_file(client, monkeypatch, tmp_path):
    monkeypatch.setattr(stripe_gotchas, "GOTCHAS_JSON_PATH", tmp_path / "does-not-exist.json")
    r = client.get("/stripe-gotchas")
    assert r.status_code == 200
    assert "Gotchas unavailable right now" in r.text
    assert "Nothing is faked" in r.text


def test_degrades_on_corrupt_file(client, monkeypatch, tmp_path):
    corrupt = tmp_path / "stripe_gotchas.json"
    corrupt.write_text("{ this is not json", encoding="utf-8")
    monkeypatch.setattr(stripe_gotchas, "GOTCHAS_JSON_PATH", corrupt)
    r = client.get("/stripe-gotchas")
    assert r.status_code == 200
    assert "Gotchas unavailable right now" in r.text


def test_loader_skips_invalid_entries(tmp_path):
    """Gotchas missing required fields are skipped, not fatal; optional
    fields normalize to None."""
    src = tmp_path / "stripe_gotchas.json"
    src.write_text(json.dumps({
        "gotchas": [
            {"id": "ok", "title": "OK", "symptom": "s", "fix": "f"},
            {"id": "no-fix", "title": "Bad", "symptom": "s"},
            {"title": "no-id", "symptom": "s", "fix": "f"},
            "not even a dict",
        ],
    }), encoding="utf-8")
    got = stripe_gotchas.load_gotchas(src)
    assert [g["id"] for g in got["gotchas"]] == ["ok"]
    assert got["gotchas"][0]["why"] is None
    assert got["gotchas"][0]["code"] is None
    assert got["provenance"] is None


def test_loader_degrades_to_empty(tmp_path):
    got = stripe_gotchas.load_gotchas(tmp_path / "missing.json")
    assert got == {"gotchas": [], "provenance": None, "framing": None,
                   "kit_checks": [], "kit_limits": []}


def test_committed_data_is_honest():
    """The committed data file carries exactly six valid gotchas and full
    provenance pinned to the venture-lab source sha."""
    got = stripe_gotchas.load_gotchas()
    assert len(got["gotchas"]) == 6
    assert [g["title"] for g in got["gotchas"]] == list(ALL_TITLES)
    prov = got["provenance"]
    assert prov is not None
    assert prov["repo"] == "menno420/venture-lab"
    assert prov["commit"] == VENTURE_LAB_SHA
    assert prov["retrieved"] == "2026-07-13"
    assert "candidates/stripe-webhook-test-kit/GOTCHAS.md" in prov["paths"]
    assert got["kit_checks"] and len(got["kit_checks"]) == 4
    assert got["kit_limits"]


def test_swtk_product_comes_from_registry():
    """The CTA's product facts come from the committed product registry —
    live, with the attribution link already applied by that loader."""
    swtk = stripe_gotchas.swtk_product()
    assert swtk is not None
    assert swtk["name"] == "Stripe Webhook Test Kit v0.1"
    assert swtk["price"] == "$29 one-time"
    assert swtk["is_live"] is True and swtk["has_link"] is True
    assert swtk["link_url"] == f"{SWTK_URL}?ref=fleet-store"
