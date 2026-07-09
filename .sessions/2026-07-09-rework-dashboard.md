# 2026-07-09 — Rework dashboard into websites (build + deploy)

> **Status:** `in-progress`

## What I'm about to do

Execute the dashboard half of the rework plan
(`docs/planning/dashboard-botsite-rework-plan-2026-07-09.md`): build the SuperBot
developer dashboard as a real, server-rendered **private** website — a new `dashboard/`
service in this repo — and deploy it as a **new Railway service `dashboard`** in
`superbot-websites` (alongside `control-plane` and `botsite`).

Read-only oversight pages ship live (consume superbot's committed `dashboard.json` /
`console.json` via raw GitHub). The Discord-OAuth live-write control panel is built as a
**clearly-labeled stub** — no production bot control-API URL/token, mutating actions
disabled. HTTP Basic auth via `SITE_PASSWORD` (fail closed if unset); `/healthz` open.
