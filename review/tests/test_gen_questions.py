"""gen_questions.py — the questions-ledger bake. Network-free: every test
monkeypatches ``fetch_issues`` (or drives the pure helpers directly); the
fail-soft tests assert the committed-file contract BYTE-identically."""

from __future__ import annotations

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
    }
    # the emitted record satisfies the /questions filter semantics as-is
    assert story.question_status(rec) == "open"
    assert story.question_answer_state(rec) == "pending"


def test_closed_issue_state_maps_to_closed_status():
    rec = gen_questions.issue_record(_issue(state="closed"))
    assert rec["status"] == "closed"


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
