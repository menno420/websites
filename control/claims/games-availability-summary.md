# Claim: games-availability-summary

- `claude/games-availability-summary` · **scope** — surface the Fleet Arcade launch-readiness summary (live / blocked / distinct owner clicks) on the `/games` front door, reusing `botsite.arcade.availability_summary` over `load_games()` (disk, no network) and cross-linking to `/arcade`; read-only, no new route · botsite/app.py, botsite/templates/games.html, botsite/tests/ · 2026-07-16
