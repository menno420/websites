# 2026-07-13 — botsite Strategy Graveyard leaderboard (/graveyard)

> **Status:** `complete` — PR pending on branch `claude/strategy-graveyard`
> (READY at open; lands via the auto-merge enabler on green). The botsite
> `/graveyard` page ships with its bake script, committed data, and a
> 17-test offline suite.

- **📊 Model:** Claude Fable 5 · worker · feature-slice

**What this session is about:** a new GET-only botsite page, `/graveyard` —
the honest ledger of the trading-strategy lane's experiment sweep: every
configuration evaluated, grouped by verdict and strategy, with the plain
truth (0 promoted) as the headline. Data arrives the review-service way: a
bake script (`botsite/gen_graveyard.py`) fetches
`menno420/trading-strategy` `experiments/index.jsonl` at bake time and
commits a compact `botsite/data/graveyard.json`; the request path reads only
the committed JSON — no live cross-repo fetch. Rung: ORDER 022 item 4
(SCAN AND INITIATE — venture WEBSITE-IDEA batch-2 intake:
strategy-graveyard leaderboard).

## What was done

- **`botsite/gen_graveyard.py`** (new): the bake half, on the
  `review/gen_fleet.py` pattern — fetches the ~256KB ledger, validates each
  JSONL record (malformed lines skipped + counted, never fatal), and writes
  the compact committed `botsite/data/graveyard.json` (14KB). Real ledger
  schema (verified this session): 551 records with `run_id`, `file`,
  `strategy`, `instrument`, `timeframe`, `params`, `sharpe`,
  `benchmark_sharpe`, `cagr`, `max_drawdown`, `data_start`, `data_end`,
  `variants_tried` (+ `holdout_unlocked` on 13) — **no verdict field**, so
  verdicts are DERIVED at bake time with the lab's own documented dev rule
  (trading-strategy `docs/research-round-3-results.md`): KEEP (dev-candidate
  only) when stitched-OOS Sharpe beats the same-window buy-and-hold
  benchmark, KILL otherwise; PROMOTED recorded explicitly as 0 (the lab's
  holdout is spent, promotion closed). `source_sha` over anonymous git
  transport (the REST API is walled from session containers); fail-soft
  everywhere (a failed fetch leaves the old committed file untouched).
- **Baked data**: 551 runs / 7,771 configuration evaluations · 0 PROMOTED /
  190 keep / 361 kill · 24 strategies · 17 instruments · daily+hourly ·
  best Sharpe 2.332, median 0.724 · source HEAD `de5a477e`.
- **`botsite/graveyard.py`** (new): runtime loader on the
  `puddle_museum.py` pattern — committed JSON only, shape-validated;
  missing/corrupt/misshapen file degrades to `available: False` with the
  exact reason, never a 500 and never invented data.
- **`/graveyard` route + nav entry** in `botsite/app.py` (GET-only) and
  `botsite/templates/graveyard.html`: clarity-bar hero (`sb-page-hero` +
  `sb-lead`), the honest headline banner ("7,771 CONFIGURATIONS TESTED
  ACROSS 551 RECORDED RUNS · 0 PROMOTED"), a three-card verdict board where
  the zero is presented plainly as the point, a per-strategy leaderboard
  table (runs/evals/keep/kill/best Sharpe/best CAGR/worst drawdown), top-20
  KEEP and top-20 KILL tables, and a provenance footer (as_of, source sha,
  data window, holdout note, skip count).
- **`botsite/tests/test_graveyard.py`** (new, 17 offline tests): page
  renders vs the REAL baked aggregates (never hardcoded copy), the
  load-bearing zero asserted in data AND copy, GET-only (POST 405, no
  forms), nav entry, missing/corrupt-file empty states, committed-JSON
  shape + internal consistency + <50KB compactness, and the bake script's
  pure transform (`parse_records` / `derive_verdict` /
  `compute_graveyard`) fed fixture records — zero network. The structural
  clarity gate (`test_clarity_structure.py`) walks the new route
  automatically and passes unchanged.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — 1107 passed, 1 warning (includes the 17 new graveyard
  tests); `python3 bootstrap.py check --strict` — green apart from this
  card's own designed born-red HOLD (flipped by this close-out) and the
  pre-existing `owner-action-fields` advisory on control/status.md (never
  exit-affecting, not owned here).

**Decisions made (decide-and-flag):** the task brief assumed a per-record
verdict field and ~3,468 configs; the real ledger has neither — verdicts
are bake-derived with the lab's documented rule and labeled as derived on
the page, and the honest computable aggregates (551 runs / 7,771 variant
evaluations summed from `variants_tried`) replace the assumed count. The
REST API sha probe failed (session proxy wall: "GitHub access to this
repository is not enabled for this session"), so `source_sha` rides
anonymous `git ls-remote` — the `gen_fleet.py` head_probe idiom.

⚑ Self-initiated: yes — ORDER 022 item 4 (WEBSITE-IDEA batch-2 venture
intake); contained to botsite/ + card/claim files and fully reversible.

## 💡 Session idea

**Wire the graveyard bake into the scheduled review-bake workflow** — the
committed `graveyard.json` ages from the moment it lands; the repo already
has a scheduled bake lane (the `review-bake` GitHub Actions workflow runs
`review/gen_*.py`), and adding `python3 botsite/gen_graveyard.py` to it
would keep the graveyard current with zero new machinery. Worth having
because a leaderboard whose `as_of` silently ages toward stale undercuts
the page's whole honesty premise. Deduped against `docs/ideas/backlog.md`
(zero graveyard/trading hits) + the queue-state NEXT list: new. Not
appended to backlog.md this session — the session's binding scope rails
limit writes to botsite/ + card/claim files; captured here on the card
instead.

## ⟲ Previous-session review

The repo-freshness session (#235) did well — its offline monkeypatched
suite and its "unknown — reason" never-fabricate rows set the bar this
session followed for the graveyard's empty states and derived-verdict
labeling; what it missed (nothing structural) was small: its card's idea
(autorefresh) stayed uncaptured in backlog.md, a gap this card at least
names explicitly when doing the same under scope rails.
