# 2026-07-13 — review: bake-time questions sync from [program-review] issues

> **Status:** `complete` — PR #297, branch
> `claude/review-questions-bake-sync-0713`; the review site's /questions
> ledger now fills itself from GitHub issues titled `[program-review]` at
> every review-bake run — intake automated, answers stay human.

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

- `review/gen_questions.py` (new, stdlib-only, mirrors `gen_stats.py`'s
  `_api`/urllib pattern incl. optional GITHUB_TOKEN + 20s timeout): one
  capped call `GET /repos/menno420/websites/issues?state=all&per_page=100`;
  filters titles carrying `[program-review]` (case-insensitive), excludes
  PR objects (`pull_request` key); maps each match to a ledger record
  (`asked` = created_at date, `title`, `url`, `status` open/closed) that
  satisfies the existing /questions filter semantics
  (`story.question_status` / `question_answer_state`); merges keyed by
  issue url into the committed file — existing records keep position and
  every hand-written field (`answer_url`/`answer_label`; a truthy
  `status_override` pins a hand-set status against the live state), new
  records append oldest-asked-first, the honest `note` stays, `updated`
  refreshes only on real change (no daily stamp-only churn). ANY failure
  (HTTP error, timeout, bad JSON, unreadable/malformed committed file)
  leaves questions.json byte-identical and exits 0.
- `.github/workflows/review-bake.yml`: `python3 review/gen_questions.py`
  in the bake step, `git add review/data/questions.json` in the explicit
  staging block, header comment's file list extended — same style as the
  three existing generators.
- `review/tests/test_gen_questions.py` — 11 network-free tests
  (fetch monkeypatched): marker filter in/out + case-insensitivity,
  PR-object exclusion, field mapping + asked-date extraction, closed
  mapping, answer-link preservation, status-override pin, dedup by url +
  oldest-first append + repeat-bake byte-stability, fail-soft
  byte-identical + exit 0 on fetch failure, honest-empty ledger kept
  byte-identical on empty result, updated-stamp format + note survival.
- No route/app change; `review/data/questions.json` untouched in the PR —
  it stays honest-empty until the bake finds a real question.
- `docs/ideas/backlog.md`: promoted bullet flipped to `built`; this
  session's 💡 captured as a new bullet.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — 1293 passed, 1 warning (+11 over main's 1282);
  `python3 bootstrap.py check --strict` — green except this card's own
  designed born-red HOLD (flipped by this commit) and the pre-existing
  never-exit-affecting `owner-action-fields` advisory on
  control/status.md (not owned here).

⚑ Self-initiated: no — backlog promotion of the captured
"Bake-time questions sync from GitHub issues" bullet
(`docs/ideas/backlog.md`, source `.sessions/2026-07-11-review-site-expansion.md` 💡).

## 💡 Session idea

**Closed-but-unanswered nag for the questions ledger** — the sync now
flips a record's status to `closed` when its issue closes, but the answer
link stays hand-written, so a question can end its life as
"closed / pending" with no published answer on record; a bake-time or
CI-time advisory flagging `status == closed` with no `answer_url` (pure
read of the committed file, no network) would turn that silent gap into a
visible nag. Worth having because automating intake makes it POSSIBLE to
close a question without answering it on record — exactly the quiet
dishonesty the ledger exists to prevent. Deduped against
`docs/ideas/backlog.md` + the queue-state NEXT list: the bake-sync bullet
(now built) covers intake only, the owner-gated answer-bot bullet covers
generating answers; nothing audits answer-lag. Captured in
`docs/ideas/backlog.md`.

## ⟲ Previous-session review

The venture-vetting-catalog session (PR #248) did well — 22 packets
curated with per-title honest states, everything pinned to venture-lab
@ `2c039e3`, and a registry-pinning test that makes drift loud; what it
missed: the pin is static and its own 💡 (the sha-drift nag) is exactly
the decay guard it shipped without, so the catalog starts rotting the
moment the vetting lane moves.
