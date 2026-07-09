# 2026-07-09 — Wire the durable GitHub PAT into the control-plane service

> **Status:** `complete` — token set on `control-plane`, board cells verified live, docs updated; shipped as PR #6 (token-only, based on current `main`; the deploy content it depended on landed separately as PR #3 mid-session).

**What this session is about:** Close the one outstanding owner TODO from the
Railway deploy session — set the durable owner GitHub PAT as the
`control-plane` service's API token so the board's auth-gated cells (actions
secrets, auto-merge, CODEOWNERS enforced) render live instead of `unknown`.
Then update `docs/deployment.md`, `docs/current-state.md`, and the decision
ledger to reflect that the token is now set and the board is fully live.

## What is being done

- Upsert the token as a Railway service variable on `control-plane` in the
  `superbot-websites` project (public GraphQL API, `RAILWAY_API_KEY` only;
  ambient production-bot IDs never passed; no destructive mutation).
- Confirm the variable change triggers a redeploy to SUCCESS.
- Verify live: `/healthz` 200, and the three previously-degraded board cells
  now render real GitHub data.
- Docs: rewrite the `docs/deployment.md` owner-TODO section (token now set),
  close the gap in `docs/current-state.md`, append a decision-ledger entry.

## What was done

- Upserted the durable owner PAT as the `control-plane` service token
  (`variableUpsert` → `true`) via the public Railway GraphQL API,
  `RAILWAY_API_KEY` only; the explicit `superbot-websites` IDs were used, the
  ambient production-bot IDs were never passed, and no destructive mutation
  was called. The value never touched the transcript (built into the JSON
  with `jq --arg` from the env and piped straight to curl).
- Confirmed the variable change auto-redeployed the service to **SUCCESS**
  (deployment `dff92282`, prior one superseded/REMOVED). No manual redeploy
  needed.
- Verified live: `GET /healthz` → 200; `GET /?refresh=1` (Basic auth) → 200
  with the three formerly-`unknown` cells now live — actions secrets show
  real names (`5 secret(s)` on superbot), auto-merge `allowed` + enabler
  state, CODEOWNERS live presence. superbot's CODEOWNERS *enforcement* stays
  `unknown` only because superbot has no CODEOWNERS file (a real state; on
  superbot-next, which has one, enforcement resolves to a real value).
- Docs updated: `docs/deployment.md` (env-var row + owner-TODO section
  rewritten to token-set, plus a token-wired verification block),
  `docs/current-state.md` (gap closed), `docs/decisions.md` ([D-0006]).

## Note on branch hygiene

Built this PR server-side (GitHub API / git plumbing) on top of the current
`main`, not the local branch tip. Two concurrent-worker hazards drove this:
(1) a parallel worker committed an unrelated born-red session log
(`dashboard-botsite-rework-plan`, now open as PR #4) onto the shared local
HEAD mid-session; (2) the deploy content this work depends on landed as PR #3
(squash-merged into `main`) *while this session was running*. An earlier
attempt (PR #5) was branched from the pre-#3 deploy SHA and went divergent
once #3 squash-merged, so it was closed and this token-only PR was rebuilt
cleanly on the post-#3 `main` — no conflicts, no force-push.

## 💡 Session idea

Have the board self-report its own token health: add a tiny top-of-page
badge that calls `GET /rate_limit` with the service token and renders the
authenticated limit (`5000/h`) vs. the unauth `60/h`. It turns "is the PAT
still valid / did it expire?" — today only inferable by eyeballing whether
the secrets cells went back to `unknown` — into one explicit, glanceable
signal on the very board whose job is surfacing config health.

## ⟲ Previous-session review

The railway-deploy session did the hard part well: honest env-var table,
"committed nowhere" provenance on `SITE_PASSWORD`, and a crisp owner-TODO
that made this follow-up almost mechanical. Two misses worth a workflow fix:
(1) its session log was flipped to `complete` claiming "shipped as PR #3,
squash-merged" while the branch was in fact never PR'd or merged — a
`complete` card should assert only what actually happened, so the checker or
a close-out step should verify the merge before the log may claim it; and
(2) leaving the deploy content on an unmerged branch is what let a *second*
parallel session commit onto a shared HEAD and muddy it. **Workflow
improvement:** land each session's PR before the log claims it merged, and
prefer server-side (API) branch creation when multiple agents share one
working tree, so an in-flight branch tip can't be contaminated by a sibling.
