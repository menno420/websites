# websites · status
updated: 2026-07-09T12:07Z
phase: three FastAPI/Jinja2 services live on Railway (control-plane board + password-gated /owner overlay, botsite, dashboard); substrate-kit machinery engaged (#16); hardening batch landed (#19/#20)
health: green (`quality` workflow — required check on main — green on last 8 runs incl. head d0e9b33; Railway auto-deploys from main into the superbot-websites project, verified live per docs/deployment.md)
last-shipped: #20 — hardening fix-forward (Railway-ID ambient-env CI guard, healthcheck script, stub badges, OWNER-ACTIONS doc); all 20 PRs merged, zero open
blockers: none agent-side. Owner-gated: plan Q4 (where the live-bot-write control panel lives: websites / superbot / superbot-next) + Q5 (submissions Postgres) — parked in docs/owner/OWNER-ACTIONS.md
orders: acked= done=
⚑ needs-owner: Q4 / Q5 decisions per docs/owner/OWNER-ACTIONS.md
notes: dashboard /admin live-bot-write panel is a deliberate labeled stub. #19 auto-merged prematurely on its born-red card alone (known kit gap, fix-forwarded by #20). Manager recon grounded in README, docs/current-state.md, docs/deployment.md, PRs #16–#20, quality runs @ d0e9b33.

⟵ manager-seeded starting point — websites, overwrite this with your own status on your first run.
