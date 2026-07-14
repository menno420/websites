"""gen_questions.py — the questions-ledger bake. Network-free: every test
monkeypatches ``fetch_issues`` (or drives the pure helpers directly); the
fail-soft tests assert the committed-file contract BYTE-identically."""

from __future__ import annotations

import datetime as dt
import json
import re

from review import gen_questions, story


# ---------------------------------------------------------------------------
# fixtures — issue objects as the REST API shapes them
# ---------------------------------------------------------------------------

def _issue(**over):
    base = {
        "title": "[program-review] How does the merge gate work?",
        "html_url": "https://github.com/menno420/websites/issues/301",
        "created_at": "2026-07-12T09:30:00Z",
        "state": "open",
    }
    base.update(over)
    return base


def _ledger(*records, note="honest note", updated="2026-07-11"):
    return {"updated": updated, "note": note, "questions": list(records)}


def _run_main(tmp_path, monkeypatch, doc, issues):
    """Point the bake at a tmp copy of the ledger, feed it ``issues``, run."""
    p = tmp_path / "questions.json"
    p.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    monkeypatch.setattr(gen_questions, "OUT_PATH", p)
    monkeypatch.setattr(gen_questions, "fetch_issues", lambda: (issues, ""))
    return p, gen_questions.main()


# ---------------------------------------------------------------------------
# intake filter — title marker in/out, PR objects excluded
# ---------------------------------------------------------------------------

def test_title_marker_filters_in_case_insensitively():
    assert gen_questions.is_review_question(_issue())
    assert gen_questions.is_review_question(
        _issue(title="Re: [Program-Review] follow-up")
    )


def test_titles_without_the_marker_are_ignored():
    assert not gen_questions.is_review_question(_issue(title="bug: /fleet 500s"))
    assert not gen_questions.is_review_question(_issue(title=""))
    assert not gen_questions.is_review_question(_issue(title=None))


def test_pr_objects_are_excluded_even_with_the_marker():
    pr = _issue(pull_request={"url": "https://api.github.com/..."})
    assert not gen_questions.is_review_question(pr)


# ---------------------------------------------------------------------------
# mapping — asked date, url, open/closed status
# ---------------------------------------------------------------------------

def test_record_maps_title_url_asked_date_and_open_status():
    rec = gen_questions.issue_record(_issue())
    assert rec == {
        "asked": "2026-07-12",
        "title": "[program-review] How does the merge gate work?",
        "url": "https://github.com/menno420/websites/issues/301",
        "status": "open",
        "asked_at": "2026-07-12T09:30:00Z",
    }
    # the emitted record satisfies the /questions filter semantics as-is
    assert story.question_status(rec) == "open"
    assert story.question_answer_state(rec) == "pending"


def test_record_stamps_full_asked_at_alongside_the_display_date():
    rec = gen_questions.issue_record(_issue())
    # SAME created_at, both precisions: ``asked`` for the table,
    # ``asked_at`` for the latency stat's sub-day resolution
    assert rec["asked"] == "2026-07-12"
    assert rec["asked_at"] == "2026-07-12T09:30:00Z"
    # never fabricated when the payload lacks the timestamp
    assert "asked_at" not in gen_questions.issue_record(_issue(created_at=None))
    assert "asked_at" not in gen_questions.issue_record(_issue(created_at=""))


def test_merge_never_backfills_asked_at_onto_existing_records():
    # committed pre-``asked_at`` records stay byte-identical through the
    # merge — the bake only owns status + closed_at on existing records
    existing = [{
        "asked": "2026-07-12",
        "title": "[program-review] How does the merge gate work?",
        "url": "https://github.com/menno420/websites/issues/301",
        "status": "open",
    }]
    merged = gen_questions.merge_questions(existing, [_issue()])
    assert merged == existing


def test_closed_issue_state_maps_to_closed_status():
    rec = gen_questions.issue_record(_issue(state="closed"))
    assert rec["status"] == "closed"


def test_closed_issue_record_stamps_closed_at_from_the_same_response():
    rec = gen_questions.issue_record(
        _issue(state="closed", closed_at="2026-07-10T12:00:00Z")
    )
    assert rec["status"] == "closed"
    assert rec["closed_at"] == "2026-07-10T12:00:00Z"


def test_open_issue_record_carries_no_closed_at():
    assert "closed_at" not in gen_questions.issue_record(_issue())
    assert "closed_at" not in gen_questions.issue_record(_issue(closed_at=None))
    # a closed issue whose payload lacks the stamp stays honest too —
    # no field beats an empty string the debt clock would choke on
    assert "closed_at" not in gen_questions.issue_record(_issue(state="closed"))


# ---------------------------------------------------------------------------
# merge — hand-written fields survive, overrides pin status
# ---------------------------------------------------------------------------

