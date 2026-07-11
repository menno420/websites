# 2026-07-11 — Time-discipline guard for tests (rung 3, backlog promotion)

> **Status:** `complete` — PR #114, branch `claude/test-time-discipline-guard`.

- **📊 Model:** claude-fable-5 · worker · routine-fired build slice (continuous mode, slice 21 — 09:38Z nudge) — family from this session's own harness, per ORDER 010.

**What this session was about:** the 09:38Z nudge; ritual clean (no new
orders; sibling #113 kit v1.10.1 landed mid-window, bumped the kit line and
added a third buildable bullet), so rung 3 with the coordinator-designated
pick: **time-discipline guard** — the slice-20 idea, promoted one slice
after capture because its failure class (a test that measures fixed
fixture timestamps against the real wall clock) detonated live at
2026-07-11T08:45Z and would detonate again silently in unattended
routine-fired sessions.

## What was done

- `tests/test_time_discipline.py` (new, +2 tests) — AST-scans every test
  module in `tests/` and fails on any call to an age-measuring entry point
  (`fleet.overview`/`lane_status`/`freshness`/`heartbeat_freshness`,
  `orders.overview`/`classify_order`) that omits a `now=` kwarg; docstring
  records the 08:45Z incident; a meta-test proves the scanner still
  catches an offending snippet (a refactor can't silently blunt it).
- **First run caught 17 latent bombs across 5 files** — `test_app.py` ×6,
  `test_orders.py` ×7, `test_fleet_chip_tooling.py` ×3,
  `test_own_heartbeat.py` ×1 — all threaded with frozen `NOW` constants.
  Behavior-preserving: every touched assertion is state/shape-based
  (verified: suite passes unchanged).
- `app/fleet.py` `heartbeat_freshness()` + `app/orders.py` `overview()`
  gain the module-standard injectable `now=` (additive, defaults to wall
  clock, zero caller change) so the rule can be absolute.
- `docs/ideas/backlog.md` — time-discipline bullet moved to Built; fresh
  💡 captured (route-level clock freeze, below).

## Close-out (auto-drafted 2026-07-11 — edit, don't author)

<!-- substrate:auto-draft -->

**Evidence (corrected — the auto-collected list was tree-wide/polluted by
sibling merges; regenerated from `git diff origin/main --stat`):**

- code touched (2): `app/fleet.py`, `app/orders.py` (injectable `now=`)
- tests touched (5): `tests/test_time_discipline.py` (new),
  `tests/test_app.py`, `tests/test_orders.py`,
  `tests/test_fleet_chip_tooling.py`, `tests/test_own_heartbeat.py`
- docs touched (1): `docs/ideas/backlog.md` (close-out commit)
- sessions touched (1): `.sessions/2026-07-11-test-time-discipline-guard.md`
- git: branch `claude/test-time-discipline-guard`, born-red card first
  commit `473900b`, build commit `dd4e08d`, this close-out commit flips
  the gate.
- verify: `python3 -m pytest tests/ -q` → **179 passed** (177 + 2 guard);
  full three-service suite → **237 passed**;
  `python3 bootstrap.py check --strict` → green (born-red HOLD on the
  first run was the designed gate; this flip commit carries PR #114).

**Judgment (the half only the session knows — resolve every slot):**

- Decisions made: no D-entry — a test-infrastructure guard plus additive,
  default-preserving signature extensions following the `now=` convention
  #111 already established; no contract or payload change. Guard scope
  decision recorded here: DIRECT calls only (static AST), route-level
  wall-clock exposure deliberately left to the captured follow-up idea.
- Next session should know: buildable backlog after this slice = nav
  manifest + quality.yml every-card gate port (sibling #113's bullet) +
  the new route-freeze idea. When adding a new age-measuring function,
  add it to `GUARDED` in `tests/test_time_discipline.py` in the same PR.

## 💡 Session idea

**Route-level clock freeze for TestClient tests** — captured in
`docs/ideas/backlog.md`. Worth having because the static guard only sees
direct calls: route tests exercising /fleet, /orders, and the board still
hit the real wall clock through the endpoints, where the 08:45Z class can
reappear beyond the AST scanner's sight; a test-only clock override pinned
by the suite would close that remaining half.

## ⟲ Previous-session review

Slice 20 (#111 + heartbeat #112): clean — the truth sweep's corrections
all verify against main HEAD, and the time-bomb root-cause (stash-verified
on an untouched tree) is what made this slice's guard a designated pick
instead of a hunch. Workflow improvement adopted here: when a defuse fixes
one instance of a failure CLASS, capture the class-wide guard as the very
next slice's bullet while the incident evidence is fresh — the 17 latent
sites this guard caught would have been found one mystery-red at a time
otherwise. Sibling watch: #113 (kit v1.10.1) landed cleanly mid-window;
its backlog bullet (quality.yml every-card gate port) is real and
buildable.
