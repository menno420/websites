# discord_auth vendored-copy drift guard

> **Status:** complete

**Order:** Task 1 (coordinator dispatch — ORDER 038 forward-idea).
**Branch:** `claude/discord-auth-drift-guard`

## What
`discord_auth.py` is vendored per-service (app/, botsite/, dashboard/) — the repo's per-service vendoring pattern, no cross-service imports. This adds `tests/test_discord_auth_vendored.py`, a guard that fails when the shared Discord-OAuth **security core** (13 module constants + 14 crypto/session/OAuth functions) drifts across the copies, while cleanly excluding the intentional per-service differences (route paths, redirect targets, template names, service-label error text, the dashboard-only `actor_for`/`require_owner` helpers, and the control-plane-only nav wiring). Mirrors the `listfilter.py` byte-identity guard pattern, adapted for the non-identical copies via docstring-stripped AST comparison.

## Verify
`python3 -m pytest tests/ botsite/tests dashboard/tests review/tests -q` ; `python3 bootstrap.py check --strict`

Housekeeping in the same PR: removes the now-terminal `control/claims/order-021-records.md` (its branch merged in #444).

## What was done

- Added `tests/test_discord_auth_vendored.py`: a docstring-stripped AST drift guard comparing the shared Discord-OAuth security core across the three vendored copies (`app/`, `botsite/`, `dashboard/`). 27 parametrized cases — 14 shared functions + 13 shared constants; intentional per-service pieces excluded by construction (only the SHARED_FUNCTIONS / SHARED_CONSTANTS names are compared).
- Housekeeping: `git rm control/claims/order-021-records.md` (terminal after its branch merged in #444); added the live claim `control/claims/discord-auth-drift-guard.md`.
- Verified: clean tree `pytest tests/test_discord_auth_vendored.py -q` → 27 passed. Bite-test — mutating `verify_session` in `botsite/discord_auth.py` (flipping the HMAC comparison) reddened exactly `test_shared_security_function_does_not_drift[verify_session]` and nothing else; reverted, back to 27 passed. Full four-suite `pytest tests/ botsite/tests dashboard/tests review/tests -q` → 2056 passed (2029 baseline + 27). `python3 bootstrap.py check --strict` → passes once this card flips complete (the born-red hold was the only red).

⚑ Self-initiated: no — Task 1 coordinator dispatch (fm ORDER 048), the ORDER 038 forward-idea.

## 💡 Session idea

**Auto-discovering vendored-copy shared-core guard** — generalize this guard into a meta-test that discovers same-basename modules living in multiple service dirs (the repo's per-service vendoring pattern) and, for each set, asserts a declared shared-symbol core stays AST-identical — so a newly vendored module gets drift coverage from one registry entry instead of a bespoke hand-written test each time. Worth having because the repo keeps closing the same drift class (listfilter byte-identity guards, now discord_auth) one module at a time, and the next vendored module ships uncovered until someone remembers to write its guard. Deduped against `docs/ideas/backlog.md` (the `drift_report()` renderer, fast-lane pin-map, env-drift, registry-drift bullets each cover a different surface — none is a generalized vendored-copy core guard) and the queue-state NEXT list: no overlap. Captured in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

The previous session (ORDER 021 owner-environments hub, #444) landed all four clauses verified with clean born-red discipline — good. Workflow friction observed this session: the boot auto-draft's evidence collector over-reported the diff (101 code / 271 session files "touched" for a genuinely 4-file change) because it diffs a stale cumulative base; a session author must ignore it rather than trust it, so the auto-draft could anchor its counts to the branch's actual merge-base vs origin/main.

- **📊 Model:** Claude Opus 4.8 · medium · test writing
