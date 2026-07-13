# 2026-07-09 — Rework botsite into websites (build + deploy)

> **Status:** `complete`

- **📊 Model:** Claude Opus 4.8 (pre-v1.2.0 backfill; builder-session subagent, inherited — not independently confirmed)

## What I did

Executed sequence step 3 of the rework plan (botsite half): built a real,
server-rendered public bot site as a new `botsite/` service in this repo and deployed
it as a **new Railway service `botsite`** in `superbot-websites` (alongside
`control-plane`), dark-launched at https://botsite-production-cfd7.up.railway.app.

- **Stack:** FastAPI + Jinja2, server-rendered, no build step. Own
  `botsite/Dockerfile`, `requirements.txt`, `Procfile`. Binds `0.0.0.0:$PORT`.
- **Design:** promoted the `ds/` design system — `tokens.css` + `components.css` +
  `ds.js` copied verbatim from superbot into `botsite/static/ds/`, plus a small
  layout-only `site.css` and a page-wiring `app.js`. Dark-first + real light theme,
  theme toggle, mobile drawer, ⌘K command palette. Dropped the v1/v2 duality and
  Tailwind-CDN — one site, one design system.
- **Data:** superbot's committed `site.json` fetched live via raw.githubusercontent.com
  with a 180s TTL cache (`data_source.py`). Read-only + forward-only toward superbot,
  **never fakes data** — a failed feed renders an honest banner (covered by a test).
- **Surface:** `/` `/features` `/features/{key}` `/commands` `/games` `/changelog`
  `/status` `/design` `/submit` `/palette.json` `/healthz` + `/static/*`.
- **`/submit`** ships the form; its DB write path is a clearly-labeled stub until the
  submissions Postgres is provisioned (owner Q5) — POST honestly says intake isn't live.
- **Tests:** `botsite/tests/test_botsite.py` — 16 network-free smoke tests (feed primed
  from a fixture). Full repo suite 23 passed; `bootstrap.py check --strict` green.
- **Railway:** created service `botsite` (`4314f839-0a93-4995-b424-02861ad2d5e6`),
  Root Directory `botsite`, repo-connected to `menno420/websites@main`, public domain
  generated — all via `RAILWAY_API_KEY` + explicit `superbot-websites` IDs only; ambient
  production-bot IDs never passed; no destructive mutation. Live-verified post-merge.
- **Docs:** new `docs/botsite.md` (routes, data source, service IDs, env, open items),
  `[D-0008]` in `docs/decisions.md`, `docs/current-state.md` updated.

Local verification before merge: ran the app against the live feed (real 485/43/12
counts render; all routes 200; 404 works; palette 414 items) and simulated the exact
in-image package layout (`/srv/botsite` + `uvicorn botsite.app:app`) — green.

## 💡 Session idea

**A repo-shared `shared/ds/` package + a tiny CI test that asserts the vendored
`botsite/static/ds/*.css` is byte-identical to its superbot source hash.** Right now the
design system is vendored per-service; when the dashboard rebuild lands it'll be vendored
twice and can silently drift. Lifting `ds/` to one shared package (plan §3) plus a drift
guard keeps every websites surface rendering as one system with an enforced single source.

## ⟲ Previous-session review

The previous session (PR #6, token-wiring) did the right small thing well: it closed the
one open owner-TODO from the deploy session and *verified the auth-gated cells live* rather
than assuming the token worked — honest, evidence-first. What it (and the plan session
before it) left implicit and this session had to infer: **which Railway build knob makes a
second service build only a subdirectory.** The plan named "per-service Root Directories"
but no doc recorded the concrete `serviceInstanceUpdate(rootDirectory)` GraphQL call — I
rediscovered it by inspecting `control-plane`. **System improvement:** `docs/deployment.md`
should grow a short "adding a second service" recipe (serviceCreate → set rootDirectory →
serviceDomainCreate, with the guardrail reminder). I've captured the concrete IDs + the
call shape in `docs/botsite.md`; folding a generic recipe into `docs/deployment.md` is the
clean next step so the dashboard service doesn't rediscover it a third time.
