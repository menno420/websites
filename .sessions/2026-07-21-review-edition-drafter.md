# Session card — 2026-07-21 · review edition auto-drafter

> **Status:** `in-progress`

- **📊 Model:** opus-4.8 · medium · idea/feature
- **💡 Idea:** The review site's "continuous review channel" had one edition (2026-07-11) and no generator — derive future editions from the already-baked committed data mirrors so the channel stays alive with zero owner action.
- **⟲ Previous-session review:** #462 landed the 2026-07-20 product-frontier plan + baton; this session executes its top slice (S1). Prior overnight work drained the hardening backlog through #460/#461.

## Goal
Ship `review/gen_edition.py` (drafts the next edition markdown from committed data mirrors) + tests, and publish a fresh edition-002.

## What landed
- review/gen_edition.py — deterministic edition drafter over review/data/*.json.
- review/data/reviews/2026-07-21-edition-002.md — generated, parseable by editions.py.
- review/tests/test_gen_edition.py — generator output validity + editions.py round-trip + idempotent slug/date.

## Verify
- env -u DATABASE_URL python3 -m pytest tests/ botsite/tests dashboard/tests review/tests -q
- env -u DATABASE_URL python3 bootstrap.py check --strict
- editions.py lists edition-002; live: review site /editions shows the new edition post-merge.
