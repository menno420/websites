# 2026-07-11 — Control-gate suite tests: pin the four fast-lane behaviors (rung 3)

> **Status:** `in-progress` — branch `claude/control-gate-tests`; flips to
> `complete` + the real PR number after the PR exists.

- **📊 Model:** claude-fable-5 · worker · routine-fired build slice (continuous mode, slice 26 — 12:45Z nudge) — family from this session's own harness, per ORDER 010.

**What this session was about:** the 12:45Z nudge; ritual clean (no new
orders, no collision; the 12:05Z fire's relayed branch correctly no longer
reads as stranded), so rung 3 with the designated pick: **pin the #125
control-gate behaviors as suite tests**. The four lane behaviors (clean
heartbeat --status-only exit 0; broken heartbeat exit 1
[status-no-heartbeat]; inbox rewrite vs --inbox-base exit 1
[inbox-not-append]; pure ORDER append exit 0) were validated by hand at
port time — that evidence lives in a PR body, and an engine regression
would only surface on a live control PR (possibly a manager's inbox
append). tests/test_control_gates.py drives the REAL CLI the gate runs,
per the tests/test_born_red_session_gate.py pattern.

## What was done

- (work in progress — filled at close-out)
