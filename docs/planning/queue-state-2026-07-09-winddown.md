# websites — queue state at gen-1 wind-down (2026-07-09)

> **Status:** `plan` — the gen-2 handover ledger, written by the gen-1 wind-down session so the
> gen-2 Project boots from `main` alone. Everything that lived only in chat or
> session state is settled here: what is DONE, what was IN-FLIGHT, what is NEXT.
> Source code and merged PRs win over this file; verify live state against
> GitHub and the deployed services before acting.

## Why this doc exists

The lane is moving gen-1 → gen-2. A fresh Project has no chat history — its
whole inheritance is this repo. This doc is the queue snapshot at the handover
boundary (main head `ab0995d`, PR #45).

## DONE — the gen-1 build (45 PRs, all terminal)

Full narrative: `docs/current-state.md` (Recently shipped) and
`docs/retro/project-review-2026-07-09.md`. Condensed milestones:

- **Foundation:** substrate-kit adopted (#1), control-plane site built (#2),
  deployed to fresh Railway project `superbot-websites` (#3), rework plan (#4),
  owner PAT wired (#6).
- **Three live public services:** botsite (#7), dashboard (#8, polish #10/#11),
  auth dropped + secrets masked (#12/#13), gated `/owner` area (#14/#15).
- **Workflow hardening:** kit machinery engaged (#16/#17), journal
  search/mobile (#18), Railway-ID guard + healthcheck + stub labels + OWNER-ACTIONS
  (#19/#20), botsite content depth (#21), born-red gate leak fixed via kit
  v1.0.0 (#24).
- **Fleet coordination era:** control protocol adopted (#23/#25), ORDER 001
  deploy-drift cell + `/version` (#26–#28), dashboard auto-deploy trigger
  root-caused + fixed (#29/#30), kit v1.2.0 (#31), `/activity` + `/ideas`
  (#33/#34), ORDER 002 `/fleet` page (#35), manifest live-parse (#36),
  auto-refresh + CI audit (#37), ORDERS 003+004 retro + Model backfill
  (#38–#40), `/activity.xml` Atom feed (#41), ORDER 006 ping-ack (#43/#44),
  kit v1.6.0 upgrade (#45).
- **Closed without merge (superseded/duplicate, parallel-checkout churn):**
  #5, #9, #22.

## IN-FLIGHT — nothing

Verified 2026-07-09 (this session, via the GitHub API): **zero open PRs** on
`menno420/websites`. No unmerged work is stranded on branches. The working
tree at wind-down matched `origin/main` exactly.

## NEXT — agent-executable queue (in priority order)

1. ~~**ORDER 005**~~ — **DONE 2026-07-10** (claimed via PR #52
   `claimed-by: 005 gen2-order-005 2026-07-10T02:24Z`; built + shipped as
   PR #53; decision stamped in `docs/site.md` + the decision ledger): `/queue` (deduplicated owner to-do surface over every
   lane's `⚑ needs-owner` + the fleet-manager owner-queue) and
   `/environments` (fleet-manager `environments/` registry render with
   copy-to-clipboard), both with honest not-configured/unavailable
   degradation while `GITHUB_TOKEN` stays unset in production. ORDER 007
   step 4 (`scripts/env-setup.sh` wrapper) landed in the same PR.
2. **`/fleet` manifest-parse smoke check** (retro A3): assert the live
   manifest parse yields a non-empty lane set so a manifest reformat surfaces
   as an alert instead of a silent fallback.
3. **`.sessions/` card template** carrying the `📊 Model: <model> · <effort> ·
   <task>` line + ender checklist, so no future grandfather backfill (the
   ORDER 004 class) is ever needed.
4. **Heartbeat enrichment** (retro G3): machine-readable outstanding-orders
   field, deployed-sha / last-verified-live per lane in `control/status.md`,
   so `/fleet` computes "what's left" without diffing inbox vs status vs git.
5. **Idea backlog** (`docs/ideas/`): `/activity` per-repo filter
   (`activity-per-repo-filter-2026-07-09.md`); kit-version rollup badge on
   `/fleet` (idea recorded in `.sessions/2026-07-09-kit-upgrade-v1.6.0.md`);
   "unseen orders?" badge on `/fleet` (inbox last-commit newer than status
   `updated:` — recorded in the same card's ⟲ review).

## NEXT — owner-gated (decisions/actions, not agent work)

Canonical list: `docs/owner/OWNER-ACTIONS.md` (6 open forks: /admin control
API, /submit Postgres, redeploy hook, custom domains, restyle-vs-v1, old-site
cutover) plus the two active six-field OWNER-ACTION asks in
`control/status.md` (provision the submissions Postgres `DATABASE_URL`; mint
a durable fine-grained `GITHUB_TOKEN` PAT for the control-plane service).
Exact click paths: `docs/retro/project-review-2026-07-09.md` § (e).

## Gen-2 boot pointers

Read in order: `.claude/CLAUDE.md` → `docs/current-state.md` →
`docs/CAPABILITIES.md` (verified walls: branch deletion 403, rulesets-API
proxy 403, api.github.com blocked → MCP only) → `docs/AGENT_ORIENTATION.md` →
`control/README.md` (inbox/status ritual; **orders stay `status: new` forever
— diff `inbox.md` against your own `status.md` `done=` line, never infer
execution from a PR title**) → `docs/retro/self-review-2026-07-09.md` (gen-1's
lived friction, the redesign payload).
