# Session — games-availability-summary

> **Status:** `in-progress`

## Goal

Surface the Fleet Arcade's launch-readiness at a glance on the `/games` front
door: add the same live / blocked / distinct-owner-clicks availability summary
strip that `/arcade` carries (PR #369), reusing the merged
`botsite.arcade.availability_summary` helper over `load_games()` (disk read, no
network) and cross-linking to `/arcade`. Read-only slice — no new route, no
state change, no POST.

## Scope

- `botsite/app.py` — the `/games` route loads the arcade games list and passes
  `arcade_summary` into the template context (reusing the arcade loader +
  helper; single source of truth, no duplicated counting).
- `botsite/templates/games.html` — a summary strip consistent with
  `arcade.html`, cross-linking to `/arcade`.
- `botsite/tests/` — a route-render test asserting the `/games` page now
  carries the arcade summary text.

Stays inside botsite (four-service import rule). Does not touch owner-console
files.
