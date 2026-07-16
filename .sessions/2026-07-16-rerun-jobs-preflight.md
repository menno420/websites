# 2026-07-16 — Owner console: rerun-ci preflight names the JOBS, chip verifies them

> **Status:** `in-progress`

- **📊 Model:** fable · high · maintenance (launch-console increment: jobs-level rerun-ci preflight)

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
rung (b) of the maintenance ladder (no open `new` ORDER at HEAD).

## Close-out

**Evidence:**

- [[fill: files touched + verify results at flip time]]

**Judgment:**

- Decisions made: [[fill: decisions]]
- Next session should know: [[fill: baton]]

## 💡 Session idea

[[fill: one genuine idea, deduped]]

## ⟲ Previous-session review

[[fill: remark on the previous session's card]]
