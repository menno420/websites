# 2026-07-09 — engage the substrate-kit machinery

> **Status:** `in-progress`

## What this session is about

The kit adoption (PR #1) was ritual-clean but never actually engaged: the
planted binding docs still carry `UNRENDERED SLOTS` banners, no CI gate runs
the kit check, `session_count` sits at 0 after ~9 sessions, the journal is an
empty template, and some bookkeeping (PR #10 card, ledger backfill, rework-plan
open questions) never landed. This session engages the machinery for real —
contained, reversible, forward-only.

Planned:
1. Render the 8 banner docs live (fill slots from project config, remove banners).
2. Install the kit CI gate (`.github/workflows/quality.yml`) + make it required if token scope allows.
3. Backfill: PR #10 retro card; add PRs #4/#10/#13/#15 to current-state Recently-shipped.
4. Route the 7 rework-plan open questions into `docs/question-router.md` as Q-blocks.
5. Engage the kit session loop (bump `session_count`, this card the kit way).
6. Seed `.session-journal.md` with a real quick-reference.
7. Ledger entry (D-0013) recording the kit-engagement pass.

Verify: `python3 bootstrap.py check --strict` green + all app test suites green.
