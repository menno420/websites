# Claim: games-availability-summary

- **Branch:** `claude/games-availability-summary`
- **Scope:** Surface the Fleet Arcade launch-readiness summary (live / blocked /
  distinct owner clicks) on the `/games` front door, reusing the merged
  `botsite/arcade.availability_summary` helper over `load_games()` (disk, no
  network) and cross-linking to `/arcade`. Read-only: no new route, no state
  change. Touches `botsite/app.py`, `botsite/templates/games.html`, and
  `botsite/tests/`.
- **Date:** 2026-07-16
