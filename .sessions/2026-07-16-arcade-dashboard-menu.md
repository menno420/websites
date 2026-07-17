# Session — arcade + dashboard overnight planning menu

> **Status:** complete

- **📊 Model:** Claude Opus 4.8 · high · idea/planning (overnight planning menu — broad, veto-ready proposal generation across botsite/Fleet-Arcade + dashboard)

## Goal
Overnight planning menu (owner OVERNIGHT ORDER, event 55f13541): generate a broad, veto-ready menu of DISTINCT proposals across the botsite/Fleet-Arcade and dashboard services — small fixes through ambitious features. Docs-only tonight; owner's morning veto is the filter.

## Scope
- botsite/ (app.py, arcade.py, registries, templates, data)
- dashboard/ (app.py, data_source.py, templates)
- Cross-service surfaces via committed JSON only (never a live cross-service import).

## Trail
- Grounded on HEAD da63857 (#357). #369 arcade blocked-game summary MERGED; #371 /games launch-readiness summary UNBUILT.
- Menu doc: docs/planning/arcade-dashboard-menu-2026-07-16.md
- Backlog bullet added to docs/ideas/backlog.md.

## Verify
- python3 bootstrap.py check --strict

## Result
- Menu doc written with 24 distinct veto-ready proposals (A1–A14 botsite/Fleet-Arcade, B1–B9 dashboard, C1–C2 cross-service) at docs/planning/arcade-dashboard-menu-2026-07-16.md; Status badge landed as `plan` (the docs-gate rejects `menu`).
- One `captured` backlog bullet added to docs/ideas/backlog.md.
- Draft PR opened (docs-only). Owner's morning veto is the filter.

## 💡 Session idea

The strongest single buildable pick from tonight's menu is **A1 — build #371 `/games` launch-readiness summary**: it is the last named open arcade issue at HEAD, and `/arcade`'s existing `availability_summary` is a ready-made template to clone. That gives the morning veto a clear default "yes, build this next" rather than a flat 24-way choice — the menu's job is breadth, but A1 is the one item that is both named-open AND has its scaffold already written.

## ⟲ Previous-session review

`.sessions/2026-07-16-rerun-jobs-preflight.md` (complete) closed clean: the rerun-ci preflight now names exactly which failed jobs the fire will re-run and the post-fire chip verifies those jobs re-queued at the job level — honest scope, well-tested (+6 tests), and it left no loose baton for this planning session to trip on. Workflow note it models well: degrade-never-blocks (the jobs row falls back to an honest "unknown" instead of gating the action) is the right default for any decoration-on-a-claim surface.
