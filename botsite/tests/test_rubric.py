""""Should I build it?" rubric-scorer page tests — network-free (site feed
primed from a fixture, rubric data read from the committed JSON on disk or
from tmp files)."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from botsite import app as app_module
from botsite import data_source as ds
from botsite import rubric

# Minimal site.json fixture so _base_ctx/lifespan never touch the network.
FIXTURE = {
    "meta": {"build": {"commit": "abcdef1234", "subject": "test build", "committed_at": "2026-07-09T00:00:00Z"}},
    "counts": {"commands": 0, "features": 0, "games": 0},
    "catalogue": [],
    "commands": [],
    "bot_changelog": [],
}

VENTURE_LAB_SHA = "0679327a463c063dcd9fc62b33ffb9a3789fa7d3"

# The rubric's real five axes (venture-eval-001 names) and weights.
ALL_AXES = (
    ("Distribution", 0.35),
    ("Agent-buildability", 0.20),
    ("Owner-click cost", 0.15),
    ("Speed to first dollar", 0.15),
    ("WTP / moat", 0.15),
)

# The verdict bands verbatim from the shipped SCORING-RUBRIC.md.
ALL_BANDS = (
    ("below ~3.0", "do not build without a named exception in writing"),
    ("3.0–3.5", "borderline — only with a tight budget"),
    ("above 3.5", "best available candidate"),
)


@pytest.fixture()
def client():
    ds.clear_cache()
    ds.prime_cache(FIXTURE)
    ds.set_client(ds.make_client())  # never actually hit (cache is warm)
    with TestClient(app_module.app) as c:
        yield c
    ds.clear_cache()


def test_page_renders_all_five_axes(client):
    r = client.get("/should-i-build-it")
    assert r.status_code == 200
    assert "Should I build it?" in r.text
    for name, weight in ALL_AXES:
        assert name in r.text
        assert f"weight {round(weight * 100)}%" in r.text
    # every axis renders a 0–5 slider on the rubric's real half-step scale
    assert r.text.count('type="range"') == 5
    assert r.text.count('step="0.5"') == 5


def test_lede_states_what_the_page_is(client):
    """Clarity: a first-time visitor learns this is the fleet's real vetting
    rubric with its source file named — not a toy."""
    r = client.get("/should-i-build-it")
    assert r.status_code == 200
    assert "venture-eval-001" in r.text
    assert "docs/research/venture-eval-001.md" in r.text
    assert "real vetting rubric" in r.text
    assert "not a toy" in r.text


def test_verdict_bands_and_thresholds_in_served_page(client):
    """The rubric's own verdict rule — thresholds and category wording —
    reaches the browser, both as page prose and as the JS scorer's config."""
    r = client.get("/should-i-build-it")
    assert r.status_code == 200
    for range_text, label in ALL_BANDS:
        assert range_text in r.text
        assert label in r.text
    assert "still not a promise anyone will buy it" in r.text
    assert "no magic pass mark" in r.text
    cfg = json.loads(r.text.split('id="rubric-config">')[1].split("</script>")[0])
    assert [b["max"] for b in cfg["bands"]] == [3.0, 3.5, None]
    assert [b["id"] for b in cfg["bands"]] == ["do-not-build", "borderline", "best-available"]
    assert [round(a["weight"], 2) for a in cfg["axes"]] == [0.35, 0.20, 0.15, 0.15, 0.15]
    assert cfg["scale"] == {"min": 0.0, "max": 5.0, "step": 0.5}


def test_scorer_js_is_served_and_single_sourced(client):
    """The page loads the vanilla scorer, and the served asset reads the
    config (never re-declares a weight or threshold)."""
    r = client.get("/should-i-build-it")
    assert 'src="/static/rubric_scorer.js"' in r.text
    js = client.get("/static/rubric_scorer.js")
    assert js.status_code == 200
    assert "rubric-config" in js.text
    assert "innerHTML" not in js.text
    assert "0.35" not in js.text  # weights come from the config, not the JS


def test_catalog_cross_link_present(client):
    r = client.get("/should-i-build-it")
    assert r.status_code == 200
    assert 'href="/products/catalog"' in r.text
    assert 'href="/products"' in r.text


def test_no_post_handler_for_the_path(client):
    """The scorer is GET-only with zero server state — a POST must fall
    through to 405, and no POST route is registered for the path."""
    assert client.post("/should-i-build-it").status_code == 405
    from fastapi.routing import APIRoute

    methods = {
        m
        for route in app_module.app.routes
        if isinstance(route, APIRoute) and route.path == "/should-i-build-it"
        for m in (route.methods or set())
    }
    assert "POST" not in methods
    assert "GET" in methods


def test_page_shows_provenance(client):
    r = client.get("/should-i-build-it")
    assert r.status_code == 200
    assert VENTURE_LAB_SHA in r.text
    assert "candidates/kill-rule-intake-kit/pack/SCORING-RUBRIC.md" in r.text


def test_nav_includes_rubric_scorer(client):
    r = client.get("/")
    assert 'href="/should-i-build-it"' in r.text
    assert "Rubric Scorer" in r.text


