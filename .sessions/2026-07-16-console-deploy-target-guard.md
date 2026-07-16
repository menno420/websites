# Session — console deploy-target single-source guard (C10)

> **Status:** `in-progress`

## Goal
Build planning-menu item **C10** (PR #375 menu, `docs/planning/2026-07-16-console-review-menu.md`):
a test tying the Railway `/version` deploy-probe URLs to a single source so a
re-provisioned service can't silently drift. Test-only, `app/` console scope,
no behavior change. Part of the X2 tests-and-guards bundle.

## Plan
- New `tests/test_deploy_target_single_source.py`:
  - the `*.up.railway.app/version` probe literal appears in `app/` code ONLY in
    `app/config.py` (single source for the probe URL);
  - each non-None `config.SERVICE_DEPLOY_TARGETS` entry is a `/version` URL and
    its host matches the same-named `app/railway.py::SERVICES` base `url`
    (the two hardcoded host lists can't drift apart on re-provision);
  - the two lists cover the same service names; `control-plane` is `None`
    (self, no network hop).

## Verify
- `python3 -m pytest tests/ botsite/tests dashboard/tests review/tests -q`
- `python3 bootstrap.py check --strict --session-log .sessions/2026-07-16-console-deploy-target-guard.md`
