# Session 2026-07-09 — pin the console.json feed contract (consumer half)

> **Status:** `in-progress`

## What I'm about to do

Consumer half of the cross-repo console.json shape contract (superbot PR #1884
ships the producer half: a committed, versioned
`botsite/data/console_data_contract.json` + a fail-closed checker, and
`console.json` now carries `meta.schema_version`):

- Pin a copy of contract v1 in `dashboard/` and verify at render time that the
  fetched feed's `meta.schema_version` matches — an honest schema-drift banner
  on `/console` instead of a silently wrong page.
- Fix the live defect the contract immediately surfaced: the console page
  treats `ideas`/`bugs` as lists (`|length`) but the real feed ships dicts
  (`{total, by_status, open_count, open}`) — the stat tiles show dict-key
  counts today. Fix template + route + fixture to the contracted shape.
- Tests for both; `python3 bootstrap.py check --strict` green.
