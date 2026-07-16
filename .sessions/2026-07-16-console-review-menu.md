# Session card — console + review overnight planning menu (2026-07-16)

> **Status:** complete

- **📊 Model:** opus-4.8 · high · idea/planning

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

## 💡 Session idea

**Bundle the pure test/guard proposals into one zero-risk green PR (menu X2)** — C9, C10, C11, R6, R7 are all coverage-only additions with no behavior change, so they can land together as a single low-risk PR the moment the owner greenlights, independent of the feature votes. Worth having because it converts the menu into an immediate coverage win with zero product risk — landable before any of the larger votes resolve. Deduped against `docs/ideas/backlog.md` + the queue-state NEXT list: no existing bullet bundles these five test/guard gaps; the closest (fast-lane pin-map drift, env-sweep coverage) each cover one specific gate, not this cross-service bundle. Captured in `docs/ideas/backlog.md` (the overnight-menu bullet; X2 within `docs/planning/2026-07-16-console-review-menu.md`).

## ⟲ Previous-session review

The release-drift session (`.sessions/2026-07-16-release-drift.md`) landed a clean `check_release_drift()` pass and a well-scoped `drift_report()` backlog idea — good, honest, deduped. What it missed: it left the buildable backlog thin enough that the owner had to issue a LIVE OVERNIGHT ORDER to plan excessively, which this session answers.
