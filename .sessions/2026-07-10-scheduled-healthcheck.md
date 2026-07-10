# 2026-07-10 — Scheduled healthcheck workflow: standing liveness verification (backlog promotion)

> **Status:** `complete` — PR #69 (`claude/scheduled-healthcheck`),
> squash-merge on `quality` green. (Card flipped AFTER the PR existed — the
> number is real, not predicted; slices 1+2 both mispredicted theirs.)

- **📊 Model:** claude-fable-5 · worker · routine-fired build slice (continuous mode, slice 3)

**What this session was about:** slice 3 of the 20:00Z continuous-mode wake
(manager Q-0265). Work-ladder rung 3 (backlog promotion) — the queue-state
NEXT list is exhausted (items 1–4 DONE, item 5 IS the backlog), inbox at HEAD
has nothing past 008. Promoted the highest-value buildable `captured` idea:
**scheduled healthcheck workflow**
(`docs/ideas/scheduled-healthcheck-workflow-2026-07-10.md`, retro F3) — an
Actions cron running the repo's own `scripts/healthcheck.py` so liveness
stops depending on a session remembering to probe.

## What was done

- **`.github/workflows/healthcheck.yml`** (new, the whole feature): cron
  `17 */6 * * *` (minute-17 offset — GitHub documents top-of-hour cron
  congestion can delay/drop runs) + `workflow_dispatch`; checkout →
  Python 3.12 → `pip install -r requirements.txt` (the script imports
  `app.fleet` — the SAME parser `/fleet` uses, which is the point of the
  manifest smoke half) → `python3 scripts/healthcheck.py` (three live
  services `/healthz` + `/` must be 200; live fleet-manifest must parse to a
  non-empty lane set). Read-only: no secret, no Railway credential, no write.
  Deliberately NOT a required check — failure notifies via the
  failed-workflow email the owner already receives.
- **Docs:** D-0029 appended to `docs/decisions.md`; backlog bullet `captured`
  → Built; idea file front-matter flipped to `state: built` + shipped
  reference.
- The first `quality` run on this PR concluded FAILURE **by design** — the
  born-red session gate holding the merge while this card was in-progress
  (plus its unresolved auto-draft fills); this flip commit is what drives it
  green.

## Close-out (auto-drafted 2026-07-10 — edit, don't author)

<!-- substrate:auto-draft -->

**Evidence (auto-collected — verify, then keep or correct):**

- files touched: `.github/workflows/healthcheck.yml` (new),
  `docs/decisions.md` (D-0029), `docs/ideas/backlog.md`,
  `docs/ideas/scheduled-healthcheck-workflow-2026-07-10.md`, this card.
- git: branch `claude/scheduled-healthcheck`, HEAD 5c80c4af3 at draft time
  (this flip commit supersedes it).
- verify: `python3 -m pytest tests/ botsite/tests dashboard/tests -q` —
  **157 passed**; `python3 bootstrap.py check --strict` — **all checks
  passed** with this card complete. Workflow YAML parses
  (`yaml.safe_load`: name `healthcheck`, triggers `schedule` +
  `workflow_dispatch`). `scripts/healthcheck.py` run live this session:
  6/6 PASS + manifest 13 lanes.

**Judgment (the half only the session knows — resolve every slot):**

- Decisions made: D-0029 (scheduled healthcheck workflow — non-required,
  read-only, 6-hourly + dispatch; ledger is the one home). Flip-after-PR
  adopted as this lane's card discipline (see ⟲ below).
- Next session should know: verify the workflow's first run actually
  happened — `workflow_dispatch` post-merge if the loop reaches it (result
  in the follow-up heartbeat), else the first cron fire is ~02:17Z; if the
  Actions tab shows no `healthcheck` run by then, the schedule is silently
  dead — treat as a bug, not a wait. Then resume work-ladder rung 3
  (backlog: own-heartbeat parse self-check or `/fleet` manifest badge are
  the smallest buildables).

## Post-merge run

Recorded after merge in the follow-up heartbeat (`control/status.md`), since
this card merges with the PR itself: first run triggered via
`workflow_dispatch`; if the dispatch could not be triggered or watched, the
exact error is recorded there instead — cron's first scheduled fire is
~02:17Z either way.

## 💡 Session idea

**Healthcheck failure auto-files a GitHub issue** — extend the scheduled
workflow so a failed run opens (or updates, dedup by title) an issue in this
repo with the probe table. Worth having because the failed-workflow email
goes only to the owner's inbox, while an ISSUE is visible to every agent
surface we already have (`/activity`, session PR-list checks, the manager) —
downtime becomes actionable work an agent can pick up from the bus instead
of news only the owner sees. Deduped against `docs/ideas/backlog.md` +
queue-state NEXT: nothing covers alert routing to agent-visible surfaces;
the wait-deploy.py capture is post-merge convergence, not standing alerts.
Captured in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

Slice 2 (same wake, PR #67) did the verification well — it found and fixed a
LIVE parse bug (the `routine:` line leaking into `blockers:`) because it
render-smoked the real page instead of trusting unit tests; what it missed:
it wrote the predicted PR number (#66) on the card and in two docs before
the PR existed, guessed wrong when a sibling took #66, and paid a fixup
commit + a full quality re-run. Workflow improvement, applied this slice:
flip the card only after the PR number is real.
