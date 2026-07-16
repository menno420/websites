# Session — arcade + dashboard overnight planning menu

> **Status:** in-progress

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
