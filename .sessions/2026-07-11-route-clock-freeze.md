# 2026-07-11 — Route-level clock freeze: the time guard's remaining half (rung 3)

> **Status:** `complete` — PR #130, branch `claude/route-clock-freeze`.

- **📊 Model:** claude-fable-5 · worker · routine-fired build slice (continuous mode, slice 27 — 13:19Z nudge) — family from this session's own harness, per ORDER 010.

**What this session was about:** the 13:19Z nudge; ritual clean (sibling
#129 landed kit v1.11.0 mid-window — engine + pin only, no collision; no
new orders), so rung 3 with the designated pick: **route-level clock
freeze**. The #114 time-discipline guard covers DIRECT calls to
age-measuring functions, but TestClient route tests (/fleet, /orders, the
board) still exercised the REAL wall clock through the endpoints — the
08:45Z failure class survived there, beyond the static guard's sight.

## What was done

- `app/clock.py` (new) — `NOW_OVERRIDE` (None in production) + `now()`:
  the app's SINGLE wall-clock read; zero prod change.
- `app/fleet.py` (4 fallback sites), `app/orders.py` (3),
  `app/activity.py` (Atom feed fallback timestamp) — every wall-clock
  fallback routes through `clock.now()`; the injectable `now=` params
  from #111/#114 unchanged.
- `tests/test_clock_freeze.py` (new, +4) — override unit pins; a WHOLE
  /fleet.json request rendered at a frozen instant (fixture lane exactly
  1.0h old, deterministically, in any decade); /orders.json under the
  same freeze; and a source guard: `app/*.py` never calls
  `datetime.now()/utcnow()` outside clock.py, so a new module cannot
  silently reopen the blind spot (companion to the #114 test-side guard).
- JSON contracts untouched (no payload change, no pin moved — per the
  nudge).
- `docs/ideas/backlog.md` — clock-freeze bullet moved to Built; fresh 💡
  captured (cross-service clock pattern, premise-verified, below).

## Close-out (auto-drafted 2026-07-11 — edit, don't author)

<!-- substrate:auto-draft -->

**Evidence (regenerated from `git diff origin/main --stat`):**

- code touched (4): `app/clock.py` (new), `app/fleet.py`,
  `app/orders.py`, `app/activity.py`
- tests touched (1): `tests/test_clock_freeze.py` (new, +4)
- docs touched (1): `docs/ideas/backlog.md` (close-out commit)
- sessions touched (1): `.sessions/2026-07-11-route-clock-freeze.md`
- git: branch `claude/route-clock-freeze`, born-red card first commit
  `b73c949`, build commit `c4439f2`, this close-out commit flips the
  gate.
- verify: new module 4/4; `python3 -m pytest tests/ -q` → **191 passed**
  (187 + 4; suite green both BEFORE and AFTER the rewiring — behavior
  preserved); `python3 bootstrap.py check --strict` before push → only
  the designed born-red HOLD (flips with this commit, PR #130).

**Judgment (the half only the session knows — resolve every slot):**

- Decisions made: no D-entry — test-infrastructure completion of the
  #111/#114 time-discipline line inside the existing layers; the one
  design decision (module-level override via monkeypatch rather than a
  FastAPI dependency) recorded here: the age-measuring functions are
  called from the domain layer, not route signatures, so a dependency
  override could not reach them — the module hook can.
- Next session should know: `clock.now()` is the ONLY legal wall-clock
  read in app/ (a test enforces it); freeze whole requests with
  `monkeypatch.setattr(clock, "NOW_OVERRIDE", NOW)`. Remaining buildable:
  order-ack latency line, nav-scan glob, inbox provenance advisory,
  cross-service clock pattern (dormant until botsite/dashboard grow
  age-measuring code).

## 💡 Session idea

**Port the clock-freeze pattern to botsite/dashboard when they grow
age-measuring code** — captured in `docs/ideas/backlog.md`,
premise-checked first (grep: ZERO `datetime.now` in botsite/app.py and
dashboard/app.py today, so nothing to port yet — the bullet exists so
the first age-measuring feature in either service starts from
app/clock.py's pattern instead of re-learning the 08:45Z lesson). Worth
having because the failure class is service-agnostic and the fix is one
small module.

## ⟲ Previous-session review

Slice 26 (#127 gate pins + heartbeat #128): clean — the five pinned
lanes are exactly what the CLI does (prototype-then-pin held up), and
the fixture-stability decision (synthetic control files, not live ones)
already proved right: this slice's heartbeat changes would have broken
live-coupled fixtures. Sibling watch: #129 (kit v1.11.0) landed cleanly
mid-window — third kit wave today, all three absorbed without a
collision; the stamp-vs-kit-line distinction in the collision rule keeps
doing the work. Workflow improvement kept: status-only pre-validation
before pushing the heartbeat (now that the fast lane gates it) — zero
surprises since adopted.
