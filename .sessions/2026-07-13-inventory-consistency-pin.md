# 2026-07-13 — committed-inventory consistency pin: railway.SERVICES vs the envhub registry

> **Status:** `in-progress` — branch `claude/inventory-consistency-pin`;
> flips to `complete` + PR number as the deliberate LAST code step.

- **📊 Model:** claude-fable-5 · worker · feature-slice

**What this session was about:** backlog promotion rung — executes the
captured bullet "Committed-inventory consistency pin: `railway.SERVICES` vs
the envhub registry" (`docs/ideas/backlog.md`, source
`.sessions/2026-07-12-owner-envs-name-drift.md` 💡). The repo hand-keeps TWO
committed inventories of the same four services' variable names
(`app/railway.py` SERVICES and `app/data/environments.json`'s
superbot-websites group) and they have already drifted: the registry
documents `ANTHROPIC_API_KEY` for botsite, SERVICES does not. This session
(1) reconciles the drift honestly — evidence decides which side is right —
and (2) pins the two inventories to each other with one zero-network suite
test (declared-exceptions allowlist, no silent exemptions), so the next
divergence goes red at PR time instead of lying to the owner.

## What was done

- <filled at close-out>
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — <N passed>; `python3 bootstrap.py check --strict` —
  <verdict>.

⚑ Self-initiated: no — backlog promotion (the committed-inventory
consistency bullet, `docs/ideas/backlog.md`).

## 💡 Session idea

<filled at close-out>

## ⟲ Previous-session review

<filled at close-out>
