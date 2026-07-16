# Session — Fleet Arcade catalog blocker surfacing + availability summary

> **Status:** `in-progress`

Branch `claude/arcade-catalog-blockers` (from `origin/main` @
16a116c). Born-red card: gate held red by design until the slice lands and
this card flips complete.

## Goal

The public arcade catalog at `/arcade` shows each game card with only a
`status_note`; the blocker's `owner_action` + `ask_id` (the honest ledger
blocker text) appears ONLY on the per-game detail page. This slice:

- Surfaces each UNAVAILABLE game's blocking `owner_action` / `ask_id` on its
  catalog card, mirroring the detail page's ledger-text idiom. Ledger text
  only — no live askverify verdicts (those stay gated-surface-only by hard
  rail; the public page shows static registry data).
- Adds a top-of-page availability summary strip ("N live · M blocked on K
  owner clicks") — counts derived from the registry (live vs blocked games,
  distinct owner-action/ask_id count among the blocked ones), via a pure
  fail-soft helper in `botsite/arcade.py`.

Read-only: no new route, no state change, no POST/CSRF surface. Stays within
the botsite package (four-service import rule).

## Trail

- [[fill: commits + verify tails at flip]]
