"""R7 — the bake advisory and the rendered answer-debt cannot silently disagree.

Two surfaces read the SAME broken promise (a reviewer question closed without a
published answer): the ``gen_questions`` bake prints one ``ADVISORY:`` line per
such record into the bake log, and the ``/questions`` page renders the same
records as an answer-debt nag from ``story.answer_debt`` (the ``q_nag`` context,
"(closed N days without an answer)"). Existing tests pin each surface and the
helper-level parity of ``unanswered_closed`` / ``answer_debt_days`` — but nothing
tied the bake's PRINTED advisory to the page's RENDERED debt, so the two could
drift (name different records, or age the debt differently) and the answer-debt
surface could silently lie relative to the log.

These tests tie them: the set of records the advisory names equals the set
``answer_debt`` renders, and each advisory line's day count matches that
record's rendered ``debt_days`` (aged wording for a known ``closed_at``, the
binary phrase when it is absent). ``now`` is frozen so the aged wording is
deterministic while the REAL functions still run — the bake's
``advise_unanswered`` reads its day count through the module-level
``answer_debt_days``, wrapped here to the same frozen ``now`` the page uses.
"""

from __future__ import annotations

import datetime as dt
import re

import pytest

from review import gen_questions, story

_NOW = dt.datetime(2026, 7, 13, 12, 0, tzinfo=dt.timezone.utc)

_AGED = re.compile(r"^ADVISORY: closed (\d+) days? without an answer: (.+)$")
_BINARY = re.compile(r"^ADVISORY: closed without a published answer: (.+)$")


def _record(url, **over):
    base = {
        "asked": "2026-07-01",
        "title": f"[program-review] Q for {url}",
        "url": url,
        "status": "closed",
    }
    base.update(over)
    return base


def _ledger():
    """A mix: two aged debts (3 days, 1 day), one undateable (binary nag), plus
    an answered-closed and an open record that BOTH surfaces must exclude."""
    return [
        _record("https://x.test/q/3day", closed_at="2026-07-10T12:00:00Z"),
        _record("https://x.test/q/1day", closed_at="2026-07-12T12:00:00Z"),
        _record("https://x.test/q/nodate"),  # closed, no closed_at → None debt
        _record("https://x.test/q/answered", answer_url="/reviews/edition-1",
                closed_at="2026-07-08T12:00:00Z"),
        _record("https://x.test/q/open", status="open"),
    ]


def _frozen_now(monkeypatch):
    """Freeze the bake advisory's clock to ``_NOW`` without stubbing the real
    computation — ``advise_unanswered`` calls the module-level
    ``answer_debt_days``, so wrapping that name pins ``now`` for the log side to
    exactly the ``now`` the page passes ``story.answer_debt``."""
    real = gen_questions.answer_debt_days
    monkeypatch.setattr(
        gen_questions, "answer_debt_days", lambda rec, now=None: real(rec, _NOW)
    )


def _advisory_debts(capsys) -> dict[str, int | None]:
    """Parse the printed advisory into ``{ref: day_count_or_None}``."""
    out = {}
    for line in capsys.readouterr().out.splitlines():
        m = _AGED.match(line)
        if m:
            out[m.group(2)] = int(m.group(1))
            continue
        m = _BINARY.match(line)
        if m:
            out[m.group(1)] = None
    return out


def _rendered_debts() -> dict[str, int | None]:
    """``{url: debt_days}`` exactly as ``/questions`` renders ``q_nag``."""
    return {q["url"]: q["debt_days"] for q in story.answer_debt(_ledger(), _NOW)}


def test_advisory_and_rendered_debt_name_the_same_records(monkeypatch, capsys):
    _frozen_now(monkeypatch)
    gen_questions.advise_unanswered(_ledger())
    advisory = _advisory_debts(capsys)
    rendered = _rendered_debts()
    # same broken promises on both surfaces — answered + open excluded from both
    assert set(advisory) == set(rendered)
    assert set(advisory) == {
        "https://x.test/q/3day",
        "https://x.test/q/1day",
        "https://x.test/q/nodate",
    }
    assert len(advisory) == len(rendered) == 3


def test_each_advisory_day_count_matches_the_rendered_debt(monkeypatch, capsys):
    _frozen_now(monkeypatch)
    gen_questions.advise_unanswered(_ledger())
    advisory = _advisory_debts(capsys)
    rendered = _rendered_debts()
    # per record, the log's aged count is the page's debt_days (None ⇒ binary)
    assert advisory == rendered
    assert rendered["https://x.test/q/3day"] == 3
    assert rendered["https://x.test/q/1day"] == 1   # renders singular "day"
    assert rendered["https://x.test/q/nodate"] is None


def test_the_one_day_advisory_reads_singular(monkeypatch, capsys):
    # the wording tie, not just the number: a 1-day debt says "day", not "days"
    _frozen_now(monkeypatch)
    gen_questions.advise_unanswered(_ledger())
    out = capsys.readouterr().out
    assert "closed 1 day without an answer: https://x.test/q/1day" in out
    assert "closed 3 days without an answer: https://x.test/q/3day" in out


def test_both_surfaces_empty_when_every_closed_question_is_answered(
    monkeypatch, capsys
):
    _frozen_now(monkeypatch)
    clean = [
        _record("https://x.test/q/a", answer_url="/reviews/edition-1",
                closed_at="2026-07-10T12:00:00Z"),
        _record("https://x.test/q/b", status="open"),
    ]
    gen_questions.advise_unanswered(clean)
    assert "ADVISORY" not in capsys.readouterr().out
    assert story.answer_debt(clean, _NOW) == []
