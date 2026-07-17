# Session — review Successes/Problems evidence-citation tally

> **Status:** `in-progress`

- **📊 Model:** Claude Opus · high · feature build

## Goal
The review service's Successes and Problems pages are the site's two flagship "with receipts"
surfaces — every claim links to committed evidence. The hero tally already counts the entries
(`N documented wins` / `N documented problems`, plus problems' `N full incident writeups`), but
the receipts themselves — the evidence citations the pages actually render — go uncounted.
Surface an evidence-citation tally in both heroes so a reviewer sees, at a glance, how densely
the claims are sourced (e.g. `7 documented wins · 19 evidence citations`).

## Scope
- `review/` only. `story.ledger_summary()` gains a pure `citations` count summing each entry's
  top-level `evidence` links plus any nested `details[].evidence` (problems' incident timelines),
  counted off the very lists the templates iterate so it can never drift from what renders.
  `successes.html` / `problems.html` add one neutral badge beside the existing tally. Read-only,
  additive, reversible by revert. No cross-service import; vendored `listfilter`/partials untouched.

## 💡 Session idea
Every evidence-linked surface on this site (the Q&A page, the "start here" homepage cards, the
review editions) is sourced the same way; a shared `citation_density` helper could let each page
badge its own sourcing depth, turning "we cite everything" from a claim into a visible, per-page
number the reviewer can spot-check.

## ⟲ Previous-session review
`.sessions/2026-07-17-dashboard-idea-status-filter.md` (complete) turned the dashboard `/ideas`
aggregate into something the owner can act on with a lifecycle-status filterbar — well-scoped,
fail-soft, single-service. This session follows the same "make an existing aggregate legible"
instinct one service over on the review site, quantifying the sourcing the pages already promise.
