# 2026-07-13 — review privacy lint: accent-aware private-token gate over all routes + data

> **Status:** in-progress — branch `claude/review-privacy-lint`; flips to
> `complete` + PR number as the deliberate LAST code step.

- **📊 Model:** Fable 5 · worker · feature-slice (test suite)

**What this session was about:** backlog promotion rung under ORDER 022
item 2 ("keep executing the existing plan to completion … the Anthropic
review site") — executes the captured bullet "Site-wide privacy lint for
the review service" (`docs/ideas/backlog.md`, captured 2026-07-12 by the
ORDER 017 D private-lane-filter session). Today's regression tests pin
only `/`, `/fleet`, `/fleet.json` and the committed mirrors; this session
builds the promised single suite that walks EVERY GET route in
`review/app.py` plus every committed `review/data/**` file and asserts no
private-lane token appears — accent-aware (`pok[eé]mon…`), because the
original escapees were an accented "Pokémon" that plain `grep -i pokemon`
missed. Zero network, PR #225-shaped: explicit per-entry-justified
allowlist, stale-allowlist rejection, headline failures naming route +
token.

## What was done

- (fills in at close-out)

⚑ Self-initiated: no — ORDER 022 item 2 follow-through, executing the
committed backlog bullet.

## 💡 Session idea

- (fills in at close-out)

## ⟲ Previous-session review

- (fills in at close-out)
