# 2026-07-13 — build-direct: wake-ritual open-work sweep doc step + drift guard

> **Status:** `complete` — PR #315, branch `claude/build-direct-0713`; the
> wake ritual's two paste-ready docs now carry the open-work sweep as a
> required pre-rung step with `scripts/open_work.py`'s real states, and
> `tests/test_wake_ritual_docs.py` reddens any PR that renames a
> classifier state without updating the docs; lands via the enabler on
> green `quality`.

- **📊 Model:** Fable 5 · worker · order-slice (ORDER 027 item 8, build-direct)

**What this session was about:** ORDER 027 item 8 [build-direct] — build ONE
slice from the two idea-engine ideas. Both ideas' scripts already shipped
2026-07-11 (`scripts/review_row_check.py` slice 14; `scripts/open_work.py`
PR #90), and idea A's remaining slice (wiring `review_row_check.py` into
`quality.yml`) is blocked tonight by the sibling fastlane-outbox-gate
session owning that workflow. The pick is therefore idea B — "Open-PR
awareness at wake" (`docs/ideas/open-pr-awareness-at-wake-2026-07-10.md`,
idea-engine copy @ `2e5d73f`): its §8 smallest shippable slice was the
wake-ritual DOC step, explicitly skipped when PR #90 shipped the script
first. This slice completes it — docs reference the shipped script's REAL
classifier states, drift-guarded by a new test.

## What was done

- `docs/project/routine-prompt.md` — one tight sweep step added inside the
  v2 WAKE paste block (before picking a rung: `python3 scripts/open_work.py`
  or `git ls-remote --heads origin` fallback; PR-OPEN → leave to its
  session, PR-LESS → stranded-work rescue candidate, NO-DIFF/MERGED-STALE →
  prune/ledger-drift, unknowable PR state → say so, never guess, Q-0120);
  a dated one-line edit note under the v2 heading.
- `docs/project/project-instructions.md` — the same sweep as one line in
  ROUTINE-FIRED protocol step 1 plus a compact six-state table using the
  script's literal states (PR-OPEN / PR-LESS / NO-DIFF / MERGED-STALE /
  PR-UNKNOWN / UNKNOWN). The sweep is a live read — its output is never
  committed (the idea's staleness-inversion trap).
- `docs/ideas/open-pr-awareness-at-wake-2026-07-10.md` — short forward-only
  note appended (existing text untouched): doc-step slice shipped
  2026-07-13, this PR.
- `tests/test_wake_ritual_docs.py` — NEW drift guard: both docs mention
  `open_work.py`; the state labels are regexed out of the script SOURCE
  (never executed, no network) and each must appear in the
  project-instructions table, so a state rename breaks the build until the
  docs follow; script existence pinned.
- Verified before push: `python3 -m pytest tests/ botsite/tests
  dashboard/tests review/tests -q` — 1349 passed, 1 warning (+4 over
  main's 1345); `python3 bootstrap.py check --strict` — "check: all checks
  passed." (born-red HOLD on this card by design until this flip).

⚑ Self-initiated: no — ORDER 027 item 8 (build-direct), idea B §8 doc-step
slice.

## 💡 Session idea

**Wire `scripts/review_row_check.py` into `quality.yml` as the advisory
owed-row step** — the script shipped slice 14 (2026-07-11) but no workflow
calls it: idea A's §8 named slice (CI wiring) is still open now that
tonight's fastlane-outbox-gate PR (#314) has landed and the workflow is
free again. One advisory (never exit-affecting) step on the full lane that
runs the range check and prints ROW OWED keeps the review-queue ledger
honest without a manager sweep. Worth having because a shipped checker
nobody invokes is drift waiting to happen — the exact hollow-gate class the
pin-map bullet warns about. Deduped against `docs/ideas/backlog.md` + the
queue-state NEXT list: the review-row bullet records the script as shipped
and defers row-APPENDING to the manager, and no bullet covers invoking the
CHECK from CI; `quality.yml` contains zero references to it. Captured in
`docs/ideas/backlog.md`.

## ⟲ Previous-session review

The questions-answer-nag session (PR #299) did well — it closed the exact
promise-break its trigger PR (#297) created, landed the nag in both the
bake advisory and the /questions banner with honest all-paths coverage
(+6 tests), and its 💡 (stamp `closed_at`, turn the nag into an age) is the
natural next rung; what it missed: the nag is print/HTML-only — nothing
machine-readable (the /questions JSON contract) carries the flag, so a
downstream consumer still can't see the debt it renders.
