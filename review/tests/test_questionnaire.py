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


# ---------------------------------------------------------------------------
# Answer-latency stat — median asked→closed turnaround over ANSWERED records,
# the promise-kept complement to the answer-debt nag
# ---------------------------------------------------------------------------

def _answered(title: str, asked: str, closed_at, num: int = 990) -> dict:
    rec = {
        "asked": asked,
        "title": title,
        "url": f"https://github.com/menno420/websites/issues/{num}",
        "status": "closed",
        "answer_url": "/reviews/2026-07-11-edition-001",
        "answer_label": "edition 1",
    }
    if closed_at is not None:
        rec["closed_at"] = closed_at
    return rec


def test_answer_latency_days_is_robust_to_missing_and_bad_stamps():
    good = {"asked": "2026-07-01", "closed_at": "2026-07-05T09:30:00Z"}
    assert story.answer_latency_days(good) == 4
    # naive stamps read as UTC, same-day answers read 0
    assert story.answer_latency_days(
        {"asked": "2026-07-01", "closed_at": "2026-07-01T23:00:00"}
    ) == 0
    # a closed_at before asked (clock skew / hand-mangled data) clamps to 0
    assert story.answer_latency_days(
        {"asked": "2026-07-05", "closed_at": "2026-07-01T00:00:00Z"}
    ) == 0
    # either timestamp missing or unparseable → None, never a guess
    assert story.answer_latency_days({"asked": "2026-07-01"}) is None
    assert story.answer_latency_days({"closed_at": "2026-07-05T00:00:00Z"}) is None
    assert story.answer_latency_days(
        {"asked": "garbage", "closed_at": "2026-07-05T00:00:00Z"}
    ) is None
    assert story.answer_latency_days(
        {"asked": "2026-07-01", "closed_at": "garbage"}
    ) is None
    assert story.answer_latency_days({}) is None


def test_answer_latency_days_prefers_asked_at_for_sub_day_resolution():
    # the full stamp resolves what the date floor read as "0 days"
    assert story.answer_latency_days({
        "asked": "2026-07-01",
        "asked_at": "2026-07-01T09:00:00Z",
        "closed_at": "2026-07-01T15:00:00Z",
    }) == 0.25
    # whole spans still collapse to int, asked_at works without asked
    assert story.answer_latency_days({
        "asked_at": "2026-07-01T09:00:00Z",
        "closed_at": "2026-07-05T09:00:00Z",
    }) == 4
    # a naive asked_at reads as UTC rather than being rejected
    assert story.answer_latency_days({
        "asked_at": "2026-07-01T09:00:00",
        "closed_at": "2026-07-01T21:00:00Z",
    }) == 0.5
    # clock skew between the stamps clamps to 0, never negative
    assert story.answer_latency_days({
        "asked_at": "2026-07-01T12:00:00Z",
        "closed_at": "2026-07-01T09:00:00Z",
    }) == 0
    # an unparseable asked_at degrades to the date-precision fallback…
    assert story.answer_latency_days({
        "asked": "2026-07-01",
        "asked_at": "garbage",
        "closed_at": "2026-07-05T09:30:00Z",
    }) == 4
    # …and to None when there is no fallback to degrade to
    assert story.answer_latency_days(
        {"asked_at": "garbage", "closed_at": "2026-07-05T09:30:00Z"}
    ) is None


def test_answer_latency_medians_answered_records_only():
    a = _answered("a", "2026-07-01", "2026-07-02T00:00:00Z")  # 1 day
    b = _answered("b", "2026-07-01", "2026-07-04T00:00:00Z")  # 3 days
    c = _answered("c", "2026-07-01", "2026-07-09T00:00:00Z")  # 8 days
    pending = {"title": "p", "status": "closed", "closed_at": "2026-06-01T00:00:00Z"}
    unstamped = _answered("u", "2026-07-01", None)
    # odd count → the middle value, an int
    assert story.answer_latency([a, b, c, pending, unstamped]) == {
        "count": 3, "median_days": 3, "median_label": "3 days",
    }
    # even count → half-day medians stay exact, whole ones collapse to int
    assert story.answer_latency([a, b]) == {
        "count": 2, "median_days": 2, "median_label": "2 days",
    }
    assert story.answer_latency([b, c]) == {
        "count": 2, "median_days": 5.5, "median_label": "5.5 days",
    }
    # no qualifying record → None (pending debt and bad stamps never count)
    assert story.answer_latency([]) is None
    assert story.answer_latency([pending, unstamped]) is None
    assert story.answer_latency(
        [_answered("g", "garbage", "2026-07-05T00:00:00Z")]
    ) is None


