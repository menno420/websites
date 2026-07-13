# 2026-07-13 — ORDER 041 remainder: prompt data on the dispatch screen + owner console

> **Status:** in-progress

- **📊 Model:** Claude Fable · worker (order execution) · feature-build

**What this session is about:** the ORDER 041 remainder (fleet-manager
inbox; the core shipped as PR #236) — "surface the same prompt data
everywhere it helps (the /prompts library, each seat's page on the
projects/console surfaces, the owner console) as views of ONE source — no
duplicated prompt copies anywhere in the site." Two surfaces are still
HEAD-copy-only: the per-seat dispatch screen (`/projects/{package}`) and
the gated owner console (`/owner`). Rung: order — ORDER 041.

## Planned slice

- `/projects/{package}`: a compact prompt-versions strip — current
  canonical version + the version ladder (via the existing
  `prompt_history.history()` module, zero new fetch semantics), the seat's
  deployed-vs-canonical state (the SAME drift plumbing the /prompts table
  uses), and a link to `/prompts/history/{seat}`. Only for packages that
  map to a roster seat; honest degradation ("history not available" — never
  hidden, never invented).
- `/owner`: a per-seat fleet prompt-state card — deployed vs canonical,
  stale count, worst state, history link — reduced from
  `prompts.deployed_drift()` rows (the one source; no copies stored).
- GET-rendering only; no new state-changing routes. Tests for both
  surfaces (rendering + degradation) in `tests/`.

## What was done

(filled at close)
