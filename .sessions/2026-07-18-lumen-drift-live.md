# 2026-07-18 — Arcade goes fully live: lumen-drift + games-web flip (ASK-0010 / ASK-0011)

> **Status:** `in-progress` — branch `claude/lumen-drift-live`. This card is
> born red on purpose: the `quality` gate stays red until the arcade flip, the
> refreshed release-drift bake, the ledger update, and the tests land green.
> The final commit flips this Status to `complete` and releases the hold.

- **📊 Model:** [[fill: model]]

**What this session is about:** two long-standing arcade launch blockers cleared
in one owner sitting. The owner (a) published the GitHub Release
`lumen-drift-v1.3` on `menno420/gba-homebrew` (satisfying **ASK-0010**) and (b)
ran product-forge's "Deploy games-web to Pages" workflow so
`https://menno420.github.io/product-forge/` now answers 200 with the real
character-sheet app (satisfying **ASK-0011**). This session records both in
`botsite/data/arcade.json` — lumen-drift → `download`, games-web → `live`, both
blockers dropped — rebakes `review/data/releases.json` (lumen-drift drift flips
to false), marks both ledger rows satisfied, and repoints the tests that pinned
the blocked state.

## Plan

- Verify both landings independently (release tag over git transport; the Pages
  site over HTTPS with a real-content snippet).
- Flip both `arcade.json` entries to a resolved shape (match the mineverse
  entry: availability set, url set, no `blocker` key).
- Rebake `review/data/releases.json` via `python3 review/gen_releases.py`;
  lumen-drift drift → false (expected tag == live tag).
- Mark ASK-0010 + ASK-0011 satisfied in `docs/owner/OWNER-ACTIONS.md`.
- Repoint `botsite/tests/test_arcade.py` (the whole arcade is now reachable:
  3 live, 0 blocked, 0 owner clicks; retire the games-web dead-URL pin).
- Full gate green, then flip this card.

⚑ Self-initiated: no — coordinator-dispatched, executing the recorded owner
clicks for ASK-0010 and ASK-0011.

## What was done

[[fill: what was done — completed on the flip commit]]

## 💡 Session idea

[[fill: session idea]]

## ⟲ Previous-session review

[[fill: previous-session review]]
