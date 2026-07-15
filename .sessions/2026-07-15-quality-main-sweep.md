# 2026-07-15 — quality-main-sweep: backfill missing quality runs on main

> **Status:** `complete` — PR #345, branch `claude/quality-main-sweep-20260715`;
> `.github/workflows/quality-main-sweep.yml` added (scheduled sweep, every 2h,
> dispatches quality.yml on an unmeasured main HEAD).

- **📊 Model:** Claude Fable · medium · feature build (scheduled CI sweep workflow)

**What this session was about:** the reboot-truing baton
(`.sessions/2026-07-15-reboot-truing.md`, next-session item 1) flagged that
main HEAD commits landed by github-actions[bot] merges get **no push-event
`quality` run** — the GITHUB_TOKEN recursion guard suppresses the push
event, so the 4 commits after `214ed0f` (ee47f8d, 6fafc1a, 68ad331,
3cac461) carry no quality check and main health is unmeasured between
merges. This slice adds a host-owned scheduled sweep workflow
`.github/workflows/quality-main-sweep.yml` that detects a main HEAD with no
completed `quality` check run and dispatches `quality.yml` on main —
mirroring the repo's documented recursion-guard exception (review-bake's
GITHUB_TOKEN `workflow_dispatch` chain, already documented in
`quality.yml`'s `on:` block).

⚑ Self-initiated: yes — contained, reversible, from the previous session's
baton (decide-and-flag).

## Close-out

**Evidence:**

- files touched this branch: `.sessions/2026-07-15-quality-main-sweep.md` +
  `control/claims/claude-quality-main-sweep-20260715.md` (first commit; the
  claim deleted at this flip), `.github/workflows/quality-main-sweep.yml`
  (the whole slice — `quality.yml` needed NO edit: it already carries the
  `workflow_dispatch` trigger from the review-bake chain).
- git: branch `claude/quality-main-sweep-20260715`, based on `main` @
  `f79c3ec`; PR #345.
- verify: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — **1414 passed, 1 warning**; `python3 bootstrap.py
  check --strict` — green except the DESIGNED born-red hold on this card
  (released by this flip); YAML parse of the new workflow OK
  (`yaml.safe_load`). The sweep's dispatch path itself is only provable
  live (schedule + `workflow_dispatch` on main after merge) — first
  scheduled firing is the real end-to-end check.

**Judgment:**

- Decisions made: (1) API-only job, no checkout — least-privilege
  `permissions: actions: write, checks: read`, nothing to run locally;
  (2) three-way idempotence: completed quality run → "quality present"
  exit 0, run in flight → no duplicate dispatch, none → dispatch once;
  (3) cron `17 */2 * * *` — every 2h off the top-of-hour rush.
- Next session should know: after the first bot merge post-merge of #345,
  confirm the sweep actually dispatches (Actions → quality-main-sweep run
  log should show either "quality present" or a dispatch line, and main
  HEAD should gain a `quality` check run within ~2h). Baton item 2 from
  the reboot-truing card (re-verify the 9 open ⚑ asks in
  `docs/owner/OWNER-ACTIONS.md`) remains untouched.

## 💡 Session idea

**Sweep coverage for skipped-over main commits** — the sweep only measures
the CURRENT main HEAD: a bot-merged commit that is HEAD for less than the
2-hour sweep window and then gets buried by the next merge stays unmeasured
forever (exactly the ee47f8d/6fafc1a/68ad331 shape — three of today's four
gap commits were already non-HEAD by the time any sweep could have fired).
A walk-back variant — scan `repos/.../commits?sha=main` newest-first until
the first sha with a completed quality run, then dispatch on the newest
unmeasured sha and record the still-buried ones — would make the health
ledger gap-free instead of HEAD-sampled. Worth having because "main is
green" claims in state docs cite the latest run; a buried red commit
(revert-then-fixed) would never surface. Deduped against
`docs/ideas/backlog.md`: no quality-run-coverage or unmeasured-commit
bullet exists (the sweep/backfill hits there are env-shape and card-format
sweeps, unrelated).

## ⟲ Previous-session review

`.sessions/2026-07-15-reboot-truing.md` handed this session its entire
brief: its "Next session should know" baton named the exact four
unmeasured shas and the `214ed0f` boundary, so this slice started at
implementation instead of re-deriving the gap from run history — a clean
demonstration of the baton pattern working. One workflow improvement it
points at: that card's verify note ("green except the DESIGNED born-red
hold") and this card's are near-identical boilerplate; the kit could stamp
the born-red-hold line into the close-out auto-draft so card authors stop
hand-copying it (adjacent to, but distinct from, that card's merge-base
auto-evidence 💡).