def test_worked_example_and_anti_gaming_rules_render(client):
    r = client.get("/should-i-build-it")
    assert r.status_code == 200
    assert "0.35·3 + 0.20·5 + 0.15·4 + 0.15·3 + 0.15·3" in r.text
    assert "3.55" in r.text
    assert "Never tune weights to save a candidate (Kill Rule 4)." in r.text
    assert "Score distribution first" in r.text


def test_degrades_on_missing_file(client, monkeypatch, tmp_path):
    monkeypatch.setattr(rubric, "RUBRIC_JSON_PATH", tmp_path / "does-not-exist.json")
    r = client.get("/should-i-build-it")
    assert r.status_code == 200
    assert "Rubric unavailable right now" in r.text
    assert "Nothing is faked" in r.text


def test_degrades_on_corrupt_file(client, monkeypatch, tmp_path):
    corrupt = tmp_path / "rubric.json"
    corrupt.write_text("{ this is not json", encoding="utf-8")
    monkeypatch.setattr(rubric, "RUBRIC_JSON_PATH", corrupt)
    r = client.get("/should-i-build-it")
    assert r.status_code == 200
    assert "Rubric unavailable right now" in r.text


def test_loader_skips_invalid_entries(tmp_path):
    """Axes/bands missing required fields are skipped, not fatal; optional
    fields normalize; a broken scale falls back to the rubric default."""
    src = tmp_path / "rubric.json"
    src.write_text(json.dumps({
        "axes": [
            {"id": "ok", "name": "OK", "weight": 0.35, "measures": "m",
             "question": "q", "plain": "p",
             "anchors": [{"score": 5, "text": "t"}]},
            {"id": "no-anchors", "name": "Bad", "weight": 0.2, "measures": "m",
             "question": "q", "plain": "p", "anchors": []},
            {"id": "bad-weight", "name": "Bad", "weight": 2, "measures": "m",
             "question": "q", "plain": "p",
             "anchors": [{"score": 5, "text": "t"}]},
            "not even a dict",
        ],
        "bands": [
            {"id": "ok", "range": "below ~3.0", "label": "l", "max": 3.0},
            {"id": "no-label", "range": "3.0–3.5", "max": 3.5},
        ],
        "scale": {"min": 5, "max": 0, "step": 0.5},
    }), encoding="utf-8")
    got = rubric.load_rubric(src)
    assert [a["id"] for a in got["axes"]] == ["ok"]
    assert got["axes"][0]["kit_name"] is None
    assert [b["id"] for b in got["bands"]] == ["ok"]
    assert got["bands"][0]["caveat"] is None
    assert got["scale"] == {"min": 0.0, "max": 5.0, "step": 0.5}
    assert got["provenance"] is None


def test_loader_degrades_to_empty(tmp_path):
    got = rubric.load_rubric(tmp_path / "missing.json")
    assert got == {"axes": [], "bands": [],
                   "scale": {"min": 0.0, "max": 5.0, "step": 0.5},
                   "provenance": None, "framing": None, "reading_note": None,
                   "anti_gaming": [], "worked_example": None}


def test_committed_data_is_the_real_rubric():
    """The committed data file carries exactly the five venture-eval-001
    axes (weights summing to 1.00), the three shipped verdict bands, and
    full provenance pinned to the venture-lab source sha."""
    got = rubric.load_rubric()
    assert [(a["name"], a["weight"]) for a in got["axes"]] == list(ALL_AXES)
    assert abs(sum(a["weight"] for a in got["axes"]) - 1.0) < 1e-9
    for axis in got["axes"]:
        assert axis["anchors"], f"axis {axis['id']} ships no anchors"
    assert [(b["range"], b["label"]) for b in got["bands"]] == list(ALL_BANDS)
    assert [b["max"] for b in got["bands"]] == [3.0, 3.5, None]
    assert got["bands"][2]["caveat"] == "which is still not a promise anyone will buy it"
    prov = got["provenance"]
    assert prov is not None
    assert prov["repo"] == "menno420/venture-lab"
    assert prov["commit"] == VENTURE_LAB_SHA
    assert prov["retrieved"] == "2026-07-13"
    assert "docs/research/venture-eval-001.md" in prov["paths"]
    assert "candidates/kill-rule-intake-kit/pack/SCORING-RUBRIC.md" in prov["paths"]
    assert got["reading_note"] and "no magic pass mark" in got["reading_note"]
    assert len(got["anti_gaming"]) == 5
    example = got["worked_example"]
    assert example and example["total"] == 3.55


def test_scorer_config_escapes_script_breakout():
    """The config is rendered raw inside a script tag — a literal "<" in the
    data must never terminate it."""
    cfg = rubric.scorer_config({
        "axes": [{"id": "x", "name": "</script><b>", "weight": 0.35}],
        "scale": {"min": 0.0, "max": 5.0, "step": 0.5},
        "bands": [],
        "reading_note": None,
    })
    assert "</script" not in cfg
    assert json.loads(cfg)["axes"][0]["name"] == "</script><b>"
