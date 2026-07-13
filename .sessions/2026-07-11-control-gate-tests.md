# 2026-07-11 — Control-gate suite tests: pin the four fast-lane behaviors (rung 3)

> **Status:** `complete` — PR #127, branch `claude/control-gate-tests`.

- **📊 Model:** Claude Fable 5 · worker · routine-fired build slice (continuous mode, slice 26 — 12:45Z nudge) — family from this session's own harness, per ORDER 010.

**What this session was about:** the 12:45Z nudge; ritual clean (no new
orders, no collision; the 12:05Z fire's relayed branch correctly no longer
reads as stranded), so rung 3 with the designated pick: **pin the #125
control-gate behaviors as suite tests**. The lane behaviors were validated
by hand at port time — that evidence lives in a PR body, and an engine
regression would only surface on a live control PR (possibly a manager's
inbox append). tests/test_control_gates.py drives the REAL CLI the gate
runs, per the tests/test_born_red_session_gate.py pattern.

## What was done

- `tests/test_control_gates.py` (new, +5) — subprocess-driven pins of the
  real `check --strict --status-only [--inbox-base]` CLI against a
  minimal synthetic fixture install (config + control files + the REAL
  quality.yml for the enforcement-wiring guard): clean heartbeat exit 0;
  broken heartbeat exit 1 `[status-no-heartbeat]`; inbox rewrite (ORDER
  erased vs base) exit 1 `[inbox-not-append]`; pure ORDER append exit 0;
  **malformed append exit 1 `[inbox-order-grammar]`** — a FIFTH lane
  found while prototyping in the scratchpad, now pinned too. Fixtures
  are synthetic (stable — not coupled to the live status.md that changes
  every wake). All assertions via subprocess returncodes, never `$?`
  after a pipeline (the slice-25 gotcha, honored per the nudge).
- `docs/ideas/backlog.md` — gate-tests bullet moved to Built; fresh 💡
  captured (inbox relay-order provenance check, below).

## Close-out (auto-drafted 2026-07-11 — edit, don't author)

<!-- substrate:auto-draft -->

**Evidence (regenerated from `git diff origin/main --stat`):**

- tests touched (1): `tests/test_control_gates.py` (new, +5)
- docs touched (1): `docs/ideas/backlog.md` (close-out commit)
- sessions touched (1): `.sessions/2026-07-11-control-gate-tests.md`
- git: branch `claude/control-gate-tests`, born-red card first commit
  `928d158`, build commit `a1d1884`, this close-out commit flips the
  gate.
- verify: new module 5/5; `python3 -m pytest tests/ -q` → **187 passed**
  (182 + 5); `python3 bootstrap.py check --strict` before push → only
  the designed born-red HOLD (flips with this commit, PR #127).

**Judgment (the half only the session knows — resolve every slot):**

- Decisions made: no D-entry — regression tests over already-decided
  gate behavior. Fixture-stability decision recorded: synthetic
  heartbeat/inbox fixtures, deliberately NOT the live control files
  (which change every wake and would couple the suite to heartbeat
  content).
- Next session should know: the five gate lanes are pinned — changing
  gate behavior now requires changing these tests in the same PR (same
  protocol as the JSON contract pins). Remaining buildable: route-level
  clock freeze, order-ack latency line, nav-scan glob, inbox provenance
  check (this slice's 💡).

## 💡 Session idea

**Inbox relay-order provenance check (advisory)** — captured in
`docs/ideas/backlog.md`. Worth having because the gates just made the
inbox TRUSTED machine-readable input, and trusted input attracts
spoofing: any green-lane author can append a well-formed ORDER that
reads as manager-issued. An advisory (never red) warning when an
appended ORDER's `provenance:` line names no session/coordinator id
keeps the order-of-record honest without blocking legitimate relays.

## ⟲ Previous-session review

Slice 25 (rescue #124 + gates #125 + heartbeat #126): clean — the
rescue-first ordering was right (main moved under #125 because of it,
one routine 405), and running the closing heartbeat as the gates' first
live fast-lane run made the port's validation loop complete within the
same wake. This slice repaid the prototype habit: driving the fixtures
in the scratchpad BEFORE writing the test file surfaced the fifth lane
(`[inbox-order-grammar]`) that the hand-validation at port time had
missed — prototype against the real CLI, then pin what it actually
does, not what the port PR said it does.
