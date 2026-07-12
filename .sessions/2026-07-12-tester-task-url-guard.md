# 2026-07-12 — botsite: tester-task product URL liveness guard

> **Status:** `in-progress` — branch `claude/tester-task-url-guard`; flips to
> `complete` + PR number as the deliberate LAST code step.

- **📊 Model:** claude-fable-5 · worker · feature-slice

**What this session was about:** backlog promotion — the captured bullet
"Tester-task URL liveness guard" (`docs/ideas/backlog.md`, source
`.sessions/2026-07-12-order-018-testing-platform-pr1.md` 💡). Every `open`
task in `botsite/testing_tasks.json` points a paying tester at a
`product_url`; if that URL dies, the program burns real testers' time and
its own credibility before anyone notices. This session grows
`scripts/healthcheck.py` a testing-catalog pass mirroring the arcade URL
drift probe (`botsite/arcade_probe.py`, PRs #214/#220): GET every open
task's `product_url`, final-200 semantics, fail-soft findings.

## What was done

- [[fill: probe module, healthcheck fold-in, tests, verification]]

⚑ Self-initiated: no — coordinator-assigned slice executing an existing
backlog bullet.

## 💡 Session idea

[[fill: one deduped idea with its "worth having because"]]

## ⟲ Previous-session review

[[fill: one line on the newest other card]]
