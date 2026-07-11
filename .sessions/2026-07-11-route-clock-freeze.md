# 2026-07-11 — Route-level clock freeze: the time guard's remaining half (rung 3)

> **Status:** `in-progress` — branch `claude/route-clock-freeze`; flips to
> `complete` + the real PR number after the PR exists.

- **📊 Model:** claude-fable-5 · worker · routine-fired build slice (continuous mode, slice 27 — 13:19Z nudge) — family from this session's own harness, per ORDER 010.

**What this session was about:** the 13:19Z nudge; ritual clean (sibling
#129 landed kit v1.11.0 mid-window — engine + pin only, no collision; no
new orders), so rung 3 with the designated pick: **route-level clock
freeze**. The #114 time-discipline guard covers DIRECT calls to
age-measuring functions, but TestClient route tests (/fleet, /orders, the
board) still exercised the REAL wall clock through the endpoints — the
08:45Z failure class survived there, beyond the static guard's sight. A
test-only now-provider (app/clock.py, default = wall clock, zero prod
change) closes that half; route code's wall-clock fallbacks route through
it, and the suite can pin one frozen instant for whole-request rendering.

## What was done

- (work in progress — filled at close-out)
