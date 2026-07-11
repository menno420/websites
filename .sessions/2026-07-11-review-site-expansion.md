# 2026-07-11 — review/ expansion: fleet coverage, dynamic stats, continuous reviews, questionnaire

> **Status:** `complete` — branch `claude/review-site-expansion`, PR #141.

- **📊 Model:** claude-fable-5 · worker (owner expansion directive) · feature-build

**What this session was about:** Owner expansion directive for the `review/`
service (landed as PR #132): all fleet repos properly featured, dynamic
stats, the site as a channel for CONTINUOUS reviews to Anthropic, room to
interact, and an evidence-backed questionnaire. Rung: owner-directed (not an
inbox order; scope verified unclaimed against control/status.md at HEAD
`fc8087c` and zero open PRs).

## What was done

- **Fleet coverage:** `review/gen_fleet.py` bakes the fleet-manager registry
  (LANES literal, raw fetch + ast.literal_eval, fail-soft) + every
  repo-backed lane's heartbeat into `review/data/fleet.json` (per-field 600
  char cap, truncation marked). New `/fleet` + `/fleet/{repo}` +
  `/fleet.json` on `review/fleetdata.py` (injectable `now=` everywhere —
  clock-freeze discipline). **18-vs-19 resolved honestly:** the registry has
  19 seats = 18 repo-backed + 1 registry-only (retro-games coordinator,
  `repo: None`); counts rendered as baked, never hardcoded.
- **Dynamic stats:** `.github/workflows/review-bake.yml` (daily cron `23 5 *
  * *` + dispatch; NOT push-triggered — no loop) regenerates
  snapshot/fleet/stats and lands the data-only diff: direct push → `[bake]`
  PR + auto-merge → visible open PR. `review/gen_stats.py` = 2 capped
  fail-soft REST calls/repo; stats.json deliberately absent until the first
  CI bake (pages say so). As-of stamps everywhere; 48h stale banners;
  site-wide snapshot-aging banner (deployed sha vs baked sha — backlog idea
  built).
- **Continuous reviews:** `review/editions.py` (front-matter + markdown
  under `review/data/reviews/`), `/reviews` index + `/reviews/{slug}` +
  valid Atom feed `/reviews/feed.xml` (ElementTree; valid when empty; entry
  ids = GitHub blob URLs). Edition #1 seeded from the ORDER 011 self-review.
  Publishing ritual + template in `review/README.md`.
- **Interaction (read-only):** `story.ask_url()` prefilled new-issue links
  on every page; `/questions` ledger (`review/data/questions.json`, honest
  empty state) + intake convention documented. No form/DB — flagged as a
  future owner option.
- **Questionnaire:** `/questionnaire` — 12 questions in `story.QUESTIONNAIRE`,
  each answered from repo evidence with citations; live answer-bot flagged
  owner-gated (needs a model key).
- Docs: current-state entry, OWNER-ACTIONS review-service ask extended +
  PAT-unlocks-richer-stats side-note, backlog ideas filed.
- Verified: `python3 -m pytest review/tests -q` — 67 passed (was 28);
  `python3 -m pytest tests/ botsite/tests dashboard/tests review/tests -q` —
  322 passed; `python3 bootstrap.py check --strict` — green (only the
  designed born-red hold before this flip).

⚑ Self-initiated: no — owner expansion directive, relayed by the coordinator.

## 💡 Session idea

**Bake-time questions sync from GitHub issues** — a fourth generator in the
review-bake workflow lists issues titled `[program-review]` (one REST call
on the Actions token) and merges them into `questions.json` automatically.
Worth having because the interaction loop's slowest step is a session
noticing a question exists — the bake noticing daily makes the ledger honest
by default. Deduped against `docs/ideas/backlog.md` + the queue-state NEXT
list: nothing covers questions intake. Captured in `docs/ideas/backlog.md`
(plus the owner-gated answer-bot flag from the directive).

## ⟲ Previous-session review

The continuous-mode chain (slice 31, #139) landed clean and its heartbeat
was accurate to the file; what it missed — nothing structural, though the
review service it left behind still described itself as a one-shot snapshot
site, which this session made untrue in the good direction.

## Park record

#141 green-clean at merge head 1f90d8b55316f13f09888444b27ff3424a5890c3
(post-wave merge of origin/main; this park-record commit sits atop it as the
branch tip — a commit cannot cite its own SHA), awaiting owner squash-merge
(workflow file → owner-click-only); after merge: Railway service
root=review, then one manual review-bake run.
