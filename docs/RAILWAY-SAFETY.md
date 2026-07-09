# ⚠️ Railway safety — the ambient production-bot IDs are radioactive

> **Status:** `binding`
>
> Read this before any Railway operation. Enforced by
> `scripts/check_no_ambient_railway_ids.py` (wired into `quality.yml`).

## The one rule

> ## 🚨 NEVER pass these three ambient IDs to any Railway API/CLI call 🚨
>
> The agent container carries three ambient environment variables:
>
> - **`RAILWAY_PROJECT_ID`**
> - **`RAILWAY_SERVICE_ID`**
> - **`RAILWAY_ENVIRONMENT_ID`**
>
> **They point at the LIVE PRODUCTION BOT project.** Passing any of them to a
> Railway GraphQL call, a `railway` CLI invocation relying on ambient linkage,
> or any deploy/mutation payload operates on **production**. That is exactly the
> mistake this repo is built to make impossible.

## Why this repo is safe by construction

The websites services (`control-plane` / `botsite` / `dashboard`) make **no
Railway API calls at all**. They read GitHub over HTTPS and render HTML — no
Railway SDK, no `RAILWAY_API_KEY` in any app env, no deploy hook wired. So the
*only* way one of those three ambient IDs could reach a Railway mutation is if
someone wired new code that reads it. The guard below makes that a hard failure.

## The enforcing guard

`scripts/check_no_ambient_railway_ids.py` runs in CI (`quality.yml`) and fails
the build if:

1. **Any tracked non-markdown file** reads one of the three ambient IDs from the
   environment (`os.environ[...]`, `os.environ.get(...)`, `os.getenv(...)`, or
   `${...}` / `$...` shell interpolation). Since the services never call
   Railway, any such read is a red flag and is rejected.
2. **No safety doc carries this warning** — so the human-readable rule cannot
   silently rot out of the repo.

It has a provenance/kill-switch header: it is a disposable convenience guard, so
if it ever proves noisy, delete it (script + test + the `quality.yml` step)
rather than working around it.

## When you DO need Railway (the safe path)

Operate **only** on the dedicated `superbot-websites` project, using
`RAILWAY_API_KEY` **plus the explicit IDs hardcoded in `docs/deployment.md`** —
never the ambient ones:

| Thing | Explicit SAFE ID (from `docs/deployment.md`) |
|---|---|
| Project `superbot-websites` | `70198ece-cbc0-484e-86d9-f8a1eca4f045` |
| Environment `production` | `31485ecd-b3fe-4a8f-b136-337f6f099dc2` |
| Service `control-plane` | `2c840017-a505-4144-b2ff-b2450430a7d9` |

Non-destructive operations only. Never call a delete/restore/destructive Railway
mutation against anything — misconfigured something? Update it or create a
replacement. Never add `RAILWAY_API_KEY` to any app's service env.

## Post-deploy verification

After any merge (merge = deploy), run `python3 scripts/healthcheck.py` — it GETs
`/healthz` and `/` on all three live services and exits non-zero if any is down.
See `docs/deployment.md` § Post-deploy verification.
