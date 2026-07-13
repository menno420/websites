# 2026-07-13 — review: bake-time questions sync from [program-review] issues

> **Status:** `in-progress` — branch `claude/review-questions-bake-sync-0713`; flips to `complete`
> + PR number as the deliberate LAST code step.

- **📊 Model:** Claude Fable 5 · worker · backlog-promotion-slice

**What this session was about:** backlog promotion — the `docs/ideas/backlog.md`
bullet "Bake-time questions sync from GitHub issues" (`captured`, source
`.sessions/2026-07-11-review-site-expansion.md` 💡). The review site's
`/questions` ledger is a hand-kept `review/data/questions.json`, honest-empty
today (docs/current-state.md §review); the `review-bake` workflow already runs
three stdlib-only generators with the Actions token, so a fourth —
`review/gen_questions.py` — lists this repo's issues titled `[program-review]`
(one capped REST call) and merges them into the ledger automatically (asked
date, url, open/closed status), preserving the hand-written answer links.

## What was done

- (in progress)
- Verified: (pending)

⚑ Self-initiated: no — backlog promotion of the captured
"Bake-time questions sync from GitHub issues" bullet
(`docs/ideas/backlog.md`, source `.sessions/2026-07-11-review-site-expansion.md` 💡).

## 💡 Session idea

(to be filled at close-out)

## ⟲ Previous-session review

(to be filled at close-out)
