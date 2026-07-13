# 2026-07-13 — review: bake `asked_at` — sub-day resolution for the questions latency stat

> **Status:** `in-progress`

- **📊 Model:** Claude Fable 5 · worker · builder-slice

**What this session is about:** the backlog item "Bake a full `asked_at`
timestamp on questions-ledger records" (captured 2026-07-13,
questions-answer-latency session 💡; follow-on to PR #302).
`gen_questions.issue_record` truncates the issue's `created_at` to a date
(`created[:10]`) while `closed_at` keeps its full timestamp, so
`answer_latency_days` can never resolve finer than whole days — a same-day
answer reads "0 days", the stat's weakest wording exactly when the
turnaround is most impressive. This session bakes `asked_at` (full ISO
timestamp, same single REST response, `asked` untouched for the table and
sorts) and teaches the latency stat to prefer it, falling back to the
date-precision `asked` so old committed records compute and render
byte-identically.

## What was done

- [[fill: files touched + verify results]]

## 💡 Session idea

[[fill: one genuine new idea, deduped against docs/ideas/backlog.md]]

## ⟲ Previous-session review

[[fill: honest remark on .sessions/2026-07-13-venture-vetting-catalog.md]]
