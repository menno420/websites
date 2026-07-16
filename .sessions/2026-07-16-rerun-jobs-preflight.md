# 2026-07-16 — Owner console: rerun-ci preflight names the JOBS, chip verifies them

> **Status:** `complete` — branch `claude/rerun-jobs-preflight-20260716`
> (draft PR opened from this branch right after this flip); the rerun-ci
> preflight facts table now names exactly which failed jobs the fire will
> re-run, and the post-fire chip verifies those jobs re-queued at the JOB
> level.

- **📊 Model:** fable · high · feature build (maintenance wake — launch-console increment: jobs-level rerun-ci preflight)

**What this session is about:** the "failed-JOBS preflight detail" baton
item from `control/status.md` (NEXT-2-TASKS: "resume console/arcade
increments (ideas on file: stable ask IDs, failed-JOBS preflight detail)"),
originated as the 💡 idea in `.sessions/2026-07-15-rerun-preflight.md`.
Today the rerun-ci preflight names the RUN (id, workflow, age, link) but
`rerun-failed-jobs` actually re-runs a SUBSET — the run's failed jobs.
This slice makes the confirm claim precise down to the job names:

- `app/github.py` gains `run_jobs` (read-only GET
  `/repos/{o}/{r}/actions/runs/{id}/jobs`, honest result envelope) and the
  pure `failed_jobs` filter;
- the preview facts table gains one row — "jobs that will re-run:
  `quality` (1 of 3 jobs)" — degrading honestly ("unknown — could not list
  jobs (…)") without ever blocking the preview;
- the post-fire verification chip verifies THOSE jobs flipped to
  queued/in-progress (job-level re-GET), falling back to the existing
  run-level check when the jobs listing is unavailable;
- test-covered in `tests/test_owner_preflight.py` (+ the one touched
  contract test in `tests/test_app.py`).

⚑ Self-initiated: no — the status.md next-2-tasks baton names this item;
rung (b) of the maintenance ladder (no open `new` ORDER at HEAD: status
orders line reads acked=001-031, done=001-019,023-031).

## Close-out

**Evidence:**

- files touched this branch: `.sessions/2026-07-16-rerun-jobs-preflight.md`
  + `control/claims/claude-rerun-jobs-preflight-20260716.md` (first commit
  `d500e7e`; claim deleted at this flip), `app/github.py` (`run_jobs` read
  + `failed_jobs` pure filter), `app/owner.py` (`_jobs_fact` facts row,
  `_preview_jobs` fetch helper, `jobs=` on `_render_rerun_preview`,
  pre-fire job pinning + job-level `_post_fire_chip` with run-level
  fallback in `action_rerun_ci`), `tests/test_owner_preflight.py` (fake
  jobs choke point + 6 new tests: named subset row, degrade-never-blocks,
  zero-failed honesty, jobs-requeued ok chip, not-requeued warn chip,
  after-re-GET-fails run-level fallback), `tests/test_app.py`
  (`test_owner_rerun_ci_action` gains the `run_jobs` mock — the one
  existing test the new read touched), `control/status.md`
  (coordinator-delegated heartbeat, commit `e42e115`).
- git: branch `claude/rerun-jobs-preflight-20260716` based on `main` @
  `16604f9`; implementation commit `d70f445`.
- verify (pre-push, this flip): `python3 -m pytest tests/ botsite/tests
  dashboard/tests review/tests -q` — **1501 passed, 1 warning** (main
  baseline 1495, +6); `python3 bootstrap.py check --strict` — pass, the
  only red being the DESIGNED born-red hold on this card, released by this
  flip.
- session boot facts: main was green before work was chosen (1495 passed +
  strict pass at `16604f9`); pre-existing dirt (`.substrate/state.json`
  session anchor) rescued to `rescue/2026-07-16-substrate-state`
  (`f93ad51`) before syncing.

**Judgment:**

- Decisions made: (1) the jobs row degrades to an honest "unknown — could
  not list jobs (…)" and NEVER blocks the preview or the confirm — the
  jobs listing is decoration on the claim, not a gate on the action;
  (2) the chip matches jobs by NAME across the fire because a rerun mints
  a fresh attempt with NEW job ids — the name is the only stable key the
  before/after comparison has; (3) the confirm spends one extra read
  pinning the failed-job names BEFORE firing (the same
  one-extra-read-for-honesty trade the stale-pin banner already made) so
  the chip verifies exactly what the preview claimed; (4) fail-closed
  re-previews re-fetch jobs for whatever run is newest NOW, so the
  re-preview is as precise as the original.
- Next session should know: the next console/arcade increment on file is
  **stable ask IDs** (`app/askverify.py:461` names the gap: "stable ask
  IDs would make matching exact; deliberately no fuzzy"); owner clicks
  still pending: #345 (remove `do-not-automerge` + hand-merge) and #343
  (approve/hand-merge the bake PR). The seat-digest staleness baton is
  consumed (#347 regenerated it; this session verified a fresh render is
  byte-identical).

## 💡 Session idea

**Verify the rerun by ATTEMPT COUNTER, not status race** — the post-fire
chip (both run-level and the new job-level lane) infers "the rerun
registered" from status flipping to queued/in-progress, which races the
fresh attempt's registration: immediately after the POST, GitHub can still
serve the OLD attempt (the warn lane exists purely for that lag). But the
run object carries `run_attempt` — re-GET the run and compare
`run_attempt` before vs after: an incremented counter is direct,
race-free proof the rerun was accepted, independent of how fast the new
jobs queue. The chip could lead with that fact ("attempt 2 → 3") and keep
the job-status detail as color. Deduped: no `run_attempt` / attempt-based
verification mention anywhere in `docs/ideas/` or `.sessions/`.

## ⟲ Previous-session review

`.sessions/2026-07-15-walls-cards-heartbeat.md` closed clean and its baton
was precise ("run `python3 bootstrap.py seat-digest` in a follow-up
slice") — but that baton was already consumed by #347 before this session
arrived, which is the useful lesson: batons decay fast on an active seat,
so this session re-verified (fresh render byte-identical to the committed
doc) instead of executing the pointer blind. Its walls append also paid
off immediately: the workflow-PR wall entry it recorded is why this
session's heartbeat names #345 as owner-merge-only-by-design instead of
re-diagnosing the parked PR. Workflow improvement it points at: a baton
line could carry a cheap "still true?" probe command alongside the task,
so successors verify-then-act in one step.
