# 2026-07-09 — Dashboard + botsite rework plan (PLAN ONLY)

> **Status:** `complete` — plan doc shipped as PR #4 (`claude/dashboard-botsite-rework-plan`); no implementation, live sites untouched.

- **📊 Model:** Claude Opus 4.8 (pre-v1.2.0 backfill; builder-session subagent, inherited — not independently confirmed)

**What this session was about:** Sequence step 3 of the websites kickoff — the
deferred rework of superbot's two existing web properties (`dashboard/`,
`botsite/`) into this repo. Per the kickoff, this step is *plan-first*: describe
the plan before any rework begins. Deliverable is a single `docs/planning/` doc
plus a ledger entry + a `current-state.md` pointer — **no code ported, no live
site touched**.

## What was done

- Read `dashboard/` and `botsite/` source in `menno420/superbot` (read-only):
  both READMEs, `app.py` / `auth.py` / `requirements.txt` / `Procfile`, and the
  template / site / ds / console / data directory listings — enough to describe
  each site accurately, cited to real paths.
- Read this repo's control-plane app (`app/main.py`, `app/config.py`, Dockerfile,
  requirements) + `docs/site.md` / `deployment.md` / `decisions.md` /
  `current-state.md` to plan a fit *alongside* the live site.
- Wrote `docs/planning/dashboard-botsite-rework-plan-2026-07-09.md`:
  what-each-does-today, carry-over-vs-rebuild tables per site, a
  one-repo/multi-Railway-service fit-alongside recommendation, botsite-first
  migration order + rollback thinking, and seven open questions for the owner.
- Recorded [D-0007] in `docs/decisions.md`; referenced the plan from
  `docs/current-state.md` (In flight + Next steps).

## Parallel-session note (a real snag, handled)

This branch was cut while a concurrent **wire-github-token** session shared the
working tree; the branch's base commit included that session's in-flight born-red
log and its uncommitted D-0006 was in the tree. Handled forward-only, without
force-push and without disturbing the other session: removed the inherited stray
log from this branch in its own commit, took **D-0007** (not D-0006) for this
session's decision, and made all ledger edits via the GitHub API so the shared
working tree and the other session's uncommitted work were never touched.

## 💡 Session idea

When the rework lands, the readiness board should grow a **"sites" row group** —
one row per deployed website service (control-plane, botsite, dashboard) showing
live `/healthz` + `deployed-SHA == main?` — so the same board that watches repo
config also watches the estate's own web surfaces. It closes the loop: the
oversight site oversees itself and its siblings.

## ⟲ Previous-session review

The railway-deploy session set the standard this one leaned on: it put the
Railway IDs, env-var names, and the owner-TODO into `docs/deployment.md` as
durable repo state rather than a scratchpad note, which is exactly why this
session could cite the project ID and deploy model confidently without
re-deriving them. One workflow improvement this session surfaced: the repo has no
guard against a branch being cut on top of a *parallel* session's in-flight
commit (the stray-file snag above). A cheap future guard — a session-close check
that the branch's merge-base is `origin/main` and its net diff touches only files
this session's log claims — would turn that silent cross-session bleed into a
visible warning before PR.
