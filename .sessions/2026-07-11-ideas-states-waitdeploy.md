# 2026-07-11 — /ideas state surfacing (conveyor health) + scripts/wait-deploy poller

> **Status:** `complete` — PR #92 (`claude/ideas-states-waitdeploy`),
> squash-merge on `quality` green. (Flipped after the PR existed.)

- **📊 Model:** Claude Fable 5 · worker · routine-fired build slice (continuous mode, slice 13 — 02:57Z nudge)

**What this session was about:** the 02:57Z send_later continuation.
Collision check: heartbeat at HEAD is this chain's 02:35Z stamp — clear.
Inbox: nothing past 009. Work-ladder rung 3, coordinator picks (a)+(c)
bundled ((b) nav overflow guard left for a deliberate design slice; the
healthcheck cron verdict deliberately NOT re-checked early — due 06:17Z):
**(a)** `/ideas` state surfacing — front-matter `state:` badges + per-repo
lifecycle counts + `?state=` filter, the conveyor-health glance; **(c)**
`scripts/wait_deploy.py` — the post-merge sha-convergence poller that turns
the manual "merge = deploy" verification loop into a deterministic
PASS/FAIL (this chain has hand-curled `/version` twelve times tonight).

## What was done

- **(a) `/ideas` state surfacing**: `ideas.extract_state` reads ONLY the
  front-matter block and only the four lifecycle tokens (else `unstated`,
  never guessed — a body sentence mentioning "state:" cannot classify an
  idea); per-idea state badges; per-repo captured/planned/built/retired/
  unstated count chips (honest scope: the newest ENRICHED files, labeled
  "of the newest N" — unfetched files are never counted); `?state=` filter
  narrows the DISPLAYED list but never the counts; unknown filter values
  flag a banner and drop nothing. Routes pass the param; `/ideas.json`
  additive.
- **(c) `scripts/wait_deploy.py`** (+ provenance/kill-switch header): polls
  the three `/version` endpoints every 10s until a given sha converges
  (prefix-tolerant, min 7 chars, never empty-matches) or times out with the
  per-service last-seen state (an unreachable endpoint counts as
  not-converged with its error shown, never a guess). **First live run:
  `CONVERGED: all 3 services at 7f948445`, exit 0, one poll.**
- **`tests/test_ideas_states_waitdeploy.py`** (+5, suites 212 → 217):
  front-matter-only + known-tokens-only extraction; per-repo counts +
  per-idea states; filter narrows list not counts (incl. `unstated` and the
  unknown-filter flag); page chips/badges/banner render; `converged`
  prefix/empty/min-length semantics.
- **Backlog:** `/ideas` state filter → Built; `wait-deploy.py` → Built. No
  decision-ledger entry — additive view polish + a convenience script.

## Close-out (auto-drafted 2026-07-11 — edit, don't author)

<!-- substrate:auto-draft -->

**Evidence (auto-collected — verify, then keep or correct):**

- files touched: `app/ideas.py`, `app/main.py` (`_state_param` + routes),
  `app/templates/ideas.html`, `scripts/wait_deploy.py` (new),
  `tests/test_ideas_states_waitdeploy.py` (new), `docs/ideas/backlog.md`,
  this card — the auto-draft had no session-start anchor; list verified by
  hand against `git diff origin/main --stat`.
- git: branch `claude/ideas-states-waitdeploy`, HEAD 0ed3c4fc4 at draft
  time (this flip commit supersedes it).
- verify: `python3 -m pytest tests/ botsite/tests dashboard/tests -q` —
  **217 passed**; `python3 bootstrap.py check --strict` — **all checks
  passed** with this card complete (kit v1.8.0); `wait_deploy.py` live-run
  CONVERGED (output above).

**Judgment (the half only the session knows — resolve every slot):**

- Decisions made: counts-over-enriched-only as the honest scope for
  conveyor health (counting unfetched files would require unbounded
  fan-out; the label says exactly what is counted); the filter narrows the
  list, never the truth.
- Next session should know: **healthcheck cron verdict due after 06:17Z**
  (a second no-show upgrades the provisional CAPABILITIES wall — and
  `wait_deploy.py` + wake-run healthchecks become the standing doctrine);
  remaining backlog picks: nav overflow guard (design slice), cron-slot
  helper, review-row auto-check, backlog fact-check pass, board-row idea
  chips (this slice's 💡).

⚑ Self-initiated: no — coordinator picks (a)+(c), both backlog promotions
(rung 3).

## 💡 Session idea

**Conveyor-health chips on the readiness board's repo rows** — the board
(`/`) is the owner's first glance and now `/ideas` computes lifecycle
counts per repo; one small chip per board row ("ideas: 3c/1b") would put
conveyor health where the owner already looks, reusing `repo_ideas`'s
cached counts (zero new fetch when the TTL cache is warm). Worth having
because /ideas is a destination page while the board is the habit — health
signals belong on the habit path. Deduped against `docs/ideas/backlog.md` +
queue-state NEXT: nothing covers board-row idea chips. Captured in
`docs/ideas/backlog.md`.

## ⟲ Previous-session review

Slice 12 (same chain, PR #90) turned a coordinator verdict-check into three
durable artifacts (evidence, tooling, telemetry) and owned this chain's own
cron-arithmetic error in public — the record self-corrected; what it
missed: `open_work.py` shells out to `git fetch` per branch serially, which
will crawl on a repo with many stale branches — fine at four, worth a batch
fetch if the branch count ever grows (noted here so the next toucher knows
the known limit).
