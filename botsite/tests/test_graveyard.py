"""Strategy Graveyard page tests — network-free (site feed primed from a
fixture; graveyard data read from the committed JSON on disk or tmp files;
the gen script's transform fed fixture records, never the network)."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from botsite import app as app_module
from botsite import data_source as ds
from botsite import gen_graveyard, graveyard

# Minimal site.json fixture so _base_ctx/lifespan never touch the network.
FIXTURE = {
    "meta": {"build": {"commit": "abcdef1234", "subject": "test build", "committed_at": "2026-07-09T00:00:00Z"}},
    "counts": {"commands": 0, "features": 0, "games": 0},
    "catalogue": [],
    "commands": [],
    "bot_changelog": [],
}

# A valid ledger record for transform tests, tweaked per test.
RECORD_BASE = {
    "run_id": "20260709T000000000000Z-abc",
    "file": "runs/x.json",
    "strategy": "sma_crossover",
    "instrument": "AAPL",
    "timeframe": "daily",
    "params": {"fast": 20, "slow": 50},
    "sharpe": 0.5,
    "benchmark_sharpe": 0.9,
    "cagr": 0.1,
    "max_drawdown": -0.3,
    "data_start": "2010-01-04 00:00:00",
    "data_end": "2025-01-08 00:00:00",
    "variants_tried": 12,
}


def _rec(**over):
    return {**RECORD_BASE, **over}


@pytest.fixture()
def client():
    ds.clear_cache()
    ds.prime_cache(FIXTURE)
    ds.set_client(ds.make_client())  # never actually hit (cache is warm)
    with TestClient(app_module.app) as c:
        yield c
    ds.clear_cache()


# --------------------------------------------------------------------------- #
# The page, against the committed bake
# --------------------------------------------------------------------------- #
def test_page_renders_with_headline_and_lede(client):
    """Clarity: 200, hero h1, and a plain-words sb-lead purpose lede."""
    r = client.get("/graveyard")
    assert r.status_code == 200
    assert "<h1>Strategy Graveyard</h1>" in r.text
    assert 'class="sb-lead"' in r.text
    assert "nothing has been promoted" in r.text
    assert "Research only" in r.text


def test_headline_reflects_the_baked_aggregates(client):
    """The banner numbers are the committed bake's numbers, never hardcoded
    copy that could drift from the data."""
    doc = graveyard.load_graveyard()
    assert doc["available"] is True
    agg = doc["aggregate"]
    r = client.get("/graveyard")
    assert r.status_code == 200
    banner = (
        f"{agg['config_evals']:,} CONFIGURATIONS TESTED ACROSS "
        f"{agg['runs']:,} RECORDED RUNS · "
        f"{agg['verdicts']['promoted']} PROMOTED"
    )
    assert banner in r.text
    assert f"{agg['verdicts']['keep']:,}" in r.text
    assert f"{agg['verdicts']['kill']:,}" in r.text
    assert str(agg["best_sharpe"]) in r.text
    assert str(agg["median_sharpe"]) in r.text


def test_zero_promoted_presented_plainly(client):
    """The load-bearing zero: promoted is 0 in the bake AND said plainly on
    the page — never spun, never hidden."""
    doc = graveyard.load_graveyard()
    assert doc["aggregate"]["verdicts"]["promoted"] == 0
    r = client.get("/graveyard")
    assert "0 PROMOTED" in r.text
    assert "Zero. Not one configuration earned an out-of-sample promotion" in r.text
    assert "holdout is spent" in r.text


def test_leaderboard_and_top_tables_render(client):
    doc = graveyard.load_graveyard()
    r = client.get("/graveyard")
    assert r.status_code == 200
    # Every strategy family appears in the leaderboard table.
    for row in doc["strategies"]:
        assert row["strategy"] in r.text
    # The best survivor and the best of the dead both render.
    assert "Best of the survivors" in r.text
    assert "Best of the dead" in r.text
    top_keep = doc["top"]["keep"][0]
    assert f"{top_keep['sharpe']:.3f}" in r.text


def test_provenance_and_verdict_rule_visible(client):
    doc = graveyard.load_graveyard()
    r = client.get("/graveyard")
    assert doc["as_of"] in r.text
    assert "derived at bake time" in r.text
    assert "experiments/index.jsonl" in r.text
    if doc["source_sha"]:
        assert doc["source_sha"][:8] in r.text
    else:
        assert "source HEAD sha unavailable at bake time" in r.text


def test_page_is_get_only_with_no_forms(client):
    r = client.get("/graveyard")
    assert "<form" not in r.text.lower()
    assert client.post("/graveyard").status_code == 405


def test_nav_includes_graveyard(client):
    r = client.get("/")
    assert 'href="/graveyard"' in r.text
    assert "Graveyard" in r.text


def test_page_degrades_on_missing_file(client, monkeypatch, tmp_path):
    monkeypatch.setattr(graveyard, "GRAVEYARD_JSON_PATH", tmp_path / "does-not-exist.json")
    r = client.get("/graveyard")
    assert r.status_code == 200
    assert "No graveyard data" in r.text
    assert "is missing" in r.text
    assert "Nothing is faked here" in r.text


def test_page_degrades_on_corrupt_file(client, monkeypatch, tmp_path):
    corrupt = tmp_path / "graveyard.json"
    corrupt.write_text("{ this is not json", encoding="utf-8")
    monkeypatch.setattr(graveyard, "GRAVEYARD_JSON_PATH", corrupt)
    r = client.get("/graveyard")
    assert r.status_code == 200
    assert "No graveyard data" in r.text
    assert "not valid JSON" in r.text


# --------------------------------------------------------------------------- #
# The loader
# --------------------------------------------------------------------------- #
def test_loader_missing_file_reason(tmp_path):
    got = graveyard.load_graveyard(tmp_path / "nope.json")
    assert got["available"] is False
    assert "missing" in got["reason"]


def test_loader_corrupt_and_misshapen_files(tmp_path):
    bad = tmp_path / "graveyard.json"
    bad.write_text("[not json", encoding="utf-8")
    assert graveyard.load_graveyard(bad)["available"] is False
    # Valid JSON of the wrong shape degrades with the section named.
    bad.write_text("[1, 2, 3]", encoding="utf-8")
    assert "not a JSON object" in graveyard.load_graveyard(bad)["reason"]
    bad.write_text(json.dumps({"as_of": "x"}), encoding="utf-8")
    assert "missing its" in graveyard.load_graveyard(bad)["reason"]
    doc = gen_graveyard.compute_graveyard([_rec()], as_of="2026-07-13T00:00:00Z", source_sha=None)
    doc["aggregate"]["verdicts"]["keep"] = "many"  # not an int
    bad.write_text(json.dumps(doc), encoding="utf-8")
    assert "verdicts" in graveyard.load_graveyard(bad)["reason"]


def test_committed_graveyard_json_parses_with_expected_shape():
    """The committed bake: parses, verdict counts internally consistent,
    promoted exactly 0, top tables capped, every strategy row consistent."""
    doc = graveyard.load_graveyard()
    assert doc["available"] is True
    agg = doc["aggregate"]
    v = agg["verdicts"]
    assert v["promoted"] == 0
    assert v["keep"] + v["kill"] == agg["runs"] > 0
    assert agg["config_evals"] >= agg["runs"]
    assert len(doc["top"]["keep"]) <= gen_graveyard.TOP_N
    assert len(doc["top"]["kill"]) <= gen_graveyard.TOP_N
    assert doc["strategies"], "no per-strategy rows in the committed bake"
    assert sum(s["runs"] for s in doc["strategies"]) == agg["runs"]
    assert sum(s["keep"] for s in doc["strategies"]) == v["keep"]
    assert sum(s["kill"] for s in doc["strategies"]) == v["kill"]
    assert sum(s["config_evals"] for s in doc["strategies"]) == agg["config_evals"]
    for entry in doc["top"]["keep"]:
        assert entry["sharpe"] > entry["benchmark_sharpe"]
    for entry in doc["top"]["kill"]:
        assert entry["sharpe"] <= entry["benchmark_sharpe"]
    assert doc["source_sha"] is None or len(doc["source_sha"]) == 40


def test_committed_graveyard_json_is_compact():
    """The committed file is the summary, never a copy of the raw ledger."""
    assert graveyard.GRAVEYARD_JSON_PATH.stat().st_size < 50_000


# --------------------------------------------------------------------------- #
# The bake script's pure transform (network-free)
# --------------------------------------------------------------------------- #
def test_parse_records_skips_malformed_lines():
    text = "\n".join([
        json.dumps(_rec()),
        "not json at all",
        json.dumps({"strategy": "x"}),          # missing required fields
        json.dumps({**_rec(), "sharpe": "high"}),  # non-numeric metric
        json.dumps({**_rec(), "variants_tried": -1}),
        "",
        json.dumps(_rec(run_id="r2", sharpe=1.2)),
    ])
    records, skipped = gen_graveyard.parse_records(text)
    assert len(records) == 2
    assert skipped == 4


def test_derive_verdict_is_the_documented_dev_rule():
    assert gen_graveyard.derive_verdict(_rec(sharpe=1.0, benchmark_sharpe=0.9)) == "keep"
    assert gen_graveyard.derive_verdict(_rec(sharpe=0.5, benchmark_sharpe=0.9)) == "kill"
    # buy-and-hold IS its own benchmark — equality never counts as a beat.
    assert gen_graveyard.derive_verdict(_rec(sharpe=0.9, benchmark_sharpe=0.9)) == "kill"


def test_compute_graveyard_aggregates_fixture_records():
    records = [
        _rec(run_id="a", strategy="alpha", sharpe=1.0, benchmark_sharpe=0.5,
             cagr=0.2, max_drawdown=-0.1, variants_tried=10),
        _rec(run_id="b", strategy="alpha", sharpe=0.2, benchmark_sharpe=0.5,
             cagr=0.05, max_drawdown=-0.4, variants_tried=5),
        _rec(run_id="c", strategy="beta", sharpe=-0.3, benchmark_sharpe=0.5,
             instrument="GLD", timeframe="hourly", variants_tried=1,
             holdout_unlocked=True),
    ]
    doc = gen_graveyard.compute_graveyard(
        records, as_of="2026-07-13T00:00:00Z", source_sha=None,
        source_sha_reason="walled", skipped=2,
    )
    agg = doc["aggregate"]
    assert agg["runs"] == 3
    assert agg["config_evals"] == 16
    assert agg["skipped_ledger_lines"] == 2
    assert agg["verdicts"] == {"promoted": 0, "keep": 1, "kill": 2}
    assert agg["strategies"] == 2
    assert agg["instruments"] == 2
    assert agg["timeframes"] == ["daily", "hourly"]
    assert agg["best_sharpe"] == 1.0
    assert agg["worst_sharpe"] == -0.3
    assert agg["holdout_unlocked_runs"] == 1
    assert doc["source_sha"] is None
    assert doc["source_sha_reason"] == "walled"
    # Strategy rows: alpha (1 keep) sorts before beta (0 keeps).
    assert [s["strategy"] for s in doc["strategies"]] == ["alpha", "beta"]
    alpha = doc["strategies"][0]
    assert alpha == {
        "strategy": "alpha", "runs": 2, "config_evals": 15,
        "keep": 1, "kill": 1, "best_sharpe": 1.0, "best_cagr": 0.2,
        "worst_max_drawdown": -0.4,
    }
    # Top tables: sorted by sharpe desc, verdict-pure.
    assert [e["sharpe"] for e in doc["top"]["kill"]] == [0.2, -0.3]
    assert [e["sharpe"] for e in doc["top"]["keep"]] == [1.0]


def test_compute_graveyard_caps_top_n():
    records = [
        _rec(run_id=f"r{i}", sharpe=1.0 + i / 100, benchmark_sharpe=0.1)
        for i in range(gen_graveyard.TOP_N + 5)
    ]
    doc = gen_graveyard.compute_graveyard(records, as_of="x", source_sha=None)
    assert len(doc["top"]["keep"]) == gen_graveyard.TOP_N
    # Highest sharpe first.
    sharpes = [e["sharpe"] for e in doc["top"]["keep"]]
    assert sharpes == sorted(sharpes, reverse=True)
