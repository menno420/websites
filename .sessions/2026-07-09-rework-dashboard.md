# 2026-07-09 — Rework dashboard into websites (build + deploy)

> **Status:** `complete`

- **📊 Model:** Claude Opus 4.8 (pre-v1.2.0 backfill; builder-session subagent, inherited — not independently confirmed)

## What I did

Executed the dashboard half of the rework plan
(`docs/planning/dashboard-botsite-rework-plan-2026-07-09.md`): built a real,
server-rendered **private** developer dashboard as a new `dashboard/` service in this repo
and deployed it as a **new Railway service `dashboard`** in `superbot-websites` (alongside
`control-plane` and `botsite`), dark-launched at
https://dashboard-production-a91b.up.railway.app.

- **Stack:** FastAPI + Jinja2, server-rendered, no build step. Own `dashboard/Dockerfile`,
  `requirements.txt`, `Procfile`, `.dockerignore`. Binds `0.0.0.0:$PORT`.
- **Auth (private):** HTTP Basic on every route (any username + `SITE_PASSWORD`,
  constant-time), same pattern as `app/main.py`. Fail-closed: 503 every route if unset.
  `/healthz` is the single unauthenticated route (Railway probe). A strong `SITE_PASSWORD`
  was generated and set as the service var; the value + URL live only in the deploy
  session scratchpad, committed nowhere.
- **Design:** vendored the `ds/` design system (`tokens.css` + `components.css` + `ds.js`
  copied from botsite), plus a layout-only `site.css` and the page-wiring `app.js`.
- **Read-only oversight surface (fully live):** `/` `/functions` `/commands` `/aliases`
  `/settings` `/access` `/env` `/ideas` `/bugs` `/updates` `/console` `/status`
  `/palette.json` `/healthz`. Reproduces superbot dashboard's read-only pages. Env-map
  shows names + code locations only, never values.
- **Data:** superbot's committed `dashboard.json` + `console.json` fetched live via
  raw.githubusercontent.com with a 180s TTL cache (`data_source.py`). Read-only +
  forward-only toward superbot, **never fakes data** — a failed feed renders an honest
  banner (covered by a test).
- **THE deliberate stub:** `/admin` renders the Discord-OAuth control-panel UI shape, but
  every mutating action is a disabled placeholder ("requires owner wiring — not connected
  to the live bot"). **No production bot control-API URL or token exists anywhere in the
  service** — a test (`test_no_control_api_token_or_url_anywhere`) asserts the literal
  names never appear. The live-write path couples websites to the running production bot
  (plan Q4) and is an owner decision.
- **Tests:** `dashboard/tests/test_dashboard.py` — 28 network-free smoke tests (feeds
  primed from fixtures) covering auth (401/503/200), every read-only page, the stub, and
  honest degradation. Full repo suite 51 passed; `python3 bootstrap.py check --strict`
  green.
- **Railway:** created service `dashboard` (`39007299-11a2-49a8-9c5c-21e17194fb3e`), Root
  Directory `dashboard`, repo-connected to `menno420/websites@main`, `SITE_PASSWORD`
  upserted, public domain generated — all via `RAILWAY_API_KEY` + explicit
  `superbot-websites` IDs only; ambient production-bot IDs never passed; no destructive
  mutation. Live-verified post-merge.
- **Docs:** new `docs/dashboard.md` (routes, data sources, service IDs, env, auth,
  real-vs-stub, open items), `[D-0009]` in `docs/decisions.md`, `docs/current-state.md`
  updated. Fixed pre-existing stamp drift: `[D-0008]` was cited from both `botsite.md` and
  `current-state.md` — de-duplicated to keep each decision single-homed.

Local verification before merge: ran the app against the **live** feeds (real 43 subsystems
/ 420-item palette / `DATABASE_URL` env map render; all routes 200; unauth 401; 404 works)
and simulated the exact in-image package layout (`/srv/dashboard` + `uvicorn
dashboard.app:app`) — green.

⚑ Self-initiated: no (owner-directed overnight task). One in-scope drift fix (the D-0008
stamp de-duplication) done on sight per the bugs-first directive.

## 💡 Session idea

**A repo CI test that greps every `dashboard/`-service source file for a denylist of
production-bot-coupling tokens** (`CONTROL_API_TOKEN`, `CONTROL_API_URL`,
`worker.railway.internal`, `DISCORD_OAUTH_CLIENT_SECRET`) — I shipped exactly this as
`test_no_control_api_token_or_url_anywhere`, but only for the dashboard. Promoting it to a
repo-wide checker (the whole `websites` repo must never reference a live-bot control
credential, since that coupling is the single boundary this project guards) would turn a
per-service convention into an enforced invariant — the "enforce, don't exhort" pattern.

## ⟲ Previous-session review

The previous session (PR #7, botsite) did the substrate work that made this one fast: a
clean `data_source.py` envelope, the vendored `ds/` system, and the born-red→flip-green
session discipline all carried straight over — I reused its shapes almost verbatim, which
is the point of building the substrate first. Its own `💡` idea (a `shared/ds/` package +
a drift guard) is now *more* justified: `ds/` is vendored **twice** (botsite + dashboard),
so the drift risk it flagged is now real. **One concrete workflow improvement it surfaces:**
the stamp-discipline check caught `[D-0008]` cited from two docs — a class of drift a human
wouldn't notice — but nothing *taught* the pattern, so PR #7 introduced it and PR #8 had to
fix it. A one-line note in the session-close doc-audit ("cite each `D-NNNN` from at most one
doc outside `decisions.md` — current-state.md is the home") would stop the next session
re-introducing it. Worth adding to the doc-audit checklist rather than relearning per PR.

## Doc audit

- `python3 bootstrap.py check --strict` → green (0 findings) after de-duplicating the
  D-0008 citation and adding the session enders.
- Full pytest suite: 51 passed.
- New owner-facing decision recorded as `[D-0009]`; `docs/dashboard.md` reachable from
  `docs/current-state.md`; live Railway IDs recorded in `docs/dashboard.md`.
