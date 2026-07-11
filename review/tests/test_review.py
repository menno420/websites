"""Review-site tests. Network-free by construction — the service's only data
source is the committed ``data/snapshot.json``; tests exercise the real file
plus synthetic good/missing/corrupt snapshots for the degradation paths."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from markupsafe import escape

from review import story
from review.app import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Probes
# ---------------------------------------------------------------------------
def test_healthz():
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "service": "review"}


def test_version_returns_env_sha(monkeypatch):
    monkeypatch.setenv("RAILWAY_GIT_COMMIT_SHA", "deadbeef1234567890")
    body = client.get("/version").json()
    assert body == {"service": "review", "sha": "deadbeef1234567890", "short": "deadbeef"}


def test_version_falls_back_to_git_sha(monkeypatch):
    monkeypatch.delenv("RAILWAY_GIT_COMMIT_SHA", raising=False)
    monkeypatch.setenv("GIT_SHA", "cafebabecafebabe")
    body = client.get("/version").json()
    assert body["sha"] == "cafebabecafebabe" and body["short"] == "cafebabe"


def test_version_unknown_when_unset(monkeypatch):
    monkeypatch.delenv("RAILWAY_GIT_COMMIT_SHA", raising=False)
    monkeypatch.delenv("GIT_SHA", raising=False)
    body = client.get("/version").json()
    assert body == {"service": "review", "sha": "unknown", "short": "unknown"}


# ---------------------------------------------------------------------------
# Pages render from the real committed snapshot
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("path", ["/", "/process", "/growth", "/successes", "/problems"])
def test_pages_render(path):
    r = client.get(path)
    assert r.status_code == 200
    assert "Program Review" in r.text


def test_overview_shows_real_totals():
    snap = story.load_snapshot()
    assert snap["ok"], f"committed snapshot must load: {snap['error']}"
    totals = snap["data"]["totals"]
    r = client.get("/")
    assert "{:,}".format(totals["prs_merged"]) in r.text
    assert "{:,}".format(totals["session_cards"]) in r.text
    # audience + honesty framing present
    assert "Anthropic" in r.text
    assert "/story.json" in r.text


def test_growth_charts_render_real_svg():
    r = client.get("/growth")
    assert "<svg" in r.text
    assert "Pull requests merged per day" in r.text
    assert "Agent session cards per day" in r.text
    assert "Test functions at end of day" in r.text
    # the table view (accessibility fallback for the charts) is present
    assert "The same numbers, as a table" in r.text
    # real day rows from the committed snapshot show through
    snap = story.load_snapshot()
    for day in snap["data"]["days"]:
        assert day["date"] in r.text


def test_process_explains_the_workflow():
    r = client.get("/process")
    assert "control/inbox.md" in r.text
    assert "control/status.md" in r.text
    assert "born-red" in r.text.lower()
    assert "Glossary" in r.text
    # the landing path renders every step
    for title, _ in story.LANDING_PATH:
        assert title in r.text


def test_problems_page_is_honest_and_evidence_linked():
    r = client.get("/problems")
    # leads with real failures, not marketing
    assert "What went wrong" in r.text
    assert "PR #19" in r.text or "empty PR" in r.text
    # every problem carries at least one evidence link
    for item in story.PROBLEMS:
        assert item["evidence"], f"problem without evidence: {item['title']}"
        assert str(escape(item["title"])) in r.text
    assert "github.com/menno420/websites" in r.text


def test_successes_page_evidence_linked():
    r = client.get("/successes")
    for item in story.SUCCESSES:
        assert item["evidence"], f"success without evidence: {item['title']}"
        assert str(escape(item["title"])) in r.text


def test_story_json_serves_snapshot():
    r = client.get("/story.json")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["snapshot"]["totals"]["services"] == 4


def test_unknown_page_404():
    r = client.get("/nope")
    assert r.status_code == 404
    assert "not found" in r.text.lower()


# ---------------------------------------------------------------------------
# Snapshot loading — honest degradation
# ---------------------------------------------------------------------------
def test_load_snapshot_missing_file(tmp_path: Path):
    res = story.load_snapshot(tmp_path / "nope.json")
    assert res["ok"] is False
    assert "missing" in res["error"]
    assert res["data"] == {}


def test_load_snapshot_corrupt_file(tmp_path: Path):
    p = tmp_path / "bad.json"
    p.write_text("{not json", encoding="utf-8")
    res = story.load_snapshot(p)
    assert res["ok"] is False
    assert "unreadable" in res["error"]


def test_load_snapshot_malformed_shape(tmp_path: Path):
    p = tmp_path / "shape.json"
    p.write_text(json.dumps({"hello": 1}), encoding="utf-8")
    res = story.load_snapshot(p)
    assert res["ok"] is False
    assert "malformed" in res["error"]


def test_pages_degrade_honestly_when_snapshot_missing(monkeypatch, tmp_path: Path):
    """No fake numbers: with the snapshot gone, pages still 200 with a banner."""
    monkeypatch.setattr(story, "SNAPSHOT_PATH", tmp_path / "gone.json")
    for path in ["/", "/growth", "/process", "/successes", "/problems"]:
        r = client.get(path)
        assert r.status_code == 200
        assert "Data snapshot unavailable" in r.text
    # and the machine view says so too
    body = client.get("/story.json").json()
    assert body["ok"] is False and body["snapshot"] == {}


# ---------------------------------------------------------------------------
# Chart geometry — pure-function units
# ---------------------------------------------------------------------------
def test_column_chart_empty():
    assert story.column_chart([])["empty"] is True


def test_column_chart_geometry():
    chart = story.column_chart([("07-09", 10), ("07-10", 5), ("07-11", 0)], height=180)
    assert chart["empty"] is False
    cols = chart["columns"]
    assert [c["value"] for c in cols] == [10, 5, 0]
    # tallest bar spans the full plot height; half value = half height
    assert cols[0]["h"] == 180 - 26 - 24
    assert cols[1]["h"] == round(cols[0]["h"] / 2)
    # zero stays zero (no invented mark), anchored at the baseline
    assert cols[2]["h"] == 0
    for c in cols:
        assert c["y"] + c["h"] == c["baseline"]
    # mark-spec cap: columns are 24px thick
    assert all(c["w"] == 24 for c in cols)


def test_column_chart_all_zero_never_divides_by_zero():
    chart = story.column_chart([("a", 0), ("b", 0)])
    assert all(c["h"] == 0 for c in chart["columns"])


def test_growth_charts_from_snapshot_shape():
    charts = story.growth_charts(
        {"days": [{"date": "2026-07-09", "prs_merged": 3, "session_cards": 2, "test_functions_eod": 7}]}
    )
    assert [c["id"] for c in charts] == ["prs", "sessions", "tests"]
    assert charts[0]["chart"]["columns"][0]["value"] == 3
    assert charts[1]["chart"]["columns"][0]["value"] == 2
    assert charts[2]["chart"]["columns"][0]["value"] == 7


def test_growth_charts_empty_days():
    charts = story.growth_charts({"days": []})
    assert all(c["chart"]["empty"] for c in charts)


# ---------------------------------------------------------------------------
# Content integrity — the honesty rules, pinned
# ---------------------------------------------------------------------------
def test_every_narrative_item_has_title_and_evidence():
    for item in story.PROBLEMS + story.SUCCESSES:
        assert item["title"].strip()
        assert item["what"].strip()
        for label, url in item["evidence"]:
            assert label.strip()
            assert url.startswith("https://github.com/menno420/")


def test_overview_stats_honest_absence():
    """A total missing from the snapshot yields NO tile — never a guessed one."""
    tiles = story.overview_stats({"totals": {"prs_merged": 5}})
    assert [t["key"] for t in tiles] == ["prs_merged"]
    assert story.overview_stats({}) == []


def test_committed_snapshot_is_current_shape():
    """The committed data file matches what the pages expect."""
    snap = story.load_snapshot()
    assert snap["ok"] is True
    data = snap["data"]
    assert data["git_head"]
    assert data["generated_at"].endswith("Z")
    for day in data["days"]:
        assert set(day) >= {"date", "prs_merged", "commits", "session_cards"}
    assert data["totals"]["services"] == 4
