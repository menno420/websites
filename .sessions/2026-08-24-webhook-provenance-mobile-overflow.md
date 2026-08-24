# 2026-08-24 — Webhook provenance mobile overflow

> **Status:** `in-progress`

- **📊 Model:** GPT-5 · high · deployed browser regression

**What this session is about:** Close the one remaining failure from the post-deployment canonical browser crawl: SuperBot `/webhook-analyzer` makes the body 13 px wider than the exact 375 px phone viewport in CI. Trace the concrete overflowing content, repair it without hiding real page overflow or removing the result table's local horizontal scroller, prove the exact live geometry through the unchanged crawl, and merge the finished green repair under Menno's standing approval.

## What remains

- Pin the source element responsible for the CI-only 388 px body width.
- Add the narrowest source and regression repair.
- Run focused and full repository gates, open a PR, merge only when green, verify deployment convergence, and rerun the unchanged live browser smoke to green.

⚑ Self-initiated: no — this is the final measured follow-up to Menno's requested first truth-and-defects tranche.

## 💡 Session idea

Pending; the live regression comes first.

## ⟲ Previous-session review

PR #514 repaired the three known post-deployment misses and passed direct 390 px use, but the unchanged canonical crawl's exact 375 px Linux browser exposed one smaller provenance-layout edge that the earlier manual viewport did not reproduce.
