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

**Public main site + one gated `/owner` area.** Every route *except* `/owner*`
serves without credentials; the public board masks the one non-public datum, the
GitHub Actions secret *names*, to a **count** (see below). The single gated
corner is the `/owner` area (`app/owner.py`, HTTP Basic on `SITE_PASSWORD`): it
un-masks the secret names and exposes privileged actions (cache refresh, re-run
failed CI). No credentials on `/owner*` → 401; `SITE_PASSWORD` unset → `/owner*`
fails closed 503 while the public site keeps serving.

## Environment variables (names only — values never in the repo)

| Var | Set? | Notes |
|---|---|---|
| `SITE_PASSWORD` | ✅ set (secret) | Gates ONLY the `/owner` area (HTTP Basic, any username). The public site never reads it. If unset, `/owner*` fails closed 503 and the public site still works. Value held by the owner, committed nowhere. |
| `GITHUB_TOKEN` | ✅ set (secret) | Durable owner PAT. Lifts the board onto the authenticated GitHub rate limit and unlocks the admin-scope cells (secret **count**, auto-merge, CODEOWNERS presence). Value held by the owner, committed nowhere. |
| `PORT` | injected by Railway | Do not set manually. |
| `CACHE_TTL_SECONDS` | not set (default 180) | Optional. |

## GitHub token — set, board fully live

A durable owner PAT is set as the `control-plane` service token. The board runs
on the authenticated GitHub rate limit, and the admin-scope cells render live
data:

- **actions secrets** → live **count only** (`N secret(s)`). The individual
  secret **names** are never rendered or serialized — they are the one
  admin-scope-only datum on this now-public board (auth-drop decision); the raw secrets
  API response is not carried into `/api/readiness.json` either.
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
- Healthcheck: `GET /healthz` (`{"ok":true,...}`).

> **Both websites services (`control-plane` and `dashboard`) are PUBLIC** since the
> 2026-07-09 auth-drop — the Basic-auth gate was dropped from both. `botsite` was already
> public. The redeploy path is identical for all three: merge to `main`
> auto-builds and auto-deploys; if a service lags, nudge it (below).

## Guardrails (binding for agents)

> ## 🚨 NEVER pass the three ambient production-bot Railway IDs to any call 🚨
>
> The agent container carries ambient **`RAILWAY_PROJECT_ID`** /
> **`RAILWAY_SERVICE_ID`** / **`RAILWAY_ENVIRONMENT_ID`** that point at the
> **LIVE PRODUCTION BOT** project. **Never pass any of them to any Railway
> API/CLI call.** Use `RAILWAY_API_KEY` alone plus the explicit
> `superbot-websites` IDs in the table above. Full rule + the enforcing guard:
> **`docs/RAILWAY-SAFETY.md`** (checked in CI by
> `scripts/check_no_ambient_railway_ids.py`, wired into `quality.yml`).

- This repo's services make **no Railway API calls at all** — no Railway SDK, no
  `RAILWAY_API_KEY` in any app env, no deploy hook. The guard
  `scripts/check_no_ambient_railway_ids.py` fails CI if any tracked code ever
  starts reading one of the three ambient IDs from the environment.
- Never call a delete/restore/destructive Railway mutation against anything.
  Misconfigured something? Update it or create a replacement.

## Post-deploy verification (habit)

Merge = deploy — each service auto-redeploys on merge to `main`. After a merge,
run the reusable 3-URL healthcheck:

```
python3 scripts/healthcheck.py
```

It GETs `/healthz` and `/` on all three live services (`control-plane`,
`botsite`, `dashboard`), prints a PASS/FAIL table, and exits non-zero if any is
down. All three are **public**, so `/` is expected `200`. Verbatim output on
2026-07-09: all six endpoints `200` / `PASS`, `RESULT: all healthy`.

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
  - **actions secrets** — superbot showed `5 secret(s)`; the other repos
    returned live empty lists (`none`). (Historically this cell listed the
    secret names; since the 2026-07-09 auth-drop the board masks them to a
    count — the names are never rendered or serialized.)
  - **auto-merge** — superbot `allowed` + `enabler workflow present`;
    other repos `allowed` + `no enabler (merge via API)`.
  - **CODEOWNERS** — live presence per repo (superbot `absent`, superbot-next
    `present` → `not enforced (CI-only-gate model)`). superbot's enforcement
    cell stays `unknown` only because it has no CODEOWNERS file — a real
    state, not a token gap.

