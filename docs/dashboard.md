# Developer dashboard — private oversight site

> **Status:** `living-ledger` — built + deployed 2026-07-09 (rework plan step 3,
> dashboard half). Ledger: `docs/decisions.md` (dashboard deploy entry). Plan:
> `docs/planning/dashboard-botsite-rework-plan-2026-07-09.md`.

The **private** developer dashboard for the SuperBot Discord bot, rebuilt on this repo's
substrate from superbot's `dashboard/`: **same read-only ideas and functionality, fresh
implementation.** It is a **separate Railway service** in `superbot-websites`, deployed
alongside `control-plane` and `botsite` from the same repo — a third service, not a router
mounted on another app (the auth-model split the plan requires).

## What it is

- **Server-rendered** FastAPI + Jinja2, no build step — the same stack as the
  control-plane and botsite apps. Drops superbot's Tailwind-CDN: one server-rendered site
  on the shared `ds/` design system.
- **Private.** The whole surface is internal oversight data, so every route is gated
  behind **HTTP Basic auth** (any username, password compared constant-time to
  `SITE_PASSWORD`) — identical to the control-plane app. **Fail-closed:** an unset
  `SITE_PASSWORD` makes every route `503`, never open. `/healthz` is the single
  unauthenticated route (Railway probe).
- **Read-only toward the bot.** It never imports bot code and holds **no bot control
  credential**. A failed feed renders an honest banner — never faked data.

## Routes

### Read-only oversight (fully live)

| Route | What | Source |
|---|---|---|
| `/` | Overview — inventory stat tiles, subsystems by area, latest sessions | `index.html` |
| `/functions` | Subsystem catalogue grouped by area (description, tier, entry points, tags); client-side filter + search | `functions.html` |
| `/commands` | Cog & command explorer — every command badged prefix/slash/subcommand/button; search + area filter | `commands.html` |
| `/aliases` | Suggest a command alias — live collision check vs. every name/alias/synonym + a prefilled GitHub issue + paste-ready snippet (fully client-side) | `aliases.html` |
| `/settings` | Settings catalogue — every per-guild key by owning subsystem, with type/default/hint/enum. Names + metadata only, **never a stored value** | `settings.html` |
| `/access` | Permissions & access map — the visibility-tier ladder + which subsystems each tier can see | `access.html` |
| `/env` | Env-var usage map — each variable → every file/line that reads it, by layer. **Names + code locations only, never a value** | `env.html` |
| `/ideas` | Idea backlog (from superbot `docs/ideas/`) | `ideas.html` |
| `/bugs` | Bug board (from superbot `docs/health/bug-book.md`) | `bugs.html` |
| `/updates` | Updates feed built from superbot `.sessions/` logs | `updates.html` |
| `/console` | Owner one-glance program console — sessions/ideas/bugs/changelog from `console.json` | `console.html` |
| `/status` | Inventory counts + bug health snapshot | `status.html` |
| `/palette.json` | Command-palette index (pages + subsystems + commands) | `app.py` |
| `/healthz` | Liveness probe (JSON, unauthenticated, no network dependency) | `app.py` |
| `/static/*` | `ds/` assets + `app.js` + `site.css` | `StaticFiles` |

### Control panel — a deliberate, clearly-labeled STUB

| Route | What | State |
|---|---|---|
| `/admin` | Discord-OAuth control panel UI (sign-in, per-server settings/help/cog-routing editors, submissions moderation) | **Stub — renders the shape; every mutating action is a disabled placeholder** |

In superbot the dashboard control panel signs in with Discord OAuth and **writes the live
production bot's control API** (settings / help / cog-routing, applied live), plus an
owner-gated submissions-moderation ring. That live-write path couples websites to the
**running production bot** across the repo boundary and is an owner decision (rework-plan
open question **Q4**). So it is **NOT wired here**:

- `/admin` renders the UI so the intent is visible, but every mutating control is a
  disabled placeholder labeled *"requires owner wiring — not connected to the live bot."*
- **No production bot control-API URL or token exists anywhere in this service** — no
  Discord OAuth client, no control-API token, no write path. A test
  (`dashboard/tests/test_dashboard.py::test_no_control_api_token_or_url_anywhere`) asserts
  those literal names never appear in the service source.

Wiring it later is an owner decision about *where bot control should live* (here, in
superbot, or in superbot-next) — see the plan's Q4.

