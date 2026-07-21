# Review: link /releases.json from the fleet page

- **Status:** complete
- **📊 Model:** opus-4.8 · medium · feature build
- **💡 Idea:** A data endpoint that only surfaces via a conditionally-hidden banner is effectively orphaned when the condition is false — link it next to its siblings so it's always findable, not only in an error state.
- **⟲ Previous-session review:** The closeout (#472) and records true-up (#473) both landed clean with named-path staging + valid PL-004 class + the flip dropping its claim in-commit; same discipline here.

## What
Add a `/releases.json` link on the review `/fleet` page next to `/fleet.json` and `/story.json`, closing the one findability gap the review-site audit found (the live release-drift mirror was only reachable via the drift banner, suppressed at drift_count=0).

## Verify
- `unset DATABASE_URL; python3 -m pytest review/tests -q`
- `unset DATABASE_URL; python3 bootstrap.py check --strict --added-card .sessions/2026-07-21-review-releases-link.md`
