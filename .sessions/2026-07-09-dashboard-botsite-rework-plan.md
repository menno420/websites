# 2026-07-09 — Dashboard + botsite rework plan (PLAN ONLY)

> **Status:** `in-progress` — drafting the step-3 rework plan; no implementation in this PR.

**What this session is about:** Sequence step 3 of the websites kickoff — the
deferred rework of superbot's two existing web properties (`dashboard/`,
`botsite/`) into this repo. Per the kickoff, this step is *plan-first*: describe
the plan before any rework begins. Deliverable is a single
`docs/planning/` doc plus a ledger entry + a `current-state.md` pointer — **no
code ported, no live site touched**.

## Plan (what this commit opens)

- Read `dashboard/` and `botsite/` source in `menno420/superbot` (read-only) to
  describe accurately what each does today.
- Read this repo's control-plane app (`app/`), `docs/site.md`,
  `docs/deployment.md`, `docs/decisions.md`, `docs/current-state.md` to plan the
  rework so it fits *alongside* the live control-plane site.
- Write `docs/planning/dashboard-botsite-rework-plan-2026-07-09.md`:
  what-each-does-today (cited to real files), carry-over-vs-rebuild tables,
  fit-alongside recommendation, migration/deploy order, open questions.
- Add [D-0006] to `docs/decisions.md` (plan drafted, awaiting owner review) and
  reference the plan from `docs/current-state.md` next steps.
