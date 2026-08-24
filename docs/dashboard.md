# Developer dashboard — public oversight site

> **Status:** `living-ledger` — built + deployed 2026-07-09 (rework plan step 3,
> dashboard half); made **public** 2026-07-09 (owner "Yes drop the auth").
> Ledger: `docs/decisions.md`. Plan:
> `docs/planning/dashboard-botsite-rework-plan-2026-07-09.md`.

The developer dashboard for the SuperBot Discord bot, rebuilt on this repo's
substrate from superbot's `dashboard/`: **same read-only ideas and functionality, fresh
implementation.** It is a **separate Railway service** in `superbot-websites`, deployed
alongside `control-plane` and `botsite` from the same repo — a third service, not a router
mounted on another app.

## What it is

- **Server-rendered** FastAPI + Jinja2, no build step — the same stack as the
  control-plane and botsite apps. Drops superbot's Tailwind-CDN: one server-rendered site
  on the shared `ds/` design system.
- **Public read views.** The former HTTP Basic gate was removed; `SITE_PASSWORD` is no
  longer read. Oversight pages serve public committed data without credentials. Only the
  state-changing dry-run POSTs under `/admin/actions` are Discord-OAuth-gated; the service
  therefore reads OAuth/session secrets for that narrow boundary. `/healthz` is public.
- **Read-only toward the bot.** It never imports bot code and holds **no bot control
  credential**. A failed feed renders an honest banner — never faked data.
- **Names, never values.** The oversight pages already show only *names + locations*
  (env vars, settings keys) and **never a stored value** — nothing on the surface is a
  secret, which is what makes going public safe.

## Routes

### Read-only oversight (public)

| Route | What | Source |
|---|---|---|
| `/` | Overview — inventory stat tiles, subsystems by area, latest sessions | `index.html` |
| `/functions` | Subsystem catalogue grouped by area (description, tier, entry points, tags); client-side filter + search | `functions.html` |
| `/commands` | Cog & command explorer — every command badged prefix/slash/subcommand/button; search + area filter | `commands.html` |
| `/aliases` | Suggest a command alias — live collision check vs. every name/alias/synonym + a prefilled GitHub issue + paste-ready snippet (fully client-side) | `aliases.html` |
| `/settings` | Settings catalogue — every per-guild key by owning subsystem, with type/default/hint/enum. Names + metadata only, **never a stored value** | `settings.html` |
| `/access` | Permissions & access map — the visibility-tier ladder + which subsystems each tier can see | `access.html` |
| `/env` | Env-var usage map — each variable → every file/line that reads it, by layer. **Names + code locations only, never a value** | `env.html` |
| `/ideas` | Idea backlog (from superbot `docs/ideas/`), one valid card per source idea | `ideas.html` |
| `/bugs` | Bug board (from superbot `docs/health/bug-book.md`) | `bugs.html` |
| `/updates` | Updates feed built from superbot `.sessions/` logs | `updates.html` |
| `/console` | Owner one-glance program console — sessions/ideas/bugs/changelog from `console.json` | `console.html` |
| `/status` | Inventory counts + bug health snapshot | `status.html` |
| `/palette.json` | Command-palette index (pages + subsystems + commands) | `app.py` |
| `/healthz` | Liveness probe (JSON, no network dependency) | `app.py` |
| `/version` | Deployed commit SHA `{service, sha, short}` — read from `RAILWAY_GIT_COMMIT_SHA` → `GIT_SHA` → `"unknown"`; powers the control-plane deploy-state cell (see `docs/site.md`) | `app.py` |
| `/static/*` | `ds/` assets + `app.js` + `site.css` | `StaticFiles` |

### Owner panel — OAuth-gated, dry-run only

| Route | What | State |
|---|---|---|
| `/admin` | Control-panel UI over committed settings/help/cog data | Publicly readable shell; state-changing preview/confirm POSTs require the owner Discord login and remain dry-run only |

The panel implements a complete two-step **dry-run** flow. A signed-in owner can validate
an action against the committed typed schema, preview the exact contract-v1 request JSON,
and confirm it into an in-memory audit log that clears on restart. Nothing is sent to the
running bot. The four Discord/owner variables below authenticate and attribute those POSTs;
there is still **no production bot control-API URL or token** anywhere in this service.
Tests pin both the fail-closed OAuth boundary and the absence of a live control credential.

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

