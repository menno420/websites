# 2026-07-09 — engage the substrate-kit machinery

> **Status:** `complete` — PR #16. Contained, reversible, forward-only.

- **📊 Model:** claude-opus-4-8 (pre-v1.2.0 backfill; builder-session subagent, inherited — not independently confirmed)

## What this session did

The kit adoption (PR #1) was ritual-clean but never engaged: the planted binding
docs still carried `UNRENDERED SLOTS` banners, no CI ran the kit check,
`session_count` sat at 0 after ~9 sessions, the journal was an empty template,
and some bookkeeping never landed. This session turned the machinery live.

1. **Rendered the 8 banner docs for real.** Filled `architecture_layers`,
   `ownership_model`, `new_area_ownership`, `mutation_seam`, `drift_resolution`,
   `staleness_review`, `owner_profile`, `review_ritual` from the actual project
   (via `bootstrap answer` + `bootstrap render --live`); removed every
   UNRENDERED-SLOTS banner. Hand-filled the load-bearing structural placeholders
   (architecture layer table + invariants, ownership table, runtime lifecycle +
   failure modes, CONSTITUTION project rails) so the binding docs are live, not
   shells.
2. **Installed the kit CI gate** `.github/workflows/quality.yml` — Python 3.12,
   installs all three services' deps, runs `bootstrap.py check --strict
   --require-session-log` (born-red gate mode) plus the app/botsite/dashboard
   pytest suites, on PRs and pushes to `main`.
3. **Backfilled bookkeeping** — retro card for PR #10
   (`2026-07-09-dashboard-stub-denylist.md`, marked backfill); added PRs
   #4/#10/#13/#15 to `current-state.md` Recently-shipped.
4. **Routed the 7 rework-plan open questions** into `docs/question-router.md` as
   Q-0001..Q-0007 (bidirectional cross-link with the plan; decisions referenced
   by ledger, not bare `D-NNNN` tokens, to keep stamp discipline).
5. **Engaged the kit session loop** — `session-close` mined reflections +
   rebuilt `.substrate/episodic_index.json` (12 logs); reconciled `session_count`
   0 → 12 to match the indexed logs. Vendored `bootstrap.py` is byte-identical to
   substrate-kit `dist/` HEAD, so no engine bump (deferred/none needed).
6. **Seeded `.session-journal.md`** with a real quick-reference (run each app,
   tests, kit check, Railway facts, docs map).
7. **Recorded [D-0013]** for the kit-engagement pass.

Verify: `python3 bootstrap.py check --strict` green; 60 tests green across all
three suites.

## 💡 Session idea

Add a **ledger-parity sub-check to `bootstrap.py check`**: compare the highest
merged PR number (from git) against the newest PR referenced in
`current-state.md`'s Recently-shipped list, and warn when they diverge by more
than one or two. Every backfill this session did (PRs #4/#10/#13/#15) existed
because nothing *enforced* that a merge lands a ledger entry — a five-line check
would make the "keep the ledger current" rhythm self-catching, the same way the
new CI gate makes the session-log ritual self-catching. It is the exact guard
two prior session reviews already wished for; worth its own small PR.

## ⟲ Previous-session review (PR #14/#15 — gated /owner area + deploy evidence)

Strong work: the gated `/owner` overlay kept the public site byte-identical while
adding real power, with tests asserting zero secret names in the public output
*and* their presence in the authed view — exactly the right invariant to lock
down, and the deploy evidence (#15) was captured verbatim. What it left for this
session to clean up: like every session since #8, it shipped without noticing
that the *kit itself* was never engaged — the docs it relied on for orientation
still had raw `${...}` slots. Concrete system improvement (now shipped): the CI
gate + born-red card convention were purely exhortative before today; a session
could merge with template-shell docs and no session log. Wiring
`check --strict --require-session-log` into Actions converts both from "please
remember" into "the door is locked" — the friction→guard move the collaboration
model calls for.

## 📤 Run report

- **Did:** rendered 8 binding docs live; installed the kit CI gate; backfilled
  PRs #4/#10/#13/#15 + a #10 retro card; routed 7 open questions to the router;
  engaged the session loop (count 0→12); seeded the journal; recorded D-0013 ·
  **Outcome:** shipped (PR #16)
- **⚑ Self-initiated:** hand-filling the binding docs' structural tables
  (layers/ownership/lifecycle/rails) beyond the raw slots; reconciling
  `session_count` to the indexed-log count; the journal candidate-rule +
  ledger-parity session idea
- **↪ Next:** make the new `quality` workflow a **required** check on `main`
  (owner/token-scope permitting); consider the ledger-parity sub-check above