def test_merge_preserves_answer_url_and_answer_label():
    existing = [{
        "asked": "2026-07-12",
        "title": "[program-review] How does the merge gate work?",
        "url": "https://github.com/menno420/websites/issues/301",
        "status": "open",
        "answer_url": "https://example.test/reviews/edition-3#q1",
        "answer_label": "edition 3",
    }]
    merged = gen_questions.merge_questions(existing, [_issue(state="closed")])
    assert len(merged) == 1
    assert merged[0]["answer_url"] == "https://example.test/reviews/edition-3#q1"
    assert merged[0]["answer_label"] == "edition 3"
    assert merged[0]["status"] == "closed"  # live state refreshed
    assert story.question_answer_state(merged[0]) == "answered"


def test_merge_keeps_a_hand_set_status_override():
    existing = [{
        "asked": "2026-07-12",
        "title": "[program-review] How does the merge gate work?",
        "url": "https://github.com/menno420/websites/issues/301",
        "status": "answered",
        "status_override": True,
    }]
    merged = gen_questions.merge_questions(existing, [_issue(state="closed")])
    assert merged[0]["status"] == "answered"  # the hand's pin wins


def test_merge_stamps_closed_at_and_drops_it_on_reopen():
    existing = [{
        "asked": "2026-07-12",
        "title": "[program-review] How does the merge gate work?",
        "url": "https://github.com/menno420/websites/issues/301",
        "status": "open",
        "answer_url": "https://example.test/reviews/edition-3#q1",
    }]
    closed = _issue(state="closed", closed_at="2026-07-10T12:00:00Z")
    merged = gen_questions.merge_questions(existing, [closed])
    assert merged[0]["status"] == "closed"
    assert merged[0]["closed_at"] == "2026-07-10T12:00:00Z"
    # hand-written fields still untouched alongside the bake-owned pair
    assert merged[0]["answer_url"] == "https://example.test/reviews/edition-3#q1"
    # the issue reopening drops the stamp with the status flip
    reopened = gen_questions.merge_questions(merged, [_issue()])
    assert reopened[0]["status"] == "open"
    assert "closed_at" not in reopened[0]


def test_merge_status_override_pins_the_closed_at_stamp_too():
    existing = [{
        "asked": "2026-07-12",
        "title": "[program-review] How does the merge gate work?",
        "url": "https://github.com/menno420/websites/issues/301",
        "status": "answered",
        "status_override": True,
    }]
    closed = _issue(state="closed", closed_at="2026-07-10T12:00:00Z")
    merged = gen_questions.merge_questions(existing, [closed])
    assert merged[0]["status"] == "answered"
    assert "closed_at" not in merged[0]  # the pin covers the whole pair


def test_merge_appends_new_questions_oldest_first_and_dedupes_by_url():
    older = _issue(
        title="[program-review] Where do the numbers come from?",
        html_url="https://github.com/menno420/websites/issues/290",
        created_at="2026-07-10T08:00:00Z",
    )
    existing = [{
        "asked": "2026-07-01",
        "title": "hand-kept question",
        "url": "https://example.test/hand",
        "status": "open",
    }]
    merged = gen_questions.merge_questions(
        existing, [_issue(), older, _issue()]  # issue 301 fed twice — one record
    )
    assert [r["url"] for r in merged] == [
        "https://example.test/hand",  # ledger order kept, hand record untouched
        "https://github.com/menno420/websites/issues/290",
        "https://github.com/menno420/websites/issues/301",
    ]
    # repeated bakes over the same inputs are byte-stable
    assert gen_questions.merge_questions(merged, [_issue(), older]) == merged


# ---------------------------------------------------------------------------
# main() — fail-soft + write discipline against the committed file
# ---------------------------------------------------------------------------

def test_fetch_failure_leaves_file_byte_identical_and_exits_zero(
    tmp_path, monkeypatch
):
    p = tmp_path / "questions.json"
    before = json.dumps(_ledger(), indent=2) + "\n"
    p.write_text(before, encoding="utf-8")
    monkeypatch.setattr(gen_questions, "OUT_PATH", p)
    monkeypatch.setattr(gen_questions, "fetch_issues", lambda: (None, "HTTP 403"))
    assert gen_questions.main() == 0
    assert p.read_text(encoding="utf-8") == before


def test_empty_result_keeps_the_honest_empty_ledger_byte_identical(
    tmp_path, monkeypatch
):
    doc = _ledger()  # questions: []
    p, rc = _run_main(tmp_path, monkeypatch, doc, [])
    assert rc == 0
    assert p.read_text(encoding="utf-8") == json.dumps(doc, indent=2) + "\n"


