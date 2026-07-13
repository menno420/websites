"""ORDER 019 PR2 filter tests for the review site's list surfaces — the
centralized listfilter core vendored from app/listfilter.py and applied to
/reviews (editions), /fleet (the lanes grid), and /questions (the ledger).

Covers, per surface: the no-param page renders exactly today's order
(default unchanged), dimension filters (single + combined), search, sorts,
honest unknown-value flagging, and the honest filtered-empty state. Plus the
vendored-copy byte-identity tests (the module needed zero edits, so identity
is asserted, not skipped).

Network-free; fixture files land in tmp paths (the test_fleet.py style)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from review import editions, fleetdata, story
from review.app import app

client = TestClient(app)

REPO_ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# vendored-copy byte identity — the sharing pattern's contract
# ---------------------------------------------------------------------------
def test_vendored_listfilter_module_is_byte_identical_to_app():
    ours = (REPO_ROOT / "review" / "listfilter.py").read_bytes()
    theirs = (REPO_ROOT / "app" / "listfilter.py").read_bytes()
    assert ours == theirs, (
        "review/listfilter.py must stay a byte-identical vendored copy of "
        "app/listfilter.py (like static/ds/ — update both together)"
    )


def test_vendored_listfilter_partial_is_byte_identical_to_app():
    ours = (REPO_ROOT / "review" / "templates" / "_listfilter.html").read_bytes()
    theirs = (REPO_ROOT / "app" / "templates" / "_listfilter.html").read_bytes()
    assert ours == theirs


# ---------------------------------------------------------------------------
# /reviews — month dim, title/summary search, newest/oldest/title sorts
# ---------------------------------------------------------------------------
_EDITION = """---
title: {title}
date: {date}
summary: {summary}
---
body
"""


@pytest.fixture()
def editions_dir(tmp_path, monkeypatch):
    d = tmp_path / "reviews"
    d.mkdir()
    (d / "2026-06-20-alpha.md").write_text(
        _EDITION.format(title="Edition A — the June retro",
                        date="2026-06-20", summary="june things"),
        encoding="utf-8")
    (d / "2026-07-05-beta.md").write_text(
        _EDITION.format(title="Edition B — payouts shipped",
                        date="2026-07-05", summary="testing program"),
        encoding="utf-8")
    (d / "2026-07-11-gamma.md").write_text(
        _EDITION.format(title="Edition C — filters landed",
                        date="2026-07-11", summary="list filters"),
        encoding="utf-8")
    monkeypatch.setattr(editions, "REVIEWS_DIR", d)
    return d


def _order(html: str, needles: list[str]) -> list[str]:
    found = [(html.index(n), n) for n in needles if n in html]
    return [n for _, n in sorted(found)]


TITLES = ["Edition A — the June retro", "Edition B — payouts shipped",
          "Edition C — filters landed"]


def test_reviews_no_params_renders_all_newest_first(editions_dir):
    r = client.get("/reviews")
    assert r.status_code == 200
    assert "3 of 3" in r.text
    assert _order(r.text, TITLES) == [TITLES[2], TITLES[1], TITLES[0]]


def test_reviews_month_filter_and_counts(editions_dir):
    r = client.get("/reviews?month=2026-07")
    assert "2 of 3" in r.text
    assert TITLES[0] not in r.text
    r = client.get("/reviews?month=2026-06")
    assert "1 of 3" in r.text and TITLES[0] in r.text


def test_reviews_search_title_and_summary(editions_dir):
    r = client.get("/reviews?q=payouts")
    assert "1 of 3" in r.text and TITLES[1] in r.text
    r = client.get("/reviews?q=june+things")  # summary text
    assert "1 of 3" in r.text and TITLES[0] in r.text


def test_reviews_sorts(editions_dir):
    r = client.get("/reviews?sort=oldest")
    assert _order(r.text, TITLES) == [TITLES[0], TITLES[1], TITLES[2]]
    r = client.get("/reviews?sort=title")
    assert _order(r.text, TITLES) == [TITLES[0], TITLES[1], TITLES[2]]


def test_reviews_unknown_month_flagged_and_empty_honest(editions_dir):
    r = client.get("/reviews?month=1999-01")
    assert r.status_code == 200
    assert "0 of 3" in r.text
    assert "unknown" in r.text and "1999-01" in r.text
    assert "no items match the active filters" in r.text


# ---------------------------------------------------------------------------
# /fleet lanes — disposition / freshness / seat dims; default sort intact
# ---------------------------------------------------------------------------
def _fixture_fleet() -> dict:
    return {
        "generated_at": "2026-07-12T06:00:00Z",
        "registry": {
            "ok": True, "reason": "", "url": "https://example/registry",
            "total_seats": 3, "repo_seats": 2,
            "registry_only_seats": ["coordinator (no repo)"],
        },
        "seats": [
            {"seat": "Websites", "role": "Control plane",
             "repos": [{"repo": "websites", "repo_url": "", "updated": "2026-07-12T05:00:00Z", "heartbeat_available": True}]},
        ],
        "lanes": [
            {
                "lane": "websites", "repo": "websites", "disposition": "live",
                "repo_url": "https://github.com/menno420/websites",
                "heartbeat": {
                    "available": True,
                    "fields": {"updated": "2026-07-12T05:00:00Z",
                               "health": "green (ok)"},
                    "source_url": "https://example/hb",
                },
            },
            {
                "lane": "darkrepo", "repo": "darkrepo", "disposition": "archived",
                "repo_url": "https://github.com/menno420/darkrepo",
                "heartbeat": {"available": False, "reason": "HTTP 404"},
            },
            {
                "lane": "coordinator (no repo)", "repo": None,
                "disposition": "registry-only",
                "heartbeat": {"available": False,
                              "reason": "registry-only seat"},
            },
        ],
    }


@pytest.fixture()
def fleet_file(tmp_path, monkeypatch):
    p = tmp_path / "fleet.json"
    p.write_text(json.dumps(_fixture_fleet()), encoding="utf-8")
    monkeypatch.setattr(fleetdata, "FLEET_PATH", p)
    monkeypatch.setattr(fleetdata, "STATS_PATH", tmp_path / "absent.json")
    return p


def _lanes_html(page: str) -> str:
    # The statrow + seats sections above the grid repeat the same names —
    # order assertions must read the lanes section only.
    return page.split("The per-repo lanes under the seats", 1)[1]


def test_fleet_no_params_keeps_disposition_order(fleet_file):
    r = client.get("/fleet")
    assert r.status_code == 200
    assert "3 of 3" in r.text
    lanes = _lanes_html(r.text)
    # attention order: live < registry-only < archived (fleet_overview's own)
    assert lanes.index(">websites<") < lanes.index("coordinator (no repo)")
    assert lanes.index("coordinator (no repo)") < lanes.index("darkrepo")


def test_fleet_disposition_and_freshness_filters(fleet_file):
    r = client.get("/fleet?disposition=archived")
    assert "1 of 3" in r.text and "darkrepo" in r.text
    r = client.get("/fleet?freshness=no-heartbeat")
    assert "2 of 3" in r.text
    # derived dimension says so
    assert "derived" in r.text


def test_fleet_seat_dim_maps_repo_to_standing_seat(fleet_file):
    r = client.get("/fleet?seat=Websites")
    assert "1 of 3" in r.text
    assert "menno420/websites" in r.text and "darkrepo" not in r.text


def test_fleet_search_and_unknown_value(fleet_file):
    r = client.get("/fleet?q=dark")
    assert "1 of 3" in r.text and "darkrepo" in r.text
    r = client.get("/fleet?disposition=bogus")
    assert "0 of 3" in r.text and "unknown" in r.text
    assert "no items match the active filters" in r.text


def test_fleet_lane_az_sort(fleet_file):
    r = client.get("/fleet?sort=az")
    lanes = _lanes_html(r.text)
    assert lanes.index("coordinator (no repo)") < lanes.index("darkrepo")
    assert lanes.index("darkrepo") < lanes.index(">websites<")


def test_fleet_mirror_missing_still_degrades_honestly(tmp_path, monkeypatch):
    monkeypatch.setattr(fleetdata, "FLEET_PATH", tmp_path / "gone.json")
    r = client.get("/fleet?disposition=live")  # params must not break the banner
    assert r.status_code == 200
    assert "Fleet mirror unavailable" in r.text


# ---------------------------------------------------------------------------
# /questions ledger — status / answer dims over the real record fields
# ---------------------------------------------------------------------------
QUESTIONS = {
    "updated": "2026-07-12",
    "note": "test ledger",
    "questions": [
        {"asked": "2026-07-01", "title": "How do payouts work?",
         "url": "https://example/q1", "status": "answered",
         "answer_url": "https://example/a1", "answer_label": "edition 1"},
        {"asked": "2026-07-10", "title": "Why vendored copies?",
         "url": "https://example/q2"},
    ],
}


@pytest.fixture()
def questions_file(tmp_path, monkeypatch):
    p = tmp_path / "questions.json"
    p.write_text(json.dumps(QUESTIONS), encoding="utf-8")
    real = story.load_questions
    monkeypatch.setattr(story, "load_questions", lambda path=None: real(p))
    return p


def test_questions_no_params_renders_ledger_order(questions_file):
    r = client.get("/questions")
    assert r.status_code == 200
    assert "2 of 2" in r.text
    assert r.text.index("How do payouts work?") < r.text.index(
        "Why vendored copies?")


def test_questions_status_defaults_open_like_the_template(questions_file):
    r = client.get("/questions?status=open")  # record 2 has NO status field
    assert "1 of 2" in r.text and "Why vendored copies?" in r.text
    r = client.get("/questions?status=answered")
    assert "1 of 2" in r.text and "How do payouts work?" in r.text


def test_questions_answer_dim_and_search(questions_file):
    r = client.get("/questions?answer=pending")
    assert "1 of 2" in r.text and "Why vendored copies?" in r.text
    r = client.get("/questions?q=payouts")
    assert "1 of 2" in r.text and "How do payouts work?" in r.text


def test_questions_sort_newest_and_unknown_value(questions_file):
    r = client.get("/questions?sort=newest")
    assert r.text.index("Why vendored copies?") < r.text.index(
        "How do payouts work?")
    r = client.get("/questions?status=bogus")
    assert "0 of 2" in r.text and "unknown" in r.text
    assert "no items match the active filters" in r.text


def test_questions_empty_ledger_keeps_its_empty_card(tmp_path, monkeypatch):
    p = tmp_path / "questions.json"
    p.write_text(json.dumps({"updated": "2026-07-12", "note": "empty on purpose",
                             "questions": []}), encoding="utf-8")
    real = story.load_questions
    monkeypatch.setattr(story, "load_questions", lambda path=None: real(p))
    r = client.get("/questions")
    assert r.status_code == 200
    assert "No external reviewer questions on record yet." in r.text


def test_fleet_zero_count_facets_suppressed_unless_active(fleet_file):
    """2026-07-13 cold pass F2 (synthetic): the fixed disposition universe
    includes "hub" but the fixture has no hub lane — the dead pill must not
    be offered, yet a deep link selecting it stays fully un-filterable."""
    r = client.get("/fleet")
    assert ">hub · 0</a>" not in r.text
    assert ">live · 1</a>" in r.text  # nonzero options still offered
    r = client.get("/fleet?disposition=hub")
    assert r.status_code == 200
    # the selected zero-count pill renders 'on', toggling back to a bare /fleet
    assert '<a class="b lf-pill on" href="/fleet">hub · 0</a>' in r.text
    assert "disposition: hub ✕" in r.text  # removable chip
    assert "0 of 3" in r.text
    assert "no items match the active filters" in r.text
