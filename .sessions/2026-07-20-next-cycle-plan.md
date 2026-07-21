# Session card — 2026-07-20 · product-frontier plan

> **Status:** `in-progress`

## Goal
Produce the 2026-07-20 product-frontier cycle plan and land it; queue the review edition auto-drafter as the top slice.

## What landed
- docs/plans/next-cycle-2026-07-20.md — 6 ranked executable slices + routed-out section.
- control/status.md baton refreshed: NEXT top = S1 edition auto-drafter.

## Evidence
- Product mining across arcade / review editions / owner console / botsite submissions / cross-site nav.
- Standout find: review editions are hand-authored, only edition-001 (2026-07-11) exists; review-bake.yml generates data mirrors but no editions — the "continuous review channel" is unbuilt, not owner-gated.

## Verify
- env -u DATABASE_URL python3 -m pytest tests/ botsite/tests dashboard/tests review/tests -q
- env -u DATABASE_URL python3 bootstrap.py check --strict
