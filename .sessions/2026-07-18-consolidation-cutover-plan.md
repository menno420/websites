# 2026-07-18 — Site-consolidation cutover plan + prose f027→fc91 corrections

> **Status:** `complete` — branch `claude/consolidation-cutover-plan`,
> PR **#410**. Wrote the owner-reviewable URL-cutover plan for the
> duplicate-sites consolidation (retire the `reliable-grace` website duplicates
> + the old `menno420/superbot` sites, KEEP the `superbot-websites` estate,
> move the URLs), sequenced lowest-risk-first with a rollback per step and a
> hold-for-owner gate on every destructive action; PLUS correcting the last
> prose/URL references that still named the retire target (`f027`) as the
> canonical review service — corrected to the KEEP service (`fc91`), matching
> #407's un-inverted ground truth.

- **📊 Model:** Claude Opus 4.8 · high · docs-only

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

**A prose-lint that flags a retire-target domain named without a
retire/dup/old label.** #407's ground-truth pin catches an inverted
canonical/duplicate mapping in the *structured* files (`web_presence.json`,
`environments.json`, `config.py`, the healthcheck tables), but every residual
`f027`-as-canonical reference this session corrected lived in *free prose*
(`CONSTITUTION.md`, `docs/current-state.md`, `docs/owner/OWNER-ACTIONS.md`,
`review/ai.py`'s system prompt, a tester-task URL) — unpinned, so they survived
the code fix. A small advisory checker that scans committed docs/strings for a
known retire-target domain (`review-production-f027`, `superbot-app`,
`superbot-dashboard`) and flags any occurrence not within N tokens of a
retire/dup/old/superseded label would turn "prose still names the retired
service as canonical" into a check finding instead of a human-spotted
follow-up. Deduped against `docs/ideas/backlog.md` + the NEXT list: distinct
from the two consolidation entries there (the structured-file ground-truth pin
from #407, and the redirect-path coverage test) — this guards the prose layer
neither covers. Captured in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

`.sessions/2026-07-18-fleet-prompt-staleness.md` (PR #408) shipped a clean
truth-in-labeling fix for the /owner "Prompt state" panel — it correctly
diagnosed that the panel reads the fleet-manager failsafe snapshot LIVE and is
honest, and that the real staleness is an upstream frozen `captured_at`; adding
the snapshot AGE + a `>24h stale, awaiting an upstream refresh` warning against
the injectable `app.clock` (not naive wall-clock) was exactly right, and routing
the underlying data refresh to the manager via 4 cross-repo outbox asks kept the
fix in-scope instead of reaching across repos. The one thing to watch: the panel
now depends on that upstream refresh actually happening — if the manager seat
stays parked the warning becomes permanent furniture, so the self-healing
per-seat stamp-at-session-ender ask (Part B) is the load-bearing follow-up, not
an optional extra.
