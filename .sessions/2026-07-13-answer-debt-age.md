# 2026-07-13 — review: answer-debt age on the questions ledger

> **Status:** `complete` — PR #301, branch `claude/answer-debt-age-0713`;
> the closed-but-unanswered nag (PR #299) now carries an age: the bake
> stamps the issue's own `closed_at` on closed ledger records, the advisory
> and the /questions banner say "closed N days without an answer", and the
> banner ranks offenders by answer debt, oldest broken promise first —
> old baked data without the stamp keeps the binary wording.

- **📊 Model:** Claude 5 family · worker · backlog-slice

**What this session was about:** the backlog bullet "Stamp `closed_at` on
questions-ledger records at bake time — turn the closed-but-unanswered nag
into an answer-debt age" (`docs/ideas/backlog.md`, captured 2026-07-13 by
the questions-answer-nag session 💡, PR #299). `gen_questions.issue_record`
read each issue's state but discarded its `closed_at` timestamp, so the nag
shipped in #299 read the same whether a question closed an hour ago
(answer plausibly in flight) or two weeks ago (promise genuinely broken).

## What was done

- `review/gen_questions.py` — `issue_record` stamps ``closed_at`` from the
  issue's own timestamp (SAME single REST response, no extra call) only
  while closed; `merge_questions` refreshes the bake-owned
  ``status``+``closed_at`` pair together (stamp dropped on reopen, a truthy
  ``status_override`` pins both); new `answer_debt_days` (whole UTC days,
  ``None`` on missing/bad stamps, clamped at 0); `advise_unanswered` prints
  ``ADVISORY: closed N days without an answer: <url>`` when the stamp is
  known, the #299 binary wording otherwise; module docstring documents the
  stamp + aged-advisory contract.
- `review/story.py` — mirrored `answer_debt_days` (one debt clock, two
  surfaces, agreement pinned by test) + `answer_debt(records)`: the
  `unanswered_closed` set copied with computed ``debt_days`` and ranked
  oldest-``closed_at``-first, unknowable debt after the dated in ledger
  order; pure read, input never mutated.
- `review/app.py` `/questions` passes `story.answer_debt(records)` as
  `q_nag`; `review/templates/questions.html` renders each offender's age
  "(closed N days without an answer)" after its link — records without
  ``debt_days`` fall back to the binary heading alone, so the committed
  pre-stamp `review/data/questions.json` (untouched, by design) keeps
  working until the next bake writes the field.
- Tests +11 (`review/tests/test_gen_questions.py` +7: stamp on closed /
  absent on open / merge stamps + drops on reopen / override pins the
  pair / UTC day math incl. naive stamps / degraded stamps incl. future
  clamp / aged advisory line replaces the binary one;
  `review/tests/test_questionnaire.py` +4: debt ordering + input purity,
  robustness, banner aged and ordered oldest-first, binary fallback for
  old baked data with dated debt outranking unknowable).
- `docs/ideas/backlog.md`: source bullet flipped `captured` → `built`
  (PR #301); this session's 💡 captured as a new bullet.
- Verified before push: `python3 -m pytest tests/ botsite/tests
  dashboard/tests review/tests -q` — 1315 passed, 1 warning (+11 over
  main's 1304); `python3 bootstrap.py check --strict` — green except this
  card's own designed born-red HOLD (flipped by this commit) and the
  pre-existing never-exit-affecting `owner-action-fields` advisory on
  control/status.md (not owned here).

## Close-out (auto-drafted 2026-07-13 — edited)

**Evidence (auto-draft corrected — the collector had swept repo-wide
touches and another lane's rescue commit into this card; the facts of THIS
session are):**

- code touched (4): `review/gen_questions.py`, `review/story.py`,
  `review/app.py`, `review/templates/questions.html`
- tests touched (2): `review/tests/test_gen_questions.py`,
  `review/tests/test_questionnaire.py`
- docs touched (1): `docs/ideas/backlog.md` (close-out commit)
- sessions touched (1): this card; claim
  `control/claims/2026-07-13-answer-debt-age.md` created at start,
  removed in the close-out commit
- git: branch `claude/answer-debt-age-0713` off main @ `2e83c9e`
- commits this session: "session start: born-red card …" · "claim: …" ·
  "review: answer-debt age — bake-stamped closed_at ages the
  closed-but-unanswered nag" · the close-out commit
- verify: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` → **1315 passed, 1 warning**; `python3 bootstrap.py
  check --strict` → green after this card flips (born-red HOLD was the
  only exit-affecting finding pre-flip)

**Judgment:**

- Decisions made: (1) "sort by answer debt" implemented as the nag
  banner's own ordering — the ledger TABLE's default stays byte-identical
  to ledger order because the listfilter spec pins "a no-param /questions
  renders exactly as before"; a debt sort option for the table is future
  work, not silently changed semantics. (2) `answer_debt_days` duplicated
  in gen_questions.py (stdlib-only, import-free from the package) and
  story.py rather than shared — mirroring #299's two-surfaces pattern,
  with a test pinning agreement. (3) Bad/missing stamps degrade to `None`
  → binary wording, never a crash or invented age; future stamps clamp
  to 0.
- Next session should know: the committed `review/data/questions.json` is
  still empty/pre-stamp — the field appears the first time the scheduled
  review-bake sees a closed `[program-review]` issue; nothing to migrate.

## 💡 Session idea

**Answer-latency stat on /questions — measure the promise kept, not just
broken** — the bake now stamps `closed_at` on EVERY closed record,
answered ones included, so `closed_at − asked` is a real per-question
resolution time; a small honest stat over the answered records ("answered
questions resolved in a median of N days", hidden until ≥1 answered record
exists) on /questions would measure the intake promise being KEPT — the
positive complement to the answer-debt nag, which only measures it
breaking. Worth having because the ledger's whole pitch to reviewers is
"ask and it lands answered here": a measured turnaround number is stronger
evidence than an empty nag banner, and it costs zero new fields — both
timestamps are already baked. Deduped against `docs/ideas/backlog.md`: the
bake-sync, closed-but-unanswered, and answer-debt-age bullets (all
`built`) cover intake and failure signals; the pickup-latency-rollup work
measures order pickup, not question resolution; nothing computes
asked→closed turnaround. Captured in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

The venture-vetting-catalog session (PR #248) did well — deriving each of
the 22 statuses from its packet's own Status/Verdict text and pinning the
exact 1/12/2/7 breakdown in a test made the page unfakeable; what it
missed: it shipped a decay-prone artifact and left its own freshness watch
(the sha-drift pin) as a backlog bullet — the same
build-the-nag-in-a-later-PR shape this session exists to finish for #297's
sync. Workflow improvement: when a slice adds a time-sensitive fact to
data (a status, a pin, a stamp), land the age/drift readout in the same
PR — three sessions in a row have now paid a follow-up PR for a missing
one-field readout.
