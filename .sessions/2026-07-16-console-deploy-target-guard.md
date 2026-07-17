# Session — console deploy-target single-source guard (C10)

> **Status:** `complete`

Build of planning-menu item **C10** (PR #375 menu,
`docs/planning/2026-07-16-console-review-menu.md`): a guard test tying the
Railway `/version` deploy-probe URLs to a single source so a re-provisioned
service can't silently drift. Test-only, `app/` console scope, no behavior
change. Part of the X2 tests-and-guards bundle.

- **📊 Model:** Claude Opus · high · test writing (console-hardening guard)

## What this session is about
The readiness deploy-drift board probes each websites service's public
`/version` endpoint. Those probe URLs live in one place —
`app/config.py::SERVICE_DEPLOY_TARGETS` (both `app/readiness.py::_deploy_board`
and `app/askverify.py` source from it). Separately, `app/railway.py::SERVICES`
hardcodes the SAME Railway hosts (base URL, no `/version`) for the gated
`/owner/environments` page. Two independent hardcoded host lists is the drift
risk: re-provision a service, update one list but not the other, and the board
probes a stale host while environments shows the new one — silently, untested.
`test_check_no_ambient_railway_ids` guarded Railway *IDs*; nothing tied these
`/version` URLs to a single consistent source. New
`tests/test_deploy_target_single_source.py` (6 tests) asserts the
`*.up.railway.app/version` literal appears in `app/` only in config.py, each
non-None target is a `/version` URL, `control-plane` is `None` (self, no hop),
the two lists cover the same service names, and each probe host matches the
same-named `railway.SERVICES` base host — the drift catch. Read-only,
source-level; no app-behavior change, no new route, no CSRF surface.

## Verify
- `python3 -m pytest tests/ botsite/tests dashboard/tests review/tests -q` → `1637 passed`
- `python3 bootstrap.py check --strict --session-log .sessions/2026-07-16-console-deploy-target-guard.md` → all checks passed

💡 Idea: promote C10's approach into a general "single-source host ledger"
guard — one committed table of every service host, with both
`SERVICE_DEPLOY_TARGETS` and `railway.SERVICES` derived from it, so the two
lists can't exist independently at all (removes the drift class rather than
just testing for it).

Previous-session review: `.sessions/2026-07-16-review-ledger-tally.md`
(review Problems/Successes at-a-glance tally) is a clean, well-scoped sibling
of tonight's idiom — its pure `story.ledger_summary` helper with the count
pinned to rendered cards is exactly the "guard the invariant, don't just
compute it" discipline this C10 test extends to the deploy board.
