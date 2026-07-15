# 2026-07-15 — Owner console: rerun-ci preflight — preview, pinned confirm, verification chip

> **Status:** `in-progress`

- **📊 Model:** Claude Fable · medium · feature build (rerun-ci preflight preview + pinned confirm on the owner console)

**What this session is about:** the "preflighted" half of the owner launch
console, PR A of 2. Today `POST /owner/actions/rerun-ci` resolves "the
newest failed run on main" AT FIRE TIME — the owner fires blind at
whatever happens to be newest-failed at that instant. This slice makes the
target visible and the fire pinned:

- `app/github.py` splits `rerun_latest_failed` into a read half
  (`latest_failed_run` — resolves the newest failed run, refresh=True) and
  a fire half (`rerun_run` — POSTs rerun-failed-jobs at a PINNED run id),
  recomposed so the existing composition keeps working;
- new gated GET `/owner/actions/rerun-ci/preview?repo=X` (plain
  `require_owner`, read-only like every other /owner GET) renders a new
  generic `owner_preflight.html`: facts table (run id, workflow, branch,
  head sha, created + age, run link) and a confirm form carrying the
  hidden pinned `run_id`; no failed run → an honest "nothing to re-run"
  page;
- `POST /owner/actions/rerun-ci` now REQUIRES the pinned `run_id`,
  re-resolves with refresh=True and FAILS CLOSED when anything moved
  (missing pin, vanished run, no-longer-failed, newer failed appeared) —
  honest banner naming exactly what moved, zero fires; a match fires at
  the pinned id and a post-action chip re-GETs the run to show it really
  started (honest-unknown when the re-GET fails);
- `POST /owner/actions/refresh` gets the cheap uniform preview on the same
  template ("N cache entries will drop"); the POST contract itself is
  untouched (the ORDER 013 security tests keep passing unchanged);
- the /owner board's rerun-ci form routes through the preview instead of
  the blind fire. The `require_owner_action` floor (auth → strict
  Origin/Referer → per-route rate limit) stays exactly as-is — no new
  CSRF token this slice.

⚑ Self-initiated: no — dispatched under the owner's live work grant
(accept-edits session mode), coordinator-approved mission slice
(scouting cites @ 1e73d8a, re-verified at HEAD).

## Close-out

**Evidence:**

- [[fill: files touched + verify lines at the flip]]

**Judgment:**

- [[fill: decisions + baton at the flip]]

## 💡 Session idea

[[fill: genuine deduped idea at the flip]]

## ⟲ Previous-session review

[[fill: review of .sessions/2026-07-15-arcade-detail.md at the flip]]
