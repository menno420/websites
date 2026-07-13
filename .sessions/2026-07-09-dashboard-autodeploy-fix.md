# 2026-07-09 — Fix dashboard flaky auto-deploy (missing GitHub trigger)

> **Status:** `complete` — root cause found + fixed non-destructively via Railway API; this PR is the live end-to-end proof that the dashboard now auto-deploys on merge to `main`.

- **📊 Model:** Claude Opus 4.8 (pre-v1.2.0 backfill; builder-session subagent, inherited — not independently confirmed)

**What this session was about:** The dashboard Railway service's auto-deploy-on-merge
was flaky — it missed merges twice and needed a manual pinned-SHA redeploy — while
control-plane and botsite (same repo `menno420/websites`, same project
`superbot-websites`) auto-deploy reliably. Find the root cause, fix it non-destructively
if possible, and prove it.

## Root cause (evidence)

The dashboard service had **no GitHub deployment trigger at all**, and its
`serviceInstanceAutoDeployStatus.enabled` was `false`. control-plane and botsite each
had a `provider: github`, `repository: menno420/websites`, `branch: main` deployment
trigger and `enabled: true`.

Evidence from the Railway GraphQL API (`backboard.railway.com/graphql/v2`):

- `deploymentTriggers` — control-plane: 1 github/main trigger; botsite: 1 github/main
  trigger; **dashboard: `edges: []` (none)**.
- `serviceInstanceAutoDeployStatus` — control-plane `enabled:true`, botsite
  `enabled:true`, **dashboard `enabled:false` (`canEnable:true`)**.
- Deployment records: control-plane and botsite got a `reason:deploy` deployment for
  **every** commit to `main` (15/15, identical timestamps + commit hashes, in lockstep).
  The dashboard only deployed a handful of times with large gaps, and its most recent
  deploy (`791380c2`, 13:32) was the owner's manual pinned-SHA redeploy.
- `watchPatterns` were empty for all three and `source.repo` was identical, so the cause
  was **not** a watch-path filter or a source misconfiguration — it was the absent trigger.

Hypothesis (b) confirmed (mis-wired / never-fully-connected GitHub push trigger for the
dashboard service); hypotheses (a) watch-path, (c) wait-for-CI, and (d) race were rejected
by the config + deployment evidence above (`checkSuites:false` on the working triggers;
identical empty `watchPatterns`).

## Fix (non-destructive, dashboard service only)

Created the missing trigger via `deploymentTriggerCreate`, matching control-plane/botsite
exactly:

- before → dashboard: **no trigger**, auto-deploy `enabled:false`
- after  → dashboard: trigger `6bc63516-b290-4f37-9b25-b155be077cde`
  (`github` · `menno420/websites` · `main` · `checkSuites:false`), auto-deploy
  `enabled:true`

Reversible (`deploymentTriggerDelete` exists). No other service or project touched; the
ambient production-bot Railway IDs were never passed to any call; no destructive mutation
was made.

## Proof

The new `dashboard/DEPLOY_TRIGGER.md` file in this PR causes a real `main` update on merge.
The trigger is expected to fire a fresh dashboard deployment automatically (no manual
`serviceInstanceDeployV2`) within minutes. Deployment id + trigger source recorded on the
run report.

## 💡 Session idea

Add a tiny "trigger present?" cell to the deploy-state row of the board: the app already
knows its own SHA vs live `main`; a companion check that each websites service has a
`deploymentTriggers` edge would have caught this silently-missing trigger the moment it
went absent, instead of after two missed merges.

## ⟲ Previous-session review

The ORDER 001 / deploy-drift session correctly *noticed* the dashboard lag and worked
around it with a manual pinned-SHA redeploy, and honestly logged the drift — good
transparency. What it missed was the *why*: it treated the symptom (behind `main`) with a
one-off redeploy rather than checking whether the service even had a push trigger, so the
flakiness would have recurred on the next merge. Workflow improvement: the board's
deploy-state drift cell should distinguish "build failed after a merge" from "no deploy was
ever triggered" — the two have different fixes, and this session's missing-trigger class is
invisible to a SHA-comparison cell alone.