## Data source — read-only toward superbot, never fake

The read-only pages consume superbot's committed generated artifacts, fetched live over
**raw.githubusercontent.com** (anonymous, public files) with a 180s in-memory TTL cache
(`data_source.py`):

```
https://raw.githubusercontent.com/menno420/superbot/main/dashboard/data/dashboard.json
https://raw.githubusercontent.com/menno420/superbot/main/botsite/data/console.json
```

`dashboard.json` (produced by superbot's stdlib `scripts/export_dashboard_data.py`) carries
the full oversight payload; `console.json` feeds `/console`. Core inherited principle:
**never fake data** — if a feed can't be fetched, pages render an honest "Live data
temporarily unavailable" banner and only what the feed provides. `?refresh=1` on any page
busts the cache. The only mutation toward superbot is **none**: websites stays read-only and
forward-only (plan Q7, resolved: consume the artifact, don't rebuild the export tooling).

## Railway service

| Thing | Value |
|---|---|
| Project | `superbot-websites` — `70198ece-cbc0-484e-86d9-f8a1eca4f045` |
| Environment | `production` — `31485ecd-b3fe-4a8f-b136-337f6f099dc2` |
| Service | `dashboard` — **`39007299-11a2-49a8-9c5c-21e17194fb3e`** |
| Domain | https://dashboard-production-a91b.up.railway.app |
| Source | GitHub `menno420/websites`, branch `main` (repo-connect → merge = deploy) |
| Root Directory | `dashboard` (Railway builds only this folder + its `Dockerfile`) |
| Build | `dashboard/Dockerfile` (python:3.12-slim; binds `0.0.0.0:$PORT`) |
| Healthcheck | `GET /healthz` |

Created 2026-07-09 via the Railway public GraphQL API with `RAILWAY_API_KEY` only and the
explicit `superbot-websites` IDs — the ambient `RAILWAY_*` env (production **bot**) was
never passed; no destructive mutation was ever issued. Same guardrails as
`docs/deployment.md`.

## Environment variables

| Var | Set? | Notes |
|---|---|---|
| `SITE_PASSWORD` | ✅ set (secret) | **Required.** Basic-auth login (any username + this value). Fail-closed: the app 503s every route if unset. Value held by the owner (written to the deploy session's scratchpad), committed nowhere. |
| `PORT` | injected by Railway | Do not set manually. |
| `DASHBOARD_JSON_URL` | not set (default superbot@main) | Optional override of the oversight feed. |
| `CONSOLE_JSON_URL` | not set (default superbot@main) | Optional override of the console feed. |
| `DATA_CACHE_TTL_SECONDS` | not set (default 180) | Optional feed cache TTL. |

This service deliberately carries **no** bot control credential — no control-API token, no
Discord OAuth secret. Those are what the control-panel stub is a stub *about*.

## How to redeploy

Merge to `main` — the service is repo-connected, so every merge auto-builds and
auto-deploys the `dashboard` root directory. No manual deploy step.

## Local run

```bash
pip install -r dashboard/requirements.txt
SITE_PASSWORD=dev uvicorn dashboard.app:app --reload   # http://127.0.0.1:8000
python3 -m pytest dashboard/tests                       # network-free smoke tests (feeds primed from fixtures)
```

## Open items / stubs

- **Discord-OAuth live-write control panel (plan Q4) — the deliberate stub.** Whether the
  panel that writes the *live production bot* comes to websites at all is an owner decision;
  until then `/admin` is a labeled stub with no production control-API URL/token. Wiring it
  = an owner call on where bot control lives + provisioning the OAuth app + control-API
  token as a **separate** service (never mounted on a read-only surface).
- **Submissions moderation ring (plan Q5).** The owner-gated moderation of public botsite
  `/submit` suggestions (+ GitHub-issue mirror) is part of the same stubbed control ring;
  it needs the submissions Postgres + mirror PAT provisioned in `superbot-websites` first.
- **`ds/` sharing.** The design system is vendored in `dashboard/static/ds/` (also vendored
  in `botsite/static/ds/`). Lifting it to a repo-shared package (plan §3) is a sensible next
  step now that two services vendor it — deferred to avoid restructuring the live services.
- **Custom domain (plan Q6).** Dark-launched on the Railway URL; apex/subdomain assignment
  is deferred to owner cutover. Nothing in superbot is touched; the live superbot dashboard
  keeps running unchanged.
