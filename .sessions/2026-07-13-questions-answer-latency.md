# 2026-07-13 — review: answer-latency stat on the questions ledger

> **Status:** `in-progress` — branch `claude/questions-answer-latency-0713`;
> building the backlog bullet "Answer-latency stat on /questions — measure
> the promise kept, not just broken": a small honest stat over the ANSWERED
> ledger records ("answered questions resolved in a median of N days",
> hidden until ≥1 answered record with both timestamps exists), the
> positive complement to the answer-debt nag.

**What this session is about:** the backlog bullet "Answer-latency stat on
/questions — measure the promise kept, not just broken"
(`docs/ideas/backlog.md`, captured 2026-07-13 by the answer-debt-age
session 💡, PR #301). The bake stamps `closed_at` on EVERY closed ledger
record, answered ones included, so `closed_at − asked` is a real
per-question resolution time — but nothing computes it. The ledger's whole
pitch to reviewers is "ask and it lands answered here"; a measured
turnaround number is stronger evidence than an empty nag banner, and it
costs zero new fields — both timestamps are already baked.

## Plan

- `review/story.py`: a pure-read helper over the answered records — parse
  `asked` and `closed_at`, ignore records where either is missing or
  unparseable, return the count + median whole-day turnaround (or nothing
  when no record qualifies — honest absence, never a fabricated stat).
- `review/app.py` `/questions` passes the stat; the template renders one
  small line, hidden entirely until ≥1 answered record with both
  timestamps exists (the committed pre-stamp ledger keeps rendering
  byte-identically).
- Tests in `review/tests/test_questionnaire.py` following the nag
  patterns: stat renders with the correct median; absent with zero
  answered records; malformed/missing timestamps ignored.
- Verify: all four service suites + `bootstrap.py check --strict`.
