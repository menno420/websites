# Session — dashboard /ideas status filter pills

> **Status:** `in-progress`

- **📊 Model:** Claude Opus · high · dashboard-feature build

## Goal
Give the dashboard `/ideas` backlog a lifecycle-status filter: `all` / `open` / `shipped`
pills that reuse the existing client-side filter (`data-filter-pill` / `data-cat`), so the
owner can isolate shipped vs still-open ideas — parity with the category filters already on
`/commands` and `/functions`. Dashboard-side pick in the spirit of B5 (idea lifecycle states),
`docs/planning/arcade-dashboard-menu-2026-07-16.md` (PR #373).

## Scope
- `dashboard/` only. `data_source.py` gets a pure `idea_bucket()` helper (reuses
  `SHIPPED_IDEA_STATUSES` — no drift with the hero count or the green badge); the `/ideas`
  route annotates each idea with its bucket; `ideas.html` renders a `sb-filterbar`, gated to a
  mixed backlog so a uniform list stays noise-free. Read-only, additive, reversible by revert.
  No cross-service import.

## 💡 Session idea
The same status-bucket filterbar generalizes to `/bugs` (open vs fixed lanes) — both pages
already carry the `data-filter-root`/search scaffold and differ only in their lifecycle
vocabulary, so a shared `_status_filterbar.html` partial could serve both once a second
consumer justifies the extraction.

## ⟲ Previous-session review
`.sessions/2026-07-17-arcade-owner-action-queue.md` (complete) surfaced the pending
owner-action queue on `/arcade` as a real list rather than a bare count — well-scoped,
fail-soft, single-service work; this session follows the same "turn an existing aggregate
into something the owner can act on" instinct, one service over on the dashboard.
