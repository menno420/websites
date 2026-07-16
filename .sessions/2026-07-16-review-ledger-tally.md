# 2026-07-16 — Review Problems/Successes: at-a-glance documented-count tally

> **Status:** `complete` — branch `claude/review-ledger-tally`; the review
> service's Problems and Successes pages lead a long card stack with no sense of
> scale. This slice adds a small hero tally ("N documented problems · K full
> incident writeups", "N documented wins") backed by a pure
> `story.ledger_summary(items)` helper, so the count equals the number of cards
> rendered below and can never drift. Read-only; no new route, no state change.
> Verify: `1636 passed` (all four suites); kit `--strict` passes once the card
> flips complete. +6 review tests.

- **📊 Model:** Claude Opus · high · feature build

**What this session is about:** a reviewer landing on `/problems` (the site's
lead page) or `/successes` scrolls a long `rv-story-card` stack with no
one-glance count of how big the ledger is. Sibling services just shipped the
same at-a-glance-count idiom (dashboard `/ideas` → `N ideas · K shipped`,
botsite `/games` → arcade availability strip). This slice brings the idiom into
`review/`: a pure `story.ledger_summary(items)` helper returns
`{total, detailed}` (detailed = entries carrying a structured `details`
incident timeline), and both heroes render a badge tally. The secondary badge
shows only when `detailed > 0`, so Problems surfaces its one full incident
writeup while Successes (no details) stays a clean total — the conditional is
exercised in both directions. Read-only: no new route, no POST, no CSRF
surface. Contained to `review/` (story.py + two templates + test); no
cross-service import.

💡 Idea: the homepage "how this site is organized" site-map lines could each
carry their section's count (`Problems — 9 documented`, `Q&A — 13 answered`),
turning the front-door map into a scale-at-a-glance index — same
single-source-of-truth `len()` discipline, one glance from the overview.

**Previous-session review**
(`.sessions/2026-07-16-games-availability-summary.md`): exemplary
single-source-of-truth discipline — the `/games` front door reused
`arcade.availability_summary` rather than recomputing counts. This session
follows the same rule: `ledger_summary` counts the very lists the templates
iterate, so the hero tally equals the cards rendered below it with no second
source to drift.
