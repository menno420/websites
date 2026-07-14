# 2026-07-14 — claims-drift gate: fail quality on claims for merged branches

> **Status:** `in-progress` — branch `claude/claims-drift-gate-0714`; flips to `complete`
> + PR number as the deliberate LAST code step.

- **📊 Model:** Claude Fable 5 · worker · gate-build + drift-sweep

**What this session was about:** backlog promotion — the fleet cleanup
audit (`docs/audits/2026-07-13-fleet-cleanup-audit.md`, suggestion 2 /
finding 1) proposed a cheap CI check that fails `quality` when a
`control/claims/*.md` file references a branch that has already merged
into main (the orphaned-claim drift class its finding 1 caught by hand:
`control/claims/2026-07-13-railway-placeholders.md` outliving merged
PR #275). This session builds that gate as a pytest, wires the control
fast lane to run it when a claims file is in a control-only diff, and
sweeps the proven-stale claim.

## What was done

- [[fill: changes with file paths]]
- Verified: [[fill: verify result]]

⚑ Self-initiated: no — audit suggestion 2 promotion
(`docs/audits/2026-07-13-fleet-cleanup-audit.md`).

## 💡 Session idea

[[fill: one idea you genuinely believe in — never filler]]

## ⟲ Previous-session review

[[fill: one genuine remark on the previous session + one workflow improvement]]
