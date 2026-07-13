"""Questionnaire + questions-ledger + interaction-affordance tests."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient
from markupsafe import escape

from review import story
from review.app import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Questionnaire content — the honesty rules, pinned like PROBLEMS/SUCCESSES
# ---------------------------------------------------------------------------
def test_every_question_answered_with_evidence():
    assert len(story.QUESTIONNAIRE) >= 8
    seen_ids = set()
    for item in story.QUESTIONNAIRE:
        assert item["id"] not in seen_ids
        seen_ids.add(item["id"])
        assert item["q"].strip().endswith("?")
        assert len(item["a"].strip()) > 100  # a real answer, not a stub
        assert item["evidence"], f"question without evidence: {item['q']}"
        for label, url in item["evidence"]:
            assert label.strip()
            # evidence is either a repo link or an internal page — never elsewhere
            assert url.startswith("https://github.com/menno420/") or url.startswith("/")


def test_questionnaire_page_renders_all_questions():
    r = client.get("/questionnaire")
    assert r.status_code == 200
    for item in story.QUESTIONNAIRE:
        assert str(escape(item["q"])) in r.text
        assert f'id="{item["id"]}"' in r.text
    # the no-live-model honesty note is present
    assert "no model behind this page" in r.text.lower() or "There is no model" in r.text


# ---------------------------------------------------------------------------
# Ask links (interaction, read-only)
# ---------------------------------------------------------------------------
def test_ask_url_prefills_issue():
    url = story.ask_url("fleet page")
    parsed = urlparse(url)
    assert parsed.netloc == "github.com"
    assert parsed.path == "/menno420/websites/issues/new"
    qs = parse_qs(parsed.query)
    assert "fleet page" in qs["title"][0]
    assert "routed to the fleet" in qs["body"][0]


def test_pages_carry_ask_affordance():
    for path in ["/", "/fleet", "/questionnaire", "/reviews"]:
        r = client.get(path)
        assert "issues/new" in r.text, f"no ask link on {path}"


# ---------------------------------------------------------------------------
# Questions ledger
# ---------------------------------------------------------------------------
def test_questions_ledger_honest_empty_state():
    r = client.get("/questions")
    assert r.status_code == 200
    # the committed ledger starts empty on purpose — the page says so and
    # documents the intake convention rather than inventing traffic
    assert "No external reviewer questions on record yet" in r.text
    assert "review edition" in r.text


def test_questions_ledger_renders_entries(monkeypatch, tmp_path: Path):
    p = tmp_path / "questions.json"
    p.write_text(
        json.dumps(
            {
                "updated": "2026-07-12",
                "note": "n",
                "questions": [
                    {
                        "asked": "2026-07-12",
                        "title": "How do gates work?",
                        "url": "https://github.com/menno420/websites/issues/999",
                        "status": "answered",
                        "answer_url": "/reviews/2026-07-11-edition-001",
                        "answer_label": "edition 1",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    real = story.load_questions

    def fake(path=None):
        return real(p)

    monkeypatch.setattr(story, "load_questions", fake)
    r = client.get("/questions")
    assert r.status_code == 200
    assert "How do gates work?" in r.text
    assert "edition 1" in r.text
    # every listed question has its answer link — no broken-promise nag
    assert "closed without a published answer" not in r.text


def test_questions_page_nags_closed_unanswered_records(monkeypatch, tmp_path: Path):
    # keep the site-wide snapshot-aging banner (also rv-aged) out of the page
    monkeypatch.delenv("RAILWAY_GIT_COMMIT_SHA", raising=False)
    monkeypatch.delenv("GIT_SHA", raising=False)
    p = tmp_path / "questions.json"
    p.write_text(
        json.dumps(
            {
                "updated": "2026-07-13",
                "note": "n",
                "questions": [
                    {
                        "asked": "2026-07-12",
                        "title": "Closed but never answered?",
                        "url": "https://github.com/menno420/websites/issues/998",
                        "status": "closed",
                    },
                    {
                        "asked": "2026-07-12",
                        "title": "Closed and answered?",
                        "url": "https://github.com/menno420/websites/issues/997",
                        "status": "closed",
                        "answer_url": "/reviews/2026-07-11-edition-001",
                        "answer_label": "edition 1",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    real = story.load_questions

    def fake(path=None):
        return real(p)

    monkeypatch.setattr(story, "load_questions", fake)
    r = client.get("/questions")
    assert r.status_code == 200
    assert "1 question closed without a published answer" in r.text
    # the nag names the offending question, not the answered one
    banner = r.text.split('class="rv-aged"', 1)[1].split("</div>", 1)[0]
    assert "Closed but never answered?" in banner
    assert "Closed and answered?" not in banner


def test_unanswered_closed_helper_semantics():
    closed_unanswered = {"title": "a", "status": "closed"}
    closed_answered = {"title": "b", "status": "closed", "answer_url": "/reviews/x"}
    open_unanswered = {"title": "c", "status": "open"}
    defaulted_open = {"title": "d"}
    assert story.unanswered_closed(
        [closed_unanswered, closed_answered, open_unanswered, defaulted_open]
    ) == [closed_unanswered]
    assert story.unanswered_closed([]) == []


# ---------------------------------------------------------------------------
# Answer-debt age — bake-stamped closed_at turns the nag into "closed N days"
# ---------------------------------------------------------------------------

def _nag_ledger(monkeypatch, tmp_path: Path, *records):
    """Point /questions at a tmp ledger of the given records (nag pattern)."""
    monkeypatch.delenv("RAILWAY_GIT_COMMIT_SHA", raising=False)
    monkeypatch.delenv("GIT_SHA", raising=False)
    p = tmp_path / "questions.json"
    p.write_text(
        json.dumps({"updated": "2026-07-13", "note": "n", "questions": list(records)}),
        encoding="utf-8",
    )
    real = story.load_questions

    def fake(path=None):
        return real(p)

    monkeypatch.setattr(story, "load_questions", fake)


def test_answer_debt_orders_oldest_closed_first_with_fallback_after():
    now = dt.datetime(2026, 7, 13, 12, 0, tzinfo=dt.timezone.utc)
    newer = {"title": "newer", "status": "closed", "closed_at": "2026-07-12T00:00:00Z"}
    older = {"title": "older", "status": "closed", "closed_at": "2026-07-01T00:00:00Z"}
    undated = {"title": "undated", "status": "closed"}
    bad = {"title": "bad", "status": "closed", "closed_at": "garbage"}
    answered = {"title": "answered", "status": "closed", "answer_url": "/x"}
    out = story.answer_debt([undated, newer, bad, older, answered], now)
    # oldest debt first; unknowable debt keeps ledger order after the dated
    assert [q["title"] for q in out] == ["older", "newer", "undated", "bad"]
    assert [q["debt_days"] for q in out] == [12, 1, None, None]
    # pure read — the given records were never mutated
    assert "debt_days" not in newer and "debt_days" not in undated


def test_answer_debt_days_is_robust_to_missing_and_bad_stamps():
    now = dt.datetime(2026, 7, 13, 12, 0, tzinfo=dt.timezone.utc)
    assert story.answer_debt_days({"status": "closed"}, now) is None
    assert story.answer_debt_days({"closed_at": "not-a-date"}, now) is None
    assert story.answer_debt_days({"closed_at": None}, now) is None
    # future stamps clamp to 0 — a just-closed record never reads negative
    assert story.answer_debt_days({"closed_at": "2026-07-14T00:00:00Z"}, now) == 0


def test_questions_banner_ages_debt_and_orders_oldest_first(
    monkeypatch, tmp_path: Path
):
    oldest = {
        "asked": "2026-06-20",
        "title": "Oldest broken promise?",
        "url": "https://github.com/menno420/websites/issues/995",
        "status": "closed",
        "closed_at": "2026-06-25T00:00:00Z",
    }
    newer = {
        "asked": "2026-07-01",
        "title": "Newer broken promise?",
        "url": "https://github.com/menno420/websites/issues/996",
        "status": "closed",
        "closed_at": "2026-07-05T00:00:00Z",
    }
    _nag_ledger(monkeypatch, tmp_path, newer, oldest)  # ledger order: newer first
    r = client.get("/questions")
    assert r.status_code == 200
    banner = r.text.split('class="rv-aged"', 1)[1].split("</div>", 1)[0]
    # each offender carries its server-computed age, "closed N days …"
    for q in (oldest, newer):
        days = story.answer_debt_days(q)
        assert days is not None and days > 1
        assert f"closed {days} days without an answer" in banner
    # … and the banner ranks by debt: oldest closed_at first
    assert banner.index("Oldest broken promise?") < banner.index(
        "Newer broken promise?"
    )


def test_questions_banner_falls_back_to_binary_wording_without_closed_at(
    monkeypatch, tmp_path: Path
):
    # old baked data — the committed ledger predates the closed_at stamp
    dated = {
        "asked": "2026-07-01",
        "title": "Dated debt?",
        "url": "https://github.com/menno420/websites/issues/994",
        "status": "closed",
        "closed_at": "2026-07-05T00:00:00Z",
    }
    undated = {
        "asked": "2026-07-01",
        "title": "Undated debt?",
        "url": "https://github.com/menno420/websites/issues/993",
        "status": "closed",
    }
    _nag_ledger(monkeypatch, tmp_path, undated, dated)
    r = client.get("/questions")
    assert r.status_code == 200
    # the binary heading still carries the promise for every offender
    assert "2 questions closed without a published answer" in r.text
    banner = r.text.split('class="rv-aged"', 1)[1].split("</div>", 1)[0]
    # the undated record renders without an invented age …
    undated_part = banner.split("Undated debt?", 1)[1].split("·", 1)[0]
    assert "without an answer" not in undated_part
    # … the dated one is aged, and dated debt outranks unknowable debt
    assert "days without an answer" in banner
    assert banner.index("Dated debt?") < banner.index("Undated debt?")


def test_load_questions_degrades(tmp_path: Path):
    res = story.load_questions(tmp_path / "nope.json")
    assert res["ok"] is False and "missing" in res["error"]
    bad = tmp_path / "bad.json"
    bad.write_text("{oops", encoding="utf-8")
    assert story.load_questions(bad)["ok"] is False
    malformed = tmp_path / "m.json"
    malformed.write_text(json.dumps({"questions": "not a list"}), encoding="utf-8")
    assert "malformed" in story.load_questions(malformed)["error"]


# ---------------------------------------------------------------------------
# Snapshot-aging banner (the backlog idea, built): deployed sha vs baked sha
# ---------------------------------------------------------------------------
def test_snapshot_aging_banner_on_sha_mismatch(monkeypatch):
    monkeypatch.setenv("RAILWAY_GIT_COMMIT_SHA", "0000000000000000000000000000000000000000")
    r = client.get("/")
    assert "the repo has moved since" in r.text


def test_no_aging_banner_when_shas_match(monkeypatch):
    snap = story.load_snapshot()
    assert snap["ok"]
    monkeypatch.setenv("RAILWAY_GIT_COMMIT_SHA", snap["data"]["git_head"])
    r = client.get("/")
    assert "the repo has moved since" not in r.text


def test_nav_covers_all_sections():
    r = client.get("/")
    for href in ["/process", "/growth", "/fleet", "/reviews", "/questionnaire", "/successes", "/problems"]:
        assert f'href="{href}"' in r.text
