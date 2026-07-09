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
| `GITHUB_TOKEN` | ❌ **not set — owner TODO** | Site runs degraded-but-honest without it (public endpoints, 60 req/h unauth limit). |
| `PORT` | injected by Railway | Do not set manually. |
| `CACHE_TTL_SECONDS` | not set (default 180) | Optional. |

## Owner TODO — mint the GitHub PAT

The board mostly renders live data even without a token (all four repos are
public), but these cells stay degraded until a durable PAT is set as the
service variable `GITHUB_TOKEN` on `control-plane`:

- **actions secrets** → shows `unknown (token lacks admin scope)`
- **auto-merge allowed** → shows `unknown (needs push-scope token)`
- **CODEOWNERS enforced** → shows `unknown`
- plus the unauth rate limit (60 req/h) is tight; the 180 s cache mitigates
  but a token raises it to 5000 req/h.

Minimum scope: `public_repo`/read. Full board: `repo` + `admin:repo` read
(secrets **names**, `allow_auto_merge`, rulesets). Set it in Railway →
project `superbot-websites` → service `control-plane` → Variables; the
service redeploys automatically on variable change.

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
