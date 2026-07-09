# Bot site — public marketing + reference

> **Status:** `living-ledger` — built + deployed 2026-07-09 (rework plan step 3,
> botsite half). Ledger: `docs/decisions.md` (botsite deploy entry). Plan:
> `docs/planning/dashboard-botsite-rework-plan-2026-07-09.md`.

The **public** marketing + reference site for the SuperBot Discord bot, rebuilt on
this repo's substrate from superbot's `botsite/`: **same ideas and functionality,
fresh implementation.** It is a **separate Railway service** in `superbot-websites`,
deployed alongside `control-plane` from the same repo — a second service, not a router
mounted on the private control-plane app (the public/private split the plan requires).

## What it is

- **Server-rendered** FastAPI + Jinja2, no build step — the same stack as the
  control-plane app. Drops superbot's v1/v2 SPA duality and Tailwind-CDN:
  **one** server-rendered site on **one** design system.
- Styled with the **`ds/` program design system** (`tokens.css` + `components.css`
  copied verbatim from superbot, promoted here under `botsite/static/ds/`), plus a
  small layout-only `site.css`. Dark-first with a real light theme; theme toggle,
  mobile drawer, and a ⌘K command palette come from the verbatim `ds.js`.
- **Public and secret-free.** It holds no token and never imports bot code.

## Routes

| Route | What | Source |
|---|---|---|
| `/` | Home — hero, live stat tiles, area cards, latest-updates teaser, CTA | `index.html` |
| `/features` | Full 43-feature catalogue; client-side filter by area + search | `features.html` |
| `/features/{key}` | Per-feature detail + its commands (404 for unknown keys) | `feature_detail.html` |
| `/commands` | Full command reference (485); client-side search + area filter | `commands.html` |
| `/games` | The game features (12) | `games.html` |
| `/changelog` | User-facing changelog timeline | `changelog.html` |
| `/status` | Honest status band — subsystems "as of last deploy" (not live-probed) | `status.html` |
| `/design` | Living style guide for the `ds/` system | `design.html` |
| `/submit` | Suggestion/bug form — **write path stubbed** (see open items) | `submit.html` |
| `/palette.json` | Command-palette index (pages + features + games + commands) | `app.py` |
| `/healthz` | Liveness probe (JSON, unauthenticated, no network dependency) | `app.py` |
| `/static/*` | `ds/` assets + `app.js` + `site.css` | `StaticFiles` |

## Data source — read-only toward superbot, never fake

The site is **decoupled** from the bot exactly as superbot's `botsite/` is. It reads
only the committed public subset **`site.json`** from the superbot repo, fetched live
over **raw.githubusercontent.com** (anonymous, public file) with a 180s in-memory TTL
cache (`data_source.py`). Default feed:

```
https://raw.githubusercontent.com/menno420/superbot/main/botsite/data/site.json
```

That subset is redaction-by-construction (top-level whitelist: `meta`, `counts`,
`catalogue`, `commands`, `bot_changelog`) — dev-only families physically cannot appear.
Core inherited principle: **never fake data.** If the feed can't be fetched, every page
renders an honest "Live data temporarily unavailable" banner and only what the feed
provides — never stale invented content. `?refresh=1` on any page busts the cache.

The only mutation toward superbot is **none**: websites stays read-only and forward-only
toward the bot repo (plan open-question Q7, resolved: consume the artifact, don't rebuild
the export tooling here).

## Railway service

| Thing | Value |
|---|---|
| Project | `superbot-websites` — `70198ece-cbc0-484e-86d9-f8a1eca4f045` |
| Environment | `production` — `31485ecd-b3fe-4a8f-b136-337f6f099dc2` |
| Service | `botsite` — **`4314f839-0a93-4995-b424-02861ad2d5e6`** |
| Domain | https://botsite-production-cfd7.up.railway.app |
| Source | GitHub `menno420/websites`, branch `main` (repo-connect → merge = deploy) |
| Root Directory | `botsite` (Railway builds only this folder + its `Dockerfile`) |
| Build | `botsite/Dockerfile` (python:3.12-slim; binds `0.0.0.0:$PORT`) |
| Healthcheck | `GET /healthz` |

Created 2026-07-09 via the Railway public GraphQL API with `RAILWAY_API_KEY` only and
the explicit `superbot-websites` IDs — the ambient `RAILWAY_*` env (production **bot**)
was never passed; no destructive mutation was ever issued. Same guardrails as
`docs/deployment.md`.

## Environment variables (names only — none required)

| Var | Set? | Notes |
|---|---|---|
| `PORT` | injected by Railway | Do not set manually. |
| `SITE_JSON_URL` | not set (default superbot@main) | Optional override of the data feed. |
| `ADD_TO_DISCORD_URL` | not set (default) | Optional override of the install link. |
| `SITE_CACHE_TTL_SECONDS` | not set (default 180) | Optional feed cache TTL. |

The public surface deliberately carries **no secret**. When the submissions pipeline is
provisioned (below), the one secret it may ever hold is an **INSERT-only**
`SUBMISSIONS_DB_DSN` — never a control-API/mirror/OAuth token.

## How to redeploy

Merge to `main` — the service is repo-connected, so every merge auto-builds and
auto-deploys the `botsite` root directory. No manual deploy step.

## Local run

```bash
pip install -r botsite/requirements.txt
uvicorn botsite.app:app --reload      # http://127.0.0.1:8000
python3 -m pytest botsite/tests       # network-free smoke tests (feed primed from a fixture)
```

## Open items / stubs (owner-deferred)

- **`/submit` write path is a labeled stub (plan Q5).** The moderated submissions
  pipeline (INSERT-only Postgres + GitHub-issue mirror on approval) is **not
  provisioned** in `superbot-websites`. The form renders and validates, but POST
  honestly reports the intake is not live and points to the bot's GitHub issues —
  it never fakes a save. Wiring it up = provision a Postgres + an INSERT-only role,
  set `SUBMISSIONS_DB_DSN` on this service, and add the moderation ring as a
  **separate** owner-gated service (never mounted on this public app).
- **Design provenance (plan Q2, defaulted).** The rebuild standardizes on the `ds/`
  system + a v2-style layout rather than preserving superbot's v1 neon SPA
  pixel-for-pixel. Reversible if the owner wants the exact v1 look.
- **Custom domain (plan Q6).** Dark-launched on the Railway URL; apex/subdomain
  assignment is deferred to owner cutover. Nothing in superbot is touched.
- **`ds/` sharing.** The design system is currently vendored inside `botsite/static/ds/`
  for a self-contained service build. Lifting it to a repo-shared package is a sensible
  later step once the dashboard is built too (plan §3) — deferred to avoid restructuring
  the live control-plane now.
