# Deployment — Railway

> **Status:** `living-ledger` — deployed and live since 2026-07-09 (Phase 3 of the kickoff sequence)

The control-plane site runs as a single service in its **own, dedicated
Railway project** — deliberately separate from the production bot project
(`reliable-grace`), which must never be touched by websites work.

## Live deployment

| Thing | Value |
|---|---|
| Railway project | `superbot-websites` |
| Project ID | `70198ece-cbc0-484e-86d9-f8a1eca4f045` |
| Environment | `production` — ID `31485ecd-b3fe-4a8f-b136-337f6f099dc2` |
| Service | `control-plane` — ID `2c840017-a505-4144-b2ff-b2450430a7d9` |
| Domain | https://control-plane-production-abb0.up.railway.app |
| Source | GitHub repo `menno420/websites`, branch `main` (repo-connect) |
| Build | Root `Dockerfile`, auto-detected (python:3.12-slim; first build succeeded 2026-07-09) |
| Deployed at | main @ `73cc501` (PR #2 squash-merge) |

Login: any username + the `SITE_PASSWORD` value (HTTP Basic). The password
is a Railway service variable and is **committed nowhere in this repo** —
the owner holds it.

## Environment variables (names only — values never in the repo)

| Var | Set? | Notes |
|---|---|---|
| `SITE_PASSWORD` | ✅ set (secret) | Site login. Fail-closed: app 503s if unset. |
| `GITHUB_TOKEN` | ✅ set (secret) | Durable owner PAT. Lifts the board onto the authenticated GitHub rate limit and unlocks the auth-gated cells (secret names, auto-merge, CODEOWNERS presence). Value held by the owner, committed nowhere. |
| `PORT` | injected by Railway | Do not set manually. |
| `CACHE_TTL_SECONDS` | not set (default 180) | Optional. |

## GitHub token — set, board fully live

A durable owner PAT is now set as the `control-plane` service token. The
board runs on the authenticated GitHub rate limit, and the previously
degraded, auth-gated cells render live data:

- **actions secrets** → live (real secret **names** per repo).
- **auto-merge allowed** → live (`allowed` + enabler-workflow state).
- **CODEOWNERS** → live (presence per repo; enforcement resolves for repos
  that have a CODEOWNERS file — a repo with no file legitimately shows
  `unknown` for enforcement, which is a real state, not a token gap).

The value is held by the owner and committed nowhere in this repo. The token
is a plain Railway service variable; a change to it triggers a redeploy on
its own, and the board's per-cell degradation still applies to anything the
token's scope or GitHub egress cannot reach — the site never fakes a value.

## How to redeploy

- **Normal path: merge to `main`.** The service is repo-connected to
  `menno420/websites@main`, so every merge auto-builds and auto-deploys.
  There is no manual deploy step.
- **Variable change:** editing a service variable triggers a redeploy on its
  own.
- **Manual nudge (rare):** Railway dashboard → `superbot-websites` →
  `control-plane` → Deployments → Redeploy; or GraphQL
  `serviceInstanceRedeploy` with the service + environment IDs above.
- Healthcheck: `GET /healthz` (unauthenticated, `{"ok":true,...}`).

## Guardrails (binding for agents)

- The agent container carries ambient `RAILWAY_PROJECT_ID` /
  `RAILWAY_SERVICE_ID` / `RAILWAY_ENVIRONMENT_ID` that point at the **live
  production bot** project. **Never pass those to any Railway API call.**
  Use `RAILWAY_API_KEY` alone and the explicit `superbot-websites` IDs above.
- Never call a delete/restore/destructive Railway mutation against anything.
  Misconfigured something? Update it or create a replacement.

## Verification evidence (2026-07-09, first deploy)

- `GET /healthz` → `200` `{"ok":true,"cache_entries":0}`
- `GET /` unauthenticated → `401`
- `GET /` with Basic auth → `200`; board rendered **live** data with no
  GITHUB_TOKEN: superbot head + active rulesets
  (`codeql-merge-protection`, `main-branch-protection`), required check
  `code-quality` 1/1 green, live check runs on main head, 6 open PRs
  (oldest #1761); superbot-next / substrate-kit rows live incl.
  `Kit test suite`, golden-parity.
- `GET /journal/superbot` with auth → `200`, real `.sessions/*.md`
  filenames listed.

## Verification evidence (2026-07-09, token wired)

After the owner PAT was set on `control-plane` (variable upsert → auto-redeploy
to SUCCESS):

- `GET /healthz` → `200`.
- `GET /?refresh=1` with Basic auth → `200`; the auth-gated cells now render
  live GitHub data instead of `unknown`:
  - **actions secrets** — superbot shows `5 secret(s)` with real names
    (`ANTHROPIC_API_KEY, DATABASE_PUBLIC_URL, DATABASE_URL, OPENAI_API_KEY,
    ROUTINE_PAT`); the other repos return live empty lists (`none`).
  - **auto-merge** — superbot `allowed` + `enabler workflow present`;
    other repos `allowed` + `no enabler (merge via API)`.
  - **CODEOWNERS** — live presence per repo (superbot `absent`, superbot-next
    `present` → `not enforced (CI-only-gate model)`). superbot's enforcement
    cell stays `unknown` only because it has no CODEOWNERS file — a real
    state, not a token gap.
