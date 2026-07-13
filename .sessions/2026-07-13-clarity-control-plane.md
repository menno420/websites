# 2026-07-13 — clarity bar audit: control-plane pages state what they are, do, and offer

> **Status:** `in-progress` — branch `claude/clarity-control-plane`; flips to `complete`
> + PR number as the deliberate LAST code step.

- **📊 Model:** Claude Fable 5 · worker · clarity audit + fixes

**What this session was about:** OWNER ORDER 022 (night run — dispatched by
coordinator; note: order text not yet at this repo's inbox HEAD at boot,
proceeding on coordinator dispatch) — clarity bar on every control-plane
page: each page immediately shows WHAT it is, WHAT it does, and its most
important features; audit all app/ pages, fix every miss. Scope: app/
templates+routes + tests/ only.

## What was done

- (in progress — audit and fixes land on this branch; filled at close-out)
- Verified: (pending — `python3 -m pytest tests/ botsite/tests
  dashboard/tests review/tests -q` + `python3 bootstrap.py check --strict`
  run and summarized here before the flip to `complete`)

⚑ Self-initiated: no — OWNER ORDER 022 night run, dispatched by the
coordinator.

## 💡 Session idea

(pending — captured with its one-line "worth having because" and deduped
against `docs/ideas/backlog.md` + the queue-state NEXT list before the flip
to `complete`)

## ⟲ Previous-session review

(pending — written at close-out)
