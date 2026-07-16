# Claim: arcade-catalog-blockers

- **Branch:** `claude/arcade-catalog-blockers`
- **Date:** 2026-07-16
- **Scope:** Public arcade catalog (`/arcade`) blocker surfacing + availability
  summary strip — surface each unavailable game's blocking `owner_action` /
  `ask_id` (ledger text only, matching the detail page) on its catalog card,
  and add a top-of-page availability summary ("N live · M blocked on K owner
  clicks") derived from the registry. Read-only, static registry data, no new
  route, no POST/CSRF surface.
- **Files touched:**
  - `botsite/arcade.py` (pure `availability_summary` count helper)
  - `botsite/app.py` (pass `arcade_summary` into the `/arcade` context)
  - `botsite/templates/arcade.html` (summary strip + per-card blocker text)
  - `botsite/tests/test_arcade.py` (unit + render tests)
