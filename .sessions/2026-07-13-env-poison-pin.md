# 2026-07-13 — self-deriving poison-list pin for the hostile-env smoke

> **Status:** `in-progress`

- **📊 Model:** Claude Fable 5 · worker · backlog-promotion

**What this session was about:** promote the captured backlog bullet
"Self-deriving poison list — pin the hostile-env smoke's ENV_VARS against
a live source sweep" (`docs/ideas/backlog.md`, captured 2026-07-13 by the
hostile-env-smoke session 💡, PR #287): the smoke poisons a hand-collected
38-name literal, so a new env-var read added after #287 is silently
unpoisoned — the exact rot class the smoke exists to close, reopened one
variable at a time. Build an AST sweep over the four services (same
discovery/exclusion rules as the smoke) that derives every env-var NAME
the source actually reads and fails, naming the variable and site, when
the poison list misses one.

## What was done

[[fill: close-out]]

## 💡 Session idea

[[fill: one idea]]

## ⟲ Previous-session review

[[fill: review]]
