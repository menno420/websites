# 2026-07-18 — Site-consolidation cutover plan + prose f027→fc91 corrections

> **Status:** `in-progress` — branch `claude/consolidation-cutover-plan`,
> PR **[[fill:PR#]]**. Writing the owner-reviewable URL-cutover plan for the
> duplicate-sites consolidation (retire the `reliable-grace` website duplicates
> + the old `menno420/superbot` sites, KEEP the `superbot-websites` estate,
> move the URLs), sequenced lowest-risk-first with a rollback per step and a
> hold-for-owner gate on every destructive action; PLUS correcting the last
> prose/URL references that still named the retire target (`f027`) as the
> canonical review service — corrected to the KEEP service (`fc91`), matching
> #407's un-inverted ground truth.

- **📊 Model:** [[fill:model line]]

**What this session is about:** #407 un-inverted the canonical/duplicate service
inventory in code+data+tests (KEEP = `superbot-websites`
`abb0`/`a91b`/`cfd7`/`fc91`; RETIRE = `reliable-grace` `f027` +
`menno420/superbot` `superbot-dashboard`/`superbot-app`; NEVER the Discord
`worker` or the Postgres DBs). Two follow-ups remained: (1) there is no written,
owner-reviewable cutover plan for actually moving the URLs and retiring the
olds; (2) a handful of prose/URL references still presented `f027` as the
canonical review site. This session ships the plan doc
(`docs/plans/site-consolidation-cutover.md`) and corrects the remaining prose.

## What will be done

- **Part A — cutover plan doc** (`docs/plans/site-consolidation-cutover.md`):
  summary, keep-vs-retire inventory table, cutover steps sequenced
  review → botsite → dashboard (repoint references → optional pretty-name
  reclaim → GATED destructive retirement), a rollback per step, a live-probe
  verification section, and an explicit "nothing here is executed — destructive
  steps await the owner's explicit go" marker.
- **Part B — prose/URL corrections** (`f027` → `fc91`, canonical review only):
  `CONSTITUTION.md`, `docs/current-state.md`, `docs/owner/OWNER-ACTIONS.md`,
  `docs/eap-closeout-walkthrough-2026-07-14.md`,
  `docs/plans/discovery-inventory.md`, `review/data/evidence/01-provenance.md`,
  `review/ai.py`, `botsite/testing_tasks.json`. The intentional old/dup/retire
  references (`review-dup-f027` in the registries, the healthcheck/dashboard
  "NOT the f027 old copy" comments, the tests asserting f027 is not canonical,
  and the fence note about the retire target) are left as-is, correctly labeled.

⚑ Self-initiated: no — coordinator-dispatched consolidation-track follow-up
(the cutover plan-doc + the residual prose corrections #407 flagged).

## 💡 Session idea

[[fill:idea]]

## ⟲ Previous-session review

[[fill:previous-session review]]
