# 2026-07-13 — review: bake `asked_at` — sub-day resolution for the questions latency stat

> **Status:** `complete` — PR #305, branch `claude/asked-at-timestamp-0713`;
> the questions ledger now bakes the full `asked_at` timestamp alongside
> the untouched display date, and the /questions latency stat resolves
> sub-day turnarounds ("resolved in a median of 6 hours") while the
> committed pre-stamp ledger computes and renders byte-identically;
> lands via the auto-merge enabler on green.

- **📊 Model:** Claude Fable 5 · worker · builder-slice

**What this session was about:** the backlog item "Bake a full `asked_at`
timestamp on questions-ledger records" (captured 2026-07-13,
questions-answer-latency session 💡; follow-on to PR #302).
`gen_questions.issue_record` truncates the issue's `created_at` to a date
(`created[:10]`) while `closed_at` keeps its full timestamp, so
`answer_latency_days` can never resolve finer than whole days — a same-day
answer reads "0 days", the stat's weakest wording exactly when the
turnaround is most impressive. This session baked `asked_at` (full ISO
timestamp, same single REST response, `asked` untouched for the table and
sorts) and taught the latency stat to prefer it, falling back to the
date-precision `asked` so old committed records compute and render
byte-identically.

## What was done

- `review/gen_questions.py` — `issue_record()` stamps `asked_at` from the
  same response's full `created_at` (never fabricated when the payload
  lacks the field); module docstring updated. Merge untouched: `asked_at`
  rides only on new records — no backfill, no committed-ledger rewrite.
- `review/story.py` — `answer_latency_days()` prefers a parseable
  `asked_at` (fractional days, int when whole, clamped at 0, unparseable
  stamp degrades to the date fallback) and keeps the exact pre-existing
  whole-day arithmetic for `asked`-only records; new `latency_label()`
  ("N days" byte-identical for whole/half-day medians, hours under a day,
  "under an hour" below one, one-decimal days otherwise);
  `answer_latency()` adds `median_label` to the stat dict.
- `review/templates/questions.html` — the stat renders `median_label`
  instead of hardcoding "N day(s)".
- Tests: 6 new — `test_gen_questions.py` (asked_at stamped + never
  fabricated; merge never backfills existing records — the byte-identical
  pin) and `test_questionnaire.py` (sub-day preference + fallbacks,
  sub-day medians, `latency_label` wordings, /questions renders
  "6 hours"); existing latency tests extended for `median_label`.
- `docs/ideas/backlog.md` — the asked_at bullet flipped to `built`
  (PR #305); this session's 💡 captured as a new bullet.
- Verified before both pushes: `python3 -m pytest tests/ botsite/tests
  dashboard/tests review/tests -q` — 1342 passed, 1 warning (+6 over
  main's 1336); `python3 bootstrap.py check --strict` — green except this
  card's own designed born-red HOLD (flipped by this commit) and the
  pre-existing never-exit-affecting `owner-action-fields` advisory on
  control/status.md (not owned here).

## 💡 Session idea

**One-shot `asked_at` backfill for the committed pre-stamp questions
ledger** — PR #305 gives sub-day resolution only to records baked after it
lands; the merge deliberately never backfills `asked_at` (pinned by test so
this PR's committed file stayed byte-identical), which floors every
historical answered record at date precision forever, and a median over
mixed-precision records stays coarse while the legacy majority dominates.
The GitHub API still serves `created_at` for every issue url already in
the ledger, so a one-time backfill run — or teaching the merge to stamp
`asked_at` when missing, bake-owned exactly like `closed_at` (strictly
additive, no display change) — would give the entire ledger the same
honest resolution in one bake diff. Deduped against `docs/ideas/backlog.md`:
the asked_at bullet (built, #305) stamps new records only; the bake-sync
and answer-debt bullets own status/closed_at; nothing proposes
backfilling. Captured in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

The venture-vetting-catalog session (PR #248) did well — 22 packets
hand-curated with per-entry provenance pinned at a single upstream sha and
an honest-registry test (1/12/2/7 breakdown) that makes silent drift to the
committed data loud; what it missed is the decay it named itself: a
hand-curated registry goes stale the moment the vetting lane moves, and its
own sha-drift-pin idea is still only a backlog bullet, so the page's
honesty currently depends on someone remembering to re-curate.
