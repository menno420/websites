# 2026-07-09 — Rework botsite into websites (build + deploy)

> **Status:** `in-progress`

## What I'm about to do

Execute sequence step 3 of the rework plan
(`docs/planning/dashboard-botsite-rework-plan-2026-07-09.md`) for the **botsite**
half: build a real, server-rendered public bot site as a new `botsite/` service in
this repo, deploy it as a **new Railway service in `superbot-websites`** (alongside
`control-plane`), dark-launched on its Railway URL.

Following the plan's botsite recommendations:
- Keep the ideas/functionality of superbot's `botsite/`, rebuild the implementation
  on this repo's substrate (FastAPI + Jinja2, server-rendered, no build step).
- Consume superbot's committed `site.json` via **raw.githubusercontent.com**
  (read-only toward superbot, forward-only). Never fake data — a missing feed
  renders as a declared pending/error lane.
- Promote the `ds/` design system (tokens.css + components.css, copied verbatim).
- Drop the v1/v2 duality and Tailwind-CDN; ship one server-rendered site on `ds/`.
- Public, secret-free surface. `/submit` form ships; its DB write path is a
  clearly-labeled stub until the submissions Postgres is provisioned (owner Q5).

Docs: new `docs/botsite.md`, `[D-0008]` in `docs/decisions.md`, current-state update.
