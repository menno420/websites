# 2026-07-13 — review: answer-latency stat on the questions ledger

> **Status:** `complete` — PR #302, branch `claude/questions-answer-latency-0713`;
> /questions now measures the promise KEPT: a one-line stat over the
> ANSWERED ledger records ("N answered questions resolved in a median of
> M days", from the baked `asked` + `closed_at` timestamps) — hidden
> entirely until ≥1 answered record carries both parseable timestamps, so
> the committed pre-stamp ledger renders byte-identically today.

- **📊 Model:** Claude 5 family · worker · backlog-slice

**What this session was about:** the backlog bullet "Answer-latency stat
on /questions — measure the promise kept, not just broken"
(`docs/ideas/backlog.md`, captured 2026-07-13 by the answer-debt-age
session 💡, PR #301). The bake stamps `closed_at` on EVERY closed ledger
record, answered ones included, so `closed_at − asked` is a real
per-question resolution time — but nothing computed it: the ledger's
whole pitch to reviewers is "ask and it lands answered here", and until
now the only measured signal was the answer-debt nag, which reads only
when that promise BREAKS.

## What was done

- `review/story.py` — `answer_latency_days(q)`: whole days from the
  record's `asked` date to its bake-stamped `closed_at`, UTC (`None`
  when either timestamp is missing/unparseable — pre-stamp baked data
  and hand-mangled fields are ignored, never guessed; clamped at 0 so a
  same-day answer or stamp skew never reads negative); `answer_latency
  (records)`: count + `statistics.median` over the qualifying ANSWERED
  records (`median_days` collapses to int when whole, keeps the exact
  half-day float on even counts), `None` until one qualifies — honest
  absence, no fabricated stat. Pure reads, records never mutated.
- `review/app.py` `/questions` passes `story.answer_latency(records)` as
  `q_latency`; `review/templates/questions.html` renders one `sb-muted`
  line above the ledger table ("N answered question(s) resolved in a
  median of M day(s) (asked → closed, from the ledger's baked
  timestamps)") only when the stat exists.
- Tests +4 (`review/tests/test_questionnaire.py`): `answer_latency_days`
  robustness (whole-day math, naive stamps as UTC, clamp, every
  missing/garbage combination → `None`); aggregate semantics (odd-count
  int median, even-count half-day float kept / whole collapsed, pending
  + unstamped + garbage records never count, empty → `None`); page
  renders the correct server-computed median over answered records; page
  hides the stat entirely when nothing qualifies (answered-unstamped +
  answered-mangled + closed-unanswered debt).
- `docs/ideas/backlog.md`: source bullet flipped `captured` → `built`
  (PR #302); this session's 💡 captured as a new bullet.
- Verified before push: `python3 -m pytest tests/ botsite/tests
  dashboard/tests review/tests -q` — 1319 passed, 1 warning (+4 over
  main's 1315); `python3 bootstrap.py check --strict` — green except this
  card's own designed born-red HOLD (flipped by this commit) and the
  pre-existing never-exit-affecting `owner-action-fields` advisory on
  control/status.md (not owned here).

## Close-out (auto-drafted 2026-07-13 — edited)

**Evidence (auto-draft corrected — the collector had swept repo-wide
touches and another lane's rescue commit into this card; the facts of
THIS session are):**

- code touched (3): `review/story.py`, `review/app.py`,
  `review/templates/questions.html`
- tests touched (1): `review/tests/test_questionnaire.py`
- docs touched (1): `docs/ideas/backlog.md` (close-out commit)
- sessions touched (1): this card; claim
  `control/claims/2026-07-13-questions-answer-latency.md` created at
  start, removed in the close-out commit
- git: branch `claude/questions-answer-latency-0713` off main @ `9dd4239`
- commits this session: "session start: born-red card + claim …" ·
  "review: answer-latency stat — median asked→closed turnaround over
  answered ledger records" · the close-out commit
- verify: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` → **1319 passed, 1 warning**; `python3 bootstrap.py
  check --strict` → green after this card flips (born-red HOLD was the
  only exit-affecting finding pre-flip)

**Judgment:**

- Decisions made: (1) "answered" means the record carries an
  `answer_url` (the template's own reading via
  `question_answer_state`) — status is not consulted, because a record
  can only qualify once `closed_at` exists, which the bake only stamps
  while closed. (2) Median over mean — one slow outlier must not be able
  to flatter or wreck the headline number; the exact half-day float is
  kept on even counts rather than rounding (honest, and the template
  renders "5.5 days" fine). (3) Day precision only — `asked` is baked as
  a date, so sub-day resolution would be invented; same-day answers read
  0 days (flagged as this session's 💡 rather than silently upgrading
  the bake's schema in a display slice).
- Next session should know: the committed `review/data/questions.json`
  is still empty — the stat first appears when the scheduled review-bake
  lands an answered `[program-review]` issue with its stamp; nothing to
  migrate, and the stat needs no bake change.

## 💡 Session idea

**Bake a full `asked_at` timestamp on questions-ledger records — give the
latency stat sub-day resolution** — `gen_questions.issue_record`
truncates the issue's `created_at` to a date (`created[:10]`) while
`closed_at` keeps its full timestamp, so `answer_latency_days` can never
resolve finer than whole days and a same-day answer reads "0 days" — the
stat's weakest wording exactly when the turnaround is most impressive.
Baking `asked_at` alongside the display date (same single REST response,
`asked` untouched for the table and existing sorts) would let the stat
say "resolved in a median of 6 hours" once real turnarounds are fast,
honest at the resolution the data actually has. Worth having because the
ledger's pitch is turnaround speed, and the current floor understates
precisely the best evidence. Deduped against `docs/ideas/backlog.md`:
the bake-sync, closed-but-unanswered, answer-debt-age, and
answer-latency bullets all read or write only the date-precision `asked`
plus `closed_at`; nothing carries a full asked timestamp. Captured in
`docs/ideas/backlog.md`.

## ⟲ Previous-session review

The questions-answer-nag session (PR #299) did well — the nag reused the
listfilter's own `question_status`/`question_answer_state` semantics
instead of inventing a third reading, kept `gen_questions.py`
stdlib-only with the advisory firing on every run path, and its card's
own workflow remark ("land the drift nag in the same PR") was exactly
right; what it missed: the `closed_at` timestamp that ages the nag was
sitting in the SAME REST response `issue_record` already parsed, and
discarding it cost the very next session (#301) a follow-up PR for one
field — the build-the-readout-in-a-later-PR shape its own review had
just named. Workflow improvement: when a slice parses a rich API
response, sweep it once for the one-field facts (timestamps, actors,
counts) the display will predictably want before discarding — a
five-minute sweep beats a follow-up PR per field, and this lineage has
now paid that PR twice.
