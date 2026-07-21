# Session card — 2026-07-21 · arcade catalog growth

> **Status:** `complete`

- **📊 Model:** opus-4.8 · medium · feature build
- **💡 Idea:** The public arcade lists only 3 games though the fleet has shipped more — grow the catalog with verified real entries so the front door reflects the fleet, honest blocker/ask_id where an owner step genuinely gates a launch.
- **⟲ Previous-session review:** This session landed S1 (review edition auto-drafter, #463) off the 2026-07-20 plan (#462); S2 is the next queue slice.

## Goal
Add verified fleet games to botsite/data/arcade.json with honest availability + blocker/ask_id, tests updated, no fabrication.

## What landed
- botsite/data/arcade.json — 1 new verified entry (gloamline, Nintendo DS, download).
- botsite/tests — count pin bumped + per-entry validation/probe coverage.

## Verify
- env -u DATABASE_URL python3 -m pytest tests/ botsite/tests dashboard/tests review/tests -q
- env -u DATABASE_URL python3 bootstrap.py check --strict --added-card .sessions/2026-07-21-arcade-catalog-growth.md
