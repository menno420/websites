"""Webhook payload analyzer page tests — network-free (site feed primed from
a fixture, analyzer knowledge base read from the committed JSON on disk or
from tmp files). The page's whole point is the privacy property: GET-only,
no POST route, and an analyzer JS with zero network primitives — those are
asserted structurally here, not just claimed in copy."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from botsite import app as app_module
from botsite import data_source as ds
from botsite import webhook_analyzer

# Minimal site.json fixture so _base_ctx/lifespan never touch the network.
FIXTURE = {
    "meta": {"build": {"commit": "abcdef1234", "subject": "test build", "committed_at": "2026-07-09T00:00:00Z"}},
    "counts": {"commands": 0, "features": 0, "games": 0},
    "catalogue": [],
    "commands": [],
    "bot_changelog": [],
}

VENTURE_LAB_SHA = "0679327a463c063dcd9fc62b33ffb9a3789fa7d3"


@pytest.fixture()
def client():
    ds.clear_cache()
    ds.prime_cache(FIXTURE)
    ds.set_client(ds.make_client())  # never actually hit (cache is warm)
    with TestClient(app_module.app) as c:
        yield c
    ds.clear_cache()


def _config_from(page_text: str) -> dict:
    raw = page_text.split('id="webhook-analyzer-config">')[1].split("</script>")[0]
    return json.loads(raw)


def test_page_renders_with_tool_ui(client):
    r = client.get("/webhook-analyzer")
    assert r.status_code == 200
    assert "Webhook Payload Analyzer" in r.text
    assert 'id="wa-input"' in r.text  # the textarea
    assert 'id="wa-analyze"' in r.text  # Analyze button
    assert 'id="wa-sample"' in r.text  # Load-sample button
    assert 'id="wa-results"' in r.text  # results region (empty until analysis)
    # the buttons are plain buttons — the page ships NO <form> for the tool
    assert "<form" not in r.text


def test_lede_states_what_it_is_and_the_privacy_property(client):
    """Clarity + privacy: a first-time visitor learns what the tool does AND
    that the payload never leaves the tab — stated in the hero lede."""
    r = client.get("/webhook-analyzer")
    assert r.status_code == 200
    assert "All analysis runs\n      in your browser" in r.text or "All analysis runs" in r.text
    assert "GET-only" in r.text
    assert "makes no network calls" in r.text
    assert "your payload never leaves the tab" in r.text


def test_privacy_note_sits_next_to_the_textarea(client):
    r = client.get("/webhook-analyzer")
    assert r.status_code == 200
    assert 'id="wa-privacy-note"' in r.text
    assert "nothing you paste here is sent anywhere" in r.text
    assert "no POST route" in r.text


def test_nav_includes_webhook_analyzer(client):
    r = client.get("/")
    assert 'href="/webhook-analyzer"' in r.text
    assert "Webhook Analyzer" in r.text


def test_cross_links_present(client):
    """The Stripe guidance's source page and the kit that does what this
    page by design cannot (fire signed events at a real handler)."""
    r = client.get("/webhook-analyzer")
    assert r.status_code == 200
    assert 'href="/stripe-gotchas"' in r.text
    assert 'href="/products"' in r.text
    assert "Stripe Webhook Test Kit ($29)" in r.text


def test_no_post_handler_for_the_path(client):
    """ZERO server involvement with pasted data — a POST must fall through
    to 405, and no POST route is registered for the path."""
    assert client.post("/webhook-analyzer").status_code == 405
    from fastapi.routing import APIRoute

    methods = {
        m
        for route in app_module.app.routes
        if isinstance(route, APIRoute) and route.path == "/webhook-analyzer"
        for m in (route.methods or set())
    }
    assert "POST" not in methods
    assert "GET" in methods


def test_config_script_tag_is_valid_json_with_no_breakout(client):
    r = client.get("/webhook-analyzer")
    assert r.status_code == 200
    raw = r.text.split('id="webhook-analyzer-config">')[1].split("</script>")[0]
    assert "</script" not in raw  # "<" is escaped against script breakout
    cfg = json.loads(raw)
    assert [p["id"] for p in cfg["providers"]] == ["stripe", "github", "discord"]
    assert cfg["generic"]["heuristics"]


def test_analyzer_js_served_with_zero_network_primitives(client):
    """The privacy claim is structural: the served analyzer script contains
    no network primitive and no markup-injection sink at all."""
    r = client.get("/webhook-analyzer")
    assert '<script src="/static/webhook_analyzer.js"></script>' in r.text
    js = client.get("/static/webhook_analyzer.js")
    assert js.status_code == 200
    assert "webhook-analyzer-config" in js.text  # reads the single-sourced config
    for forbidden in ("fetch(", "XMLHttpRequest", "sendBeacon", "WebSocket", "innerHTML"):
        assert forbidden not in js.text, f"analyzer JS must not contain {forbidden!r}"
    assert "textContent" in js.text  # renders via textContent only


def test_page_shows_provenance_and_grounding(client):
    """Every guidance source renders, the SWTK line pinned to the full
    venture-lab sha, the GitHub docs lines with their fetch date, and the
    Discord signature line honestly marked not-verified."""
    r = client.get("/webhook-analyzer")
    assert r.status_code == 200
    assert VENTURE_LAB_SHA in r.text
    assert "SWTK material via botsite/data/stripe_gotchas.json" in r.text
    assert "docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries" in r.text
    assert "not verified from source this session" in r.text


def test_signature_headers_ride_headers_not_body_reminder(client):
    r = client.get("/webhook-analyzer")
    assert r.status_code == 200
    assert "not the JSON body" in r.text
    assert "a pasted payload alone can never be signature-verified" in r.text.lower()


def test_sample_is_declared_synthetic(client):
    r = client.get("/webhook-analyzer")
    assert r.status_code == 200
    assert "SYNTHETIC" in r.text
    js = client.get("/static/webhook_analyzer.js")
    assert "evt_TESTsample" in js.text
    assert '"customer_email": null' in js.text  # the gotcha demo is baked in


def test_degrades_on_missing_file(client, monkeypatch, tmp_path):
    monkeypatch.setattr(webhook_analyzer, "ANALYZER_JSON_PATH", tmp_path / "does-not-exist.json")
    r = client.get("/webhook-analyzer")
    assert r.status_code == 200
    assert "Analyzer unavailable right now" in r.text
    assert "Nothing is faked" in r.text
    assert 'id="webhook-analyzer-config"' not in r.text


def test_degrades_on_corrupt_file(client, monkeypatch, tmp_path):
    corrupt = tmp_path / "webhook_analyzer.json"
    corrupt.write_text("{ this is not json", encoding="utf-8")
    monkeypatch.setattr(webhook_analyzer, "ANALYZER_JSON_PATH", corrupt)
    r = client.get("/webhook-analyzer")
    assert r.status_code == 200
    assert "Analyzer unavailable right now" in r.text


def test_loader_returns_none_without_a_valid_provider(tmp_path):
    src = tmp_path / "webhook_analyzer.json"
    src.write_text(json.dumps({"providers": [], "generic": {}}), encoding="utf-8")
    assert webhook_analyzer.load_analyzer(src) is None
    src.write_text(json.dumps({"providers": "nope"}), encoding="utf-8")
    assert webhook_analyzer.load_analyzer(src) is None
    assert webhook_analyzer.load_analyzer(tmp_path / "missing.json") is None


def test_loader_skips_invalid_entries(tmp_path):
    """Providers missing required fields are skipped, not fatal; unknown
    strong-marker ids are dropped; invalid sources/notes are skipped."""
    src = tmp_path / "webhook_analyzer.json"
    src.write_text(json.dumps({
        "provenance": {
            "note": "n",
            "sources": [
                {"id": "ok", "label": "OK source", "verified": True},
                {"id": "no-verified-flag", "label": "Bad"},
                "not even a dict",
            ],
        },
        "providers": [
            {"id": "ok", "name": "OK",
             "markers": [{"id": "m1", "label": "marker one"}],
             "strong_markers": ["m1", "ghost-marker"],
             "signature": {"header": "X-Test",
                           "lines": [{"text": "t", "source": "ok"}]},
             "field_notes": [{"id": "n1", "text": "t", "source": "ok"},
                             {"id": "no-source", "text": "t"}]},
            {"id": "no-markers", "name": "Bad", "markers": [],
             "signature": {"lines": [{"text": "t", "source": "ok"}]}},
            {"id": "no-signature-lines", "name": "Bad",
             "markers": [{"id": "m", "label": "l"}],
             "signature": {"lines": []}},
            "not even a dict",
        ],
    }), encoding="utf-8")
    got = webhook_analyzer.load_analyzer(src)
    assert got is not None
    assert [p["id"] for p in got["providers"]] == ["ok"]
    assert got["providers"][0]["strong_markers"] == ["m1"]
    assert [n["id"] for n in got["providers"][0]["field_notes"]] == ["n1"]
    assert [s["id"] for s in got["provenance"]["sources"]] == ["ok"]


def test_committed_data_is_grounded():
    """The committed knowledge base carries exactly the three providers,
    every guidance line cited: Stripe to the SWTK material, GitHub to the
    docs fetched 2026-07-13, and Discord's signature line to the honestly
    UNVERIFIED docs pointer."""
    got = webhook_analyzer.load_analyzer()
    assert got is not None
    assert [p["id"] for p in got["providers"]] == ["stripe", "github", "discord"]
    sources = {s["id"]: s for s in got["provenance"]["sources"]}
    stripe, github, discord = got["providers"]
    assert {ln["source"] for ln in stripe["signature"]["lines"]} == {"swtk"}
    assert VENTURE_LAB_SHA in sources["swtk"]["detail"]
    assert {ln["source"] for ln in github["signature"]["lines"]} == {"github-validating"}
    assert sources["github-validating"]["verified"] is True
    assert sources["github-validating"]["fetched"] == "2026-07-13"
    assert sources["github-validating"]["url"].startswith("https://docs.github.com/")
    assert {ln["source"] for ln in discord["signature"]["lines"]} == {"discord-signature-unverified"}
    assert sources["discord-signature-unverified"]["verified"] is False
    assert stripe["signature"]["header"] == "Stripe-Signature"
    assert github["signature"]["header"] == "X-Hub-Signature-256"
    assert discord["signature"]["header"] is None  # not verified → no header claim
    assert "evt_" in stripe["id_prefixes"] and "cs_" in stripe["id_prefixes"]
    assert any(n["id"] == "customer-email-null" for n in stripe["field_notes"])


def test_config_resolves_source_labels_and_verified_flags():
    """The serialized client config carries the resolved source label +
    verified flag on every guidance line — the JS never re-declares one."""
    got = webhook_analyzer.load_analyzer()
    cfg = json.loads(webhook_analyzer.analyzer_config(got))
    stripe = cfg["providers"][0]
    assert all("SWTK material via botsite/data/stripe_gotchas.json" in ln["source_label"]
               for ln in stripe["signature"]["lines"])
    assert all(ln["verified"] is True for ln in stripe["signature"]["lines"])
    discord = cfg["providers"][2]
    assert discord["signature"]["lines"][0]["verified"] is False
    assert cfg["generic"]["header_reminder"]


def test_analyzer_config_escapes_script_breakout():
    """The config is rendered raw inside a script tag — a literal "<" in
    the data must never terminate it."""
    cfg = webhook_analyzer.analyzer_config({
        "providers": [{
            "id": "x", "name": "</script><b>",
            "markers": [{"id": "m", "label": "l"}],
            "strong_markers": [], "id_prefixes": {},
            "signature": {"header": None,
                          "lines": [{"text": "</script>", "source": "s"}]},
            "field_notes": [],
        }],
        "generic": {"header_reminder": None, "heuristics": [], "limits": None},
        "provenance": None,
    })
    assert "</script" not in cfg
    assert json.loads(cfg)["providers"][0]["name"] == "</script><b>"


def test_heuristics_and_caps_render_on_the_page(client):
    """The generic heuristics section is the same single-sourced copy the
    JS runs on — including the honest unknown rule and the walk caps."""
    r = client.get("/webhook-analyzer")
    assert r.status_code == 200
    assert "possible snowflake id (unverified)" in r.text
    assert "epoch timestamp (inferred)" in r.text
    assert "no classification is invented" in r.text
    assert "6 levels deep and 500 fields" in r.text
