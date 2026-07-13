# 2026-07-13 — clarity bar for botsite + dashboard: every live page says what it is

> **Status:** `in-progress` — branch `claude/clarity-botsite-dashboard`; flips to `complete`
> + PR number as the deliberate LAST code step.

- **📊 Model:** Claude Fable 5 · worker · audit-and-fix-slice

**What this session was about:** order rung — ORDER 022 seat item 1, the
clarity-bar audit, dispatched by the coordinator as a worker slice scoped to
the **botsite/** and **dashboard/** services (sibling sessions own the app/
and review/ halves of the same order). Goal: every live page on the two sites
immediately shows what it is, what it does, and what its key features are — a
first-time visitor should never have to guess. Fixes stay inside the existing
Jinja2 server-rendered design idiom, with tests covering the new copy/structure.

## What was done

- In progress — audit of botsite/ and dashboard/ templates against the
  clarity bar, then fixes + tests, land on this branch.
- Verified: in progress — `python3 -m pytest tests/ botsite/tests
  dashboard/tests review/tests -q` and `python3 bootstrap.py check --strict`
  run before every push; final counts recorded here at close-out.

⚑ Self-initiated: no — coordinator-dispatched slice of ORDER 022 seat item 1.

## 💡 Session idea

In progress — captured at close-out (deduped against `docs/ideas/backlog.md`
+ the queue-state NEXT list before it counts).

## ⟲ Previous-session review

The inventory-consistency-pin session (PR #225) did well — it proved its new
pin red on pre-fix main before trusting it green, and its card recorded exact
test counts; nothing it missed affects this lane.