## Verification evidence (2026-07-09, auth dropped — both sites public)

Local (both apps run **without** `SITE_PASSWORD` set):

- control-plane `GET /healthz` → `200`; `GET /` → `200` with **no**
  `www-authenticate` header; served board HTML contained no secret names.
- dashboard `GET /healthz` → `200`; `GET /` and `GET /commands` → `200` with no
  auth; `GET /admin` still renders the "requires owner wiring" stub.
- `tests/test_app.py` (8) + `dashboard/tests/test_dashboard.py` (29) green,
  including the new assertion that a secret name (`ANTHROPIC_API_KEY`) is absent
  from the served board HTML and `/api/readiness.json`.

Live production (after PR #12 merged to `main` @ `f6628fe`):

- **Deploy method** — `control-plane` **auto-deployed** the merge on its own
  (repo-connect; latest deployment `SUCCESS` on `f6628fe` within a minute of the
  merge). `dashboard` **lagged** (the known auto-deploy lag for these services), so
  it was redeployed **pinned to the merged SHA** via `serviceInstanceDeployV2`
  (`commitSha=f6628fe`) → `SUCCESS`. Both non-destructive; `RAILWAY_API_KEY` +
  explicit `superbot-websites` IDs only; ambient production-bot IDs never passed.
- **control-plane** — `GET /healthz` `200`; `GET /` `HTTP/2 200` with **no** auth
  and **no** `www-authenticate`; `grep -c ANTHROPIC_API_KEY` on the served `/`
  HTML = `0` (also 0 for `ROUTINE_PAT` / `OPENAI_API_KEY` / `DATABASE_PUBLIC_URL`);
  the board shows `5 secret(s)` and real public data (`superbot-next`,
  `Kit test suite`).
- **dashboard** — `GET /healthz` `200`; `GET /` `HTTP/2 200` with no auth;
  `/commands` renders real data (`!daily`, `!shop`, `Economy`); `/admin` still
  shows the "requires owner wiring — not connected to the live bot" stub.

## Verification evidence (2026-07-09, gated `/owner` area added)

PR #14 (`claude/owner-area`) merged to `main` @ `71a8ca1`. **Deploy method:**
`control-plane` **auto-deployed** the merge (repo-connect) — the new deployment
built and reached `SUCCESS` on `71a8ca1` on its own (polled via
`serviceInstanceDeployV2`-style `deployments` query; no manual nudge needed).
Non-destructive; `RAILWAY_API_KEY` + explicit `superbot-websites` IDs only;
ambient production-bot IDs never passed; **no `RAILWAY_API_KEY` added to the app
env, no destructive mutation.**

Live evidence (captured verbatim from
`https://control-plane-production-abb0.up.railway.app`):

- **public `/` (no auth)** → `200`, **no** `www-authenticate`; `grep -c
  ANTHROPIC_API_KEY` on the served HTML = **0**; board shows `5 secret(s)`
  (count only). Public `/api/readiness.json` → `200`, `ANTHROPIC_API_KEY` count
  **0**. **Public masking NOT regressed.**
- **`/owner` no creds** → `401`.
- **`/owner` with `SITE_PASSWORD`** (any username) → `200`; the served HTML
  **contains** the real secret names — `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`,
  `ROUTINE_PAT`, `DATABASE_URL`, `DATABASE_PUBLIC_URL`, `SITE_PASSWORD`.
  Authed `/owner/api/readiness.json` → `200` with a `names` array carrying
  `ANTHROPIC_API_KEY`.
- **`POST /owner/actions/refresh`** (authed) → `200`, banner
  `cache cleared — 40 entries dropped; the board below is re-fetched live`.
- **`POST /owner/actions/rerun-ci`** — unauthed → `401` (gated); `GET` on the
  route → `405` (route exists, POST-only). Wired + reachable; a real re-run was
  deliberately **not** fired during verification (it is a live write).
- **`/healthz`** → `200` `{"ok":true,...}`.

The `/owner` gate uses `SITE_PASSWORD` (already set on the service since the
auth-drop); no new production credential was introduced. Railway account-token
actions and any live production-bot control API remain **unwired** by design
(separate owner approval).
