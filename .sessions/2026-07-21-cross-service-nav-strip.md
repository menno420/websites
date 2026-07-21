# Session card — 2026-07-21 · cross-service fleet nav strip

> **Status:** `in-progress`

- **📊 Model:** opus-4.8 · medium · feature build
- **💡 Idea:** The four services never link to each other — add a small footer fleet strip so a visitor can move control-plane ↔ botsite ↔ dashboard ↔ review. URLs hardcoded until the deferred custom-domain call.
- **⟲ Previous-session review:** This session shipped S1 (edition drafter, #463) and S2 (arcade catalog +Gloamline, #464) off the 2026-07-20 plan; S3 is the next queue slice.

## Goal
Add a footer fleet nav strip (four cross-service links) to each service's base.html, per-service vendored (no cross-service imports), with a render test per service.

## What landed
- app/botsite/dashboard/review base.html footer: a fleet-links strip.
- one render test per service asserting the four links appear.

## Verify
- env -u DATABASE_URL python3 -m pytest tests/ botsite/tests dashboard/tests review/tests -q
- env -u DATABASE_URL python3 bootstrap.py check --strict --added-card .sessions/2026-07-21-cross-service-nav-strip.md
- live: each service footer shows the four fleet links post-merge.
