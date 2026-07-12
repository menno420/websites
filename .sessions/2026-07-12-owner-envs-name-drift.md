# 2026-07-12 — /owner/environments documented-vs-live variable NAME drift check

> **Status:** `in-progress` — branch `claude/owner-envs-name-drift`; flips to
> `complete` + PR number as the deliberate LAST code step.

- **📊 Model:** claude-fable-5 · worker · feature-slice

**What this session was about:** the gated /owner/environments page holds
both halves of a diff it does not compute — the COMMITTED documented env-var
names per service (`app/railway.py` SERVICES) and the LIVE variable NAMES
Railway reports (`railway.live_overview`, project-scoped token, names never
values). This session builds the comparison: per-service and per-variable
documented-but-missing-live / live-but-undocumented badges, plus an honest
"drift unknown" state with the exact reason whenever Railway is unreachable —
never fabricated. Backlog promotion rung; executes the captured bullet
"/owner/environments drift check: documented vs live variable names"
(`docs/ideas/backlog.md`, source
`.sessions/2026-07-12-order-015-owner-environments.md` 💡). Plumbing follows
PR #216's `envhub.annotate_completeness` annotate/unknown-with-reason idiom;
rendering follows the #213/#217 chip idioms.

## What was done

- [[fill: implementation summary]]
- Verified: [[fill: verification output]]

⚑ Self-initiated: no — coordinator-assigned slice executing an existing
backlog bullet.

## 💡 Session idea

[[fill: session idea]]

## ⟲ Previous-session review

[[fill: previous-session review]]
