# Session card — 2026-07-21 · owner actions-now panel

> **Status:** `complete`

- **📊 Model:** opus-4.8 · medium · feature build
- **💡 Idea:** The /owner home leads with the readiness board and buries the actual open-action list one click away at /owner/queue — surface a top-of-home "Your N open actions" panel from the briefing.asks data already fetched, matching the owner's "what needs me now" instinct.
- **⟲ Previous-session review:** This session shipped S1 (edition drafter #463), S2 (arcade +Gloamline #464), S3 (fleet nav strip #466) off the 2026-07-20 plan; S4 is the last queue slice.

## Goal
Add an inline top-of-home open-actions panel on /owner reusing already-fetched briefing.asks (no new fetch), with an empty state, linking to /owner/queue for detail.

## What landed
- app/owner.py / app/templates/owner.html — inline "actions now" panel.
- tests/ — panel renders the pending-action count + empty state.

## Verify
- env -u DATABASE_URL python3 -m pytest tests/ botsite/tests dashboard/tests review/tests -q
- env -u DATABASE_URL python3 bootstrap.py check --strict --added-card .sessions/2026-07-21-owner-actions-panel.md
- live: /owner home shows the open-actions panel above the fold post-merge.