**The console feed's shape is a pinned cross-repo contract** (decision stamped in
`docs/current-state.md` / `docs/decisions.md`, 2026-07-09). Superbot commits the
canonical, versioned contract (`botsite/data/console_data_contract.json`, superbot PR #1884)
and stamps `meta.schema_version` into every emitted `console.json`; producer-side parity +
fail-closed shape checks run in superbot's CI. This service pins the copy it was built
against (`dashboard/console_data_contract.json`, v1) and verifies at render time
(`data_source.console_contract_issue`): a version mismatch or missing contracted family
renders an honest **schema-drift banner** on `/console` instead of a silently wrong page.
Upgrading = sync the pinned copy, adapt `console.html`/route, update the test fixture, in
one commit. `ideas`/`bugs` in the feed are counter **dicts** (`{total, by_status,
open_count, open}`), not lists.

## Railway service

| Thing | Value |
|---|---|
| Project | `superbot-websites` — `70198ece-cbc0-484e-86d9-f8a1eca4f045` |
| Environment | `production` — `31485ecd-b3fe-4a8f-b136-337f6f099dc2` |
| Service | `dashboard` — **`39007299-11a2-49a8-9c5c-21e17194fb3e`** |
| Domain | https://superbot-dashboard.up.railway.app |
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
| `SITE_PASSWORD` | left set but **unused** | The Basic-auth gate was removed (2026-07-09 auth-drop decision); the app no longer reads this — `rg SITE_PASSWORD dashboard/` matches nothing. Its continued live presence was re-confirmed by the ORDER 026 names-only read (2026-07-13, the "undocumented drift" lead in `docs/owner/OWNER-ACTIONS.md` row K — this row is its documentation). Left set in Railway is harmless and reversible. |
| `PORT` | injected by Railway | Do not set manually. |
| `DASHBOARD_JSON_URL` | not set (default superbot@main) | Optional override of the oversight feed. |
| `CONSOLE_JSON_URL` | not set (default superbot@main) | Optional override of the console feed. |
| `DATA_CACHE_TTL_SECONDS` | not set (default 180) | Optional feed cache TTL. Empty/malformed values fall back to the default at import (`_env_int`, 2026-07-13 hardening) — an empty Railway entry can no longer crash the service. |
| `DISCORD_CLIENT_ID` | runtime owner config; see names-only environments view | Discord OAuth application id; gates only `/admin/actions/*`. |
| `DISCORD_CLIENT_SECRET` | runtime owner config; see names-only environments view | Discord OAuth client secret; never exposed to public read views. |
| `OWNER_DISCORD_ID` | runtime owner config; see names-only environments view | Only this Discord user may receive an owner session. |
| `OWNER_SESSION_SECRET` | runtime owner config; see names-only environments view | Signs the owner session cookie. |

This service carries OAuth/session secrets for the owner gate, but deliberately carries
**no bot-control credential**: no production control-API URL or token.

## How to redeploy

Merge to `main` — the service is repo-connected, so every merge auto-builds and
auto-deploys the `dashboard` root directory. No manual deploy step.

## Local run

```bash
pip install -r dashboard/requirements.txt
uvicorn dashboard.app:app --reload   # http://127.0.0.1:8000 — public read views
python3 -m pytest dashboard/tests    # network-free smoke tests (feeds primed from fixtures)
```

## Open items / stubs

- **Live bot control remains deliberately unwired (plan Q4).** `/admin` is useful today as
  an OAuth-gated dry-run preview/audit surface. Any future production control API remains a
  separate owner decision and a separate armed service, never a credential added to these
  public read views.
- **Dashboard-local submissions moderation (plan Q5).** The public intake and durable
  Postgres store already live on botsite; bringing that queue into this dashboard remains
  a separate deferred information-design choice, not a prerequisite for `/admin` dry runs.
- **`ds/` sharing.** The design system is vendored in `dashboard/static/ds/` (also vendored
  in `botsite/static/ds/`). Lifting it to a repo-shared package (plan §3) is a sensible next
  step now that two services vendor it — deferred to avoid restructuring the live services.
- **Optional branded domain (plan Q6).** The friendly Railway domain is live; a separate
  branded apex/subdomain remains an owner-deferred marketing decision.