def test_write_refreshes_updated_stamp_and_keeps_the_note(tmp_path, monkeypatch):
    p, rc = _run_main(tmp_path, monkeypatch, _ledger(), [_issue()])
    assert rc == 0
    out = json.loads(p.read_text(encoding="utf-8"))
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", out["updated"])
    assert out["updated"] >= "2026-07-13"  # refreshed, not the committed stamp
    assert out["note"] == "honest note"  # the file's honest note survives
    assert [r["url"] for r in out["questions"]] == [
        "https://github.com/menno420/websites/issues/301"
    ]


# ---------------------------------------------------------------------------
# closed-but-unanswered advisory — the broken promise nags every run
# ---------------------------------------------------------------------------

def _closed_record(**over):
    base = {
        "asked": "2026-07-12",
        "title": "[program-review] How does the merge gate work?",
        "url": "https://github.com/menno420/websites/issues/301",
        "status": "closed",
    }
    base.update(over)
    return base


def test_unanswered_closed_flags_only_closed_records_without_answers():
    closed_unanswered = _closed_record()
    closed_answered = _closed_record(answer_url="/reviews/edition-1")
    still_open = _closed_record(status="open")
    defaulted_open = {k: v for k, v in _closed_record().items() if k != "status"}
    records = [closed_unanswered, closed_answered, still_open, defaulted_open]
    assert gen_questions.unanswered_closed(records) == [closed_unanswered]
    # the app-side reading agrees — one promise, two surfaces
    assert story.unanswered_closed(records) == [closed_unanswered]


def test_bake_prints_advisory_for_closed_unanswered_records(
    tmp_path, monkeypatch, capsys
):
    doc = _ledger(_closed_record())
    _, rc = _run_main(tmp_path, monkeypatch, doc, [_issue(state="closed")])
    assert rc == 0
    out = capsys.readouterr().out
    assert "ADVISORY: closed without a published answer" in out
    assert "issues/301" in out


def test_advisory_fires_even_when_the_fetch_fails(tmp_path, monkeypatch, capsys):
    p = tmp_path / "questions.json"
    p.write_text(
        json.dumps(_ledger(_closed_record()), indent=2) + "\n", encoding="utf-8"
    )
    monkeypatch.setattr(gen_questions, "OUT_PATH", p)
    monkeypatch.setattr(gen_questions, "fetch_issues", lambda: (None, "HTTP 403"))
    assert gen_questions.main() == 0
    assert "ADVISORY: closed without a published answer" in capsys.readouterr().out


def test_no_advisory_when_every_closed_question_is_answered(
    tmp_path, monkeypatch, capsys
):
    doc = _ledger(
        _closed_record(answer_url="/reviews/edition-1", answer_label="edition 1")
    )
    _, rc = _run_main(tmp_path, monkeypatch, doc, [_issue(state="closed")])
    assert rc == 0
    assert "ADVISORY" not in capsys.readouterr().out


# ---------------------------------------------------------------------------
# answer-debt age — closed_at turns the binary nag into "closed N days"
# ---------------------------------------------------------------------------

_NOW = dt.datetime(2026, 7, 13, 12, 0, tzinfo=dt.timezone.utc)


def test_answer_debt_days_counts_whole_utc_days():
    rec = _closed_record(closed_at="2026-07-10T12:00:00Z")
    assert gen_questions.answer_debt_days(rec, _NOW) == 3
    # the app-side clock agrees — one debt, two surfaces
    assert story.answer_debt_days(rec, _NOW) == 3
    assert gen_questions.answer_debt_days(
        _closed_record(closed_at="2026-07-12T13:00:00Z"), _NOW
    ) == 0  # closed under a day ago


def test_answer_debt_days_degrades_on_missing_or_bad_stamps():
    assert gen_questions.answer_debt_days(_closed_record(), _NOW) is None
    assert gen_questions.answer_debt_days(
        _closed_record(closed_at="not-a-date"), _NOW
    ) is None
    assert gen_questions.answer_debt_days(_closed_record(closed_at=""), _NOW) is None
    assert gen_questions.answer_debt_days(_closed_record(closed_at=None), _NOW) is None
    # a future stamp (clock skew) clamps to 0 — never a negative debt
    assert gen_questions.answer_debt_days(
        _closed_record(closed_at="2026-07-14T00:00:00Z"), _NOW
    ) == 0
    # a naive timestamp is read as UTC rather than rejected
    assert gen_questions.answer_debt_days(
        _closed_record(closed_at="2026-07-10T12:00:00"), _NOW
    ) == 3


def test_bake_advisory_ages_the_debt_when_closed_at_is_known(
    tmp_path, monkeypatch, capsys
):
    doc = _ledger(_closed_record())
    _, rc = _run_main(
        tmp_path,
        monkeypatch,
        doc,
        [_issue(state="closed", closed_at="2026-07-01T00:00:00Z")],
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert re.search(
        r"ADVISORY: closed \d+ days? without an answer: .*issues/301", out
    )
    # the aged line replaces the binary wording, never doubles it
    assert "closed without a published answer" not in out
