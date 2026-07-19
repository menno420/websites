# discord_auth vendored-copy drift guard

> **Status:** in-progress

**Order:** Task 1 (coordinator dispatch — ORDER 038 forward-idea).
**Branch:** `claude/discord-auth-drift-guard`

## What
`discord_auth.py` is vendored per-service (app/, botsite/, dashboard/) — the repo's per-service vendoring pattern, no cross-service imports. This adds `tests/test_discord_auth_vendored.py`, a guard that fails when the shared Discord-OAuth **security core** (13 module constants + 14 crypto/session/OAuth functions) drifts across the copies, while cleanly excluding the intentional per-service differences (route paths, redirect targets, template names, service-label error text, the dashboard-only `actor_for`/`require_owner` helpers, and the control-plane-only nav wiring). Mirrors the `listfilter.py` byte-identity guard pattern, adapted for the non-identical copies via docstring-stripped AST comparison.

## Verify
`python3 -m pytest tests/ botsite/tests dashboard/tests review/tests -q` ; `python3 bootstrap.py check --strict`

Housekeeping in the same PR: removes the now-terminal `control/claims/order-021-records.md` (its branch merged in #444).
