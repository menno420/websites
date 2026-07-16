# Session card — console + review overnight planning menu (2026-07-16)

> **Status:** in-progress

📊 Model: claude-opus family · high effort · task-class: planning/docs

## Goal
Per owner LIVE OVERNIGHT ORDER (event 55f13541): the buildable backlog is thin, so PLAN EXCESSIVELY. Produce a veto-ready MENU of 25+ genuinely distinct proposals across the control-plane launch console (`app/`) and the review service (`review/`) — small fixes through ambitious features — for the owner to skim and veto in the morning. Quantity is deliberate; the owner's veto is the filter. Docs-only tonight (do NOT build the ambitious ones).

## What shipped
- `docs/planning/2026-07-16-console-review-menu.md` — 25+ distinct proposals grouped by service, each with title · pitch · effort (S/M/L) · risk/reversibility (✅/↩️/⚠) · what it unblocks. Grounded in a fresh read of `app/` (34 routes, readiness/journal/github domain) and `review/` (20 routes, editions/fleetdata/story/ai + bake generators).

## Verify
- `python3 bootstrap.py check --strict` — pass (docs-only; the four pytest suites unaffected).

## Landing
Branch `claude/console-review-menu-20260716`, draft PR. Born-red card holds the PR red until this flips complete. Landing gated on the auto-merge draft-gap fix — leave as a green ready-to-land draft; named blocker: awaiting owner morning go-ahead.

## Next
Owner skims the menu, vetoes; surviving picks become idea-backlog bullets / build slices.
