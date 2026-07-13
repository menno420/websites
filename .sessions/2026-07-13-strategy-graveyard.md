# 2026-07-13 — botsite Strategy Graveyard leaderboard (/graveyard)

> **Status:** `in-progress` — branch `claude/strategy-graveyard`; flips to `complete`
> + PR number as the deliberate LAST code step.

- **📊 Model:** Claude Fable 5 · worker · feature-slice

**What this session is about:** a new GET-only botsite page, `/graveyard` —
the honest ledger of the trading-strategy lane's experiment sweep: every
configuration tested, grouped by verdict and strategy, with the plain truth
(0 promoted) as the headline. Data arrives the review-service way: a bake
script (`botsite/gen_graveyard.py`) fetches
`menno420/trading-strategy` `experiments/index.jsonl` at bake time and
commits a compact `botsite/data/graveyard.json`; the request path reads only
the committed JSON — no live cross-repo fetch. Rung: ORDER 022 item 4
(SCAN AND INITIATE — venture WEBSITE-IDEA batch-2 intake:
strategy-graveyard leaderboard).

## What was done

- (in progress)

⚑ Self-initiated: yes — ORDER 022 item 4 (WEBSITE-IDEA batch-2 venture
intake); contained to botsite/ + card/claim files and fully reversible.

## 💡 Session idea

- (to be filled at close-out)

## ⟲ Previous-session review

- (to be filled at close-out)
