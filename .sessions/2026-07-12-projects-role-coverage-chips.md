# 2026-07-12 — seat role-coverage chips on the /projects dispatch index

> **Status:** `complete` — branch `claude/order-015-projects-role-chips`;
> PR number recorded on the PR itself (opened READY off this branch).

- **📊 Model:** claude-fable-5 · worker · feature-slice

**What this session was about:** backlog promotion under ORDER 015 (owner
live directive: website-plans sweep — "find all website related plans across
the multiple repos and execute all the important ones"). Promoted the first
backlog bullet, "Seat role-coverage chips on the /projects dispatch index"
(`docs/ideas/backlog.md`, captured from the PR #158 session's 💡): the
dispatch INDEX doesn't say which seats are dispatch-READY — a seat missing
its coordinator prompt or failsafe looks identical to a complete one until
the owner opens it mid-dispatch.

## What was done

- `app/projects.py`: new `role_coverage()` — one chip per dispatch-critical
  role (`_DISPATCH_ROLES` = instructions / coordinator / failsafe),
  `present` derived from the package's already-role-classified file listing
  (zero extra API calls, per the bullet). `_build_package` sets `coverage`
  + `dispatch_ready` (all three present); an unlistable package keeps
  `coverage=[]` / `dispatch_ready=None` — honest unknown, never a
  fabricated ✗.
- `app/templates/projects.html`: chip row per seat card (`.b ok` ✓ /
  `.b bad` ✗, role-label tooltip), a dispatch-ready / NOT-dispatch-ready
  note, and an "N of M dispatch-ready" summary on the index header.
- `/projects.json` packages now carry `coverage` + `dispatch_ready`;
  contract pins updated in the SAME PR (`tests/test_json_contracts.py`:
  `PROJECTS_PACKAGE` + new `PROJECTS_COVERAGE`).
- `tests/test_projects.py`: +5 tests (coverage derivation, overview flag,
  honest-unknown on listing error, incomplete-seat render, ready-seat
  render + JSON). `docs/ideas/backlog.md` bullet flipped
  `captured` → `built`.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — 359 passed; `python3 bootstrap.py check --strict` —
  OK after this card's complete flip (born-red hold observed red before
  it, by design).

⚑ Self-initiated: no — backlog promotion (`docs/ideas/backlog.md` bullet 1)
under ORDER 015 (owner plans-sweep directive, `control/inbox.md` on the
PR #160 branch, `claude/order-012-records-reconcile` @ `05f98c9`).

## 💡 Session idea

**Coverage-chip rollup on the /fleet board** — the same
instructions/coordinator/failsafe coverage now computed per seat could feed
one "packages incomplete: N" cell on `/fleet`'s websites-adjacent registry
row (or the board), so registry lint surfaces where the manager already
looks instead of only on `/projects`. Worth having because the chips double
as registry lint but only fire when the owner opens the dispatch index.
Deduped against `docs/ideas/backlog.md` + the queue-state NEXT list:
nothing rolls coverage up to the monitoring surfaces. Captured in
`docs/ideas/backlog.md`.

## ⟲ Previous-session review

The PR #158 session shipped the dispatch view end-to-end and captured this
exact gap as its 💡 instead of scope-creeping it in — good discipline; it
missed nothing this slice had to repair.
