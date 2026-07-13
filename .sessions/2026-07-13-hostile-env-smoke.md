# 2026-07-13 — hostile-env import smoke: import every service module under a poisoned environment

> **Status:** `in-progress` — branch `claude/hostile-env-smoke-0713`; flips
> to `complete` + PR number as the deliberate LAST code step.

- **📊 Model:** Claude Fable 5 · worker · backlog-slice

**What this session was about:** backlog promotion — the captured bullet in
`docs/ideas/backlog.md` ("Hostile-env import smoke — dynamically import
every service module under a poisoned environment", 2026-07-13,
env-guard-gate session 💡, source `.sessions/2026-07-13-env-guard-gate.md`).
The static AST gate (`tests/test_env_guard_gate.py`, PR #285) only sees bare
`int()`/`float()` over env vars; this session adds the dynamic complement —
a smoke test that actually imports every module of all four services in a
subprocess whose environment sets every documented env var to `""` and to
garbage, proving no import-time crash of ANY kind.

## What was done

- (in progress — filled at close-out)

⚑ Self-initiated: no — backlog promotion of the hostile-env import smoke
bullet (`docs/ideas/backlog.md`, captured 2026-07-13 by the env-guard-gate
session).

## 💡 Session idea

(filled at close-out)

## ⟲ Previous-session review

(filled at close-out)
