# 2026-07-16 — Games front door: Fleet Arcade launch-readiness summary

> **Status:** `complete` — branch `claude/games-availability-summary`; the
> live / blocked / distinct-owner-clicks summary the /arcade catalog carries
> (PR #369) now also greets visitors on the `/games` front door, reusing the
> merged `botsite.arcade.availability_summary` helper over `load_games()`
> (disk read, no network, no duplicated counting) and cross-linking to
> /arcade. Read-only; +3 tests.

- **📊 Model:** Claude Opus · high · feature build — games front-door arcade availability summary

**What this session is about:** promote the Fleet Arcade's launch-readiness
from the /arcade catalog to the sibling /games front door. PR #369 added the
`availability_summary(games)` helper and a top-of-page strip counting live vs
blocked games plus the distinct owner clicks blocking launch — but only on
/arcade. Visitors landing on /games (in-chat mini-games) saw nothing of how
launch-ready the fleet's playable catalog is. This slice adds the SAME strip
to `/games`: the route loads the arcade registry via the shared
`arcade.load_games()` (disk, no network) and passes
`arcade.availability_summary(...)` — the single source of truth, no copied
counting — into `games.html`, which renders a summary consistent with
`arcade.html`'s markup and cross-links to /arcade. Read-only throughout: no
new route, no state change, no POST, no CSRF surface; the strip is omitted
when the registry is empty (fail-soft `total == 0` guard).

⚑ Self-initiated: no — coordinator-dispatched slice, the preferred path from
the dispatch (front door surfaces arcade launch-readiness at a glance).

💡 Idea: a tiny "N of M live" figure could ride the top nav "Arcade" item
itself (a computed nav badge), so every page — not just /games and /arcade —
surfaces launch-readiness; would need the summary in `_base_ctx` behind a
cheap once-per-request cache of `load_games()`.

**Previous-session review** (`.sessions/2026-07-16-console-release-drift-chip.md`):
exemplary reuse discipline — #365's drift ladder extracted to one pure
`release_drift.classify()` consumed by BOTH the healthcheck and the console
chip, byte-identical output keeping the old tests green; this session follows
the same single-source-of-truth rule by reusing `availability_summary` rather
than recomputing counts on the games route.

## Close-out

**Evidence:**

- files touched this branch: `botsite/app.py` (the `/games` route loads
  `arcade_registry.load_games()` and passes `arcade_summary =
  arcade_registry.availability_summary(...)` into the context; docstring
  records the read-only, no-network, no-duplicated-counting contract);
  `botsite/templates/games.html` (a summary strip after the hero, guarded by
  `arcade_summary.total`, mirroring `arcade.html`'s markup — bold `N live`,
  `K blocked on J owner click(s)` with singular/plural — plus an "Explore the
  Arcade" cross-link); `botsite/tests/test_arcade.py` (+3 tests:
  route-render over the committed registry asserting `1 live` / `2 blocked` /
  `on 2 owner clicks` + the /arcade cross-link; a monkeypatched-helper test
  proving the strip tracks `availability_summary` exactly with singular
  "owner click"; and a no-live-verdict-leak hard rail mirroring /arcade).
- `control/claims/games-availability-summary.md` — created at start, deleted
  at this flip.

**Verify (both green):**

- `python3 -m pytest tests/ botsite/tests dashboard/tests review/tests -q`
  → `1628 passed, 1 warning in 84.96s`
- `python3 bootstrap.py check --strict --session-log
  .sessions/2026-07-16-games-availability-summary.md` → HOLD by design while
  the card read in-progress (born-red session gate); clears on this flip to
  complete. No claims-format / duplicate advisory.

**Next session should know:** the arcade summary now renders on two surfaces
(/arcade, /games) from one helper. If a third surface wants it (see the 💡
nav-badge idea), lift the `load_games()` call behind a per-request cache
rather than calling it per route.
