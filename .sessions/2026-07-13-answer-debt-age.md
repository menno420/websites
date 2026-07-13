# 2026-07-13 — review: answer-debt age on the questions ledger

> **Status:** `in-progress` — branch `claude/answer-debt-age-0713`; stamping
> the issue's `closed_at` on questions-ledger records at bake time so the
> closed-but-unanswered nag (PR #299) stops being binary: the advisory and
> the /questions banner will say "closed N days without an answer" and the
> banner will rank offenders by answer debt, oldest broken promise first.

- **📊 Model:** Claude 5 family · worker · backlog-slice

**What this session was about:** the backlog bullet "Stamp `closed_at` on
questions-ledger records at bake time — turn the closed-but-unanswered nag
into an answer-debt age" (`docs/ideas/backlog.md`, captured 2026-07-13 by
the questions-answer-nag session 💡, PR #299). `gen_questions.issue_record`
reads each issue's state but discards its `closed_at` timestamp, so the nag
shipped in #299 reads the same whether a question closed an hour ago
(answer plausibly in flight) or two weeks ago (promise genuinely broken).
Plan: record `closed_at` at bake time (one field off the SAME REST response,
hand-written fields untouched, absent while open); compute the debt age
server-side in UTC, robust to missing/bad timestamps; age the advisory and
banner wording with graceful fallback to the binary wording for old baked
data (the committed `review/data/questions.json` won't carry the field until
the next bake); order the nagged records oldest-`closed_at`-first among
themselves while every other ordering semantic stays put.

## What was done

- (in progress — filled at close-out)
