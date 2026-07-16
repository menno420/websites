# Claim: console-release-drift-chip

- **Branch:** `claude/console-release-drift-chip`
- **Date:** 2026-07-16
- **Scope:** Owner-console release-drift chip — surface each open ask's
  release-drift verdict (#365's registry-blocker ↔ askverify-probe signal,
  reused) as a glanceable chip on the GATED `/owner/queue`, beside the
  existing askverify preflight chip. The shared verdict logic is extracted
  into `app/release_drift.py` so `scripts/healthcheck.py` and the owner
  console are ONE source of truth. Read-only: no new route, no state
  change, no CSRF surface; the chip is shown only for a drifting ask and
  omitted otherwise.
- **Files touched:**
  - `app/release_drift.py` (new — pure drift `classify` + console `chip`)
  - `scripts/healthcheck.py` (`check_release_drift` renders via the helper)
  - `app/owner.py` (`_render_owner_queue` attaches `it["drift"]`)
  - `app/templates/owner_queue.html` (drift chip markup)
  - `tests/test_release_drift.py` (unit tests for the helper)
  - `tests/test_owner_queue_drift.py` (owner-console render test)