def test_answer_latency_resolves_sub_day_medians_from_asked_at():
    fast = _answered("f", "2026-07-01", "2026-07-01T15:00:00Z")
    fast["asked_at"] = "2026-07-01T09:00:00Z"  # 6 hours
    assert story.answer_latency([fast]) == {
        "count": 1, "median_days": 0.25, "median_label": "6 hours",
    }
    # a record without asked_at still counts at date precision alongside
    dated = _answered("d", "2026-07-01", "2026-07-04T09:00:00Z")  # 3 days
    stat = story.answer_latency([fast, dated])
    assert stat["count"] == 2 and stat["median_days"] == 1.625


def test_latency_label_wordings():
    assert story.latency_label(0) == "0 days"
    assert story.latency_label(1) == "1 day"
    assert story.latency_label(3) == "3 days"
    assert story.latency_label(5.5) == "5.5 days"  # date-precision wording kept
    assert story.latency_label(0.25) == "6 hours"
    assert story.latency_label(1 / 24) == "1 hour"
    assert story.latency_label(0.01) == "under an hour"
    assert story.latency_label(1.625) == "1.6 days"
    assert story.latency_label(2.04) == "2 days"  # one-decimal round collapses


def test_questions_page_renders_latency_stat_with_correct_median(
    monkeypatch, tmp_path: Path
):
    _nag_ledger(
        monkeypatch,
        tmp_path,
        _answered("Fast answer?", "2026-07-01", "2026-07-02T00:00:00Z", 992),
        _answered("Slow answer?", "2026-07-01", "2026-07-08T00:00:00Z", 991),
    )
    r = client.get("/questions")
    assert r.status_code == 200
    # median of [1, 7] days — the stat is server-computed and pluralized
    assert "<strong>2 answered questions</strong> resolved in a median of" in r.text
    assert "<strong>4 days</strong>" in r.text


def test_questions_page_words_sub_day_latency_in_hours(
    monkeypatch, tmp_path: Path
):
    fast = _answered("Same-day answer?", "2026-07-01", "2026-07-01T15:00:00Z", 987)
    fast["asked_at"] = "2026-07-01T09:00:00Z"  # 6 hours asked → closed
    _nag_ledger(monkeypatch, tmp_path, fast)
    r = client.get("/questions")
    assert r.status_code == 200
    assert "<strong>1 answered question</strong> resolved in a median of" in r.text
    assert "<strong>6 hours</strong>" in r.text
    assert "0 days" not in r.text  # the old floor's weakest wording is gone


def test_questions_page_hides_latency_stat_without_qualifying_records(
    monkeypatch, tmp_path: Path
):
    # answered but unstamped (old baked data) + answered with a mangled stamp
    # + closed-but-unanswered debt: nothing qualifies, the stat is absent
    _nag_ledger(
        monkeypatch,
        tmp_path,
        _answered("Answered pre-stamp?", "2026-07-01", None, 989),
        _answered("Answered, stamp mangled?", "2026-07-01", "garbage", 988),
        {"title": "Still owed?", "status": "closed",
         "closed_at": "2026-07-01T00:00:00Z"},
    )
    r = client.get("/questions")
    assert r.status_code == 200
    assert "resolved in a median of" not in r.text


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
    for href in ["/process", "/growth", "/fleet", "/reviews", "/questionnaire", "/questions", "/successes", "/problems"]:
        assert f'href="{href}"' in r.text


def test_nav_surfaces_questions_ledger():
    # R1: the built /questions ledger is reachable from the header NAV, not
    # only by direct URL — and the page it links to still returns 200 with its
    # deliberately-honest empty state over the empty committed ledger.
    home = client.get("/")
    assert 'href="/questions"' in home.text
    q = client.get("/questions")
    assert q.status_code == 200
    assert "No external reviewer questions on record yet" in q.text
    # on the ledger page, its own NAV entry is the current one (not its Q&A
    # sibling) — the R1 active-state fix
    assert 'href="/questions" aria-current="page"' in q.text
