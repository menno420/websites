# 2026-07-11 — ORDER 010 executed (model-attribution ground truth) + cron-slot helper + review-row check

> **Status:** `complete` — PR #96 (`claude/order-010-and-tooling`),
> squash-merge on `quality` green. (Flipped after the PR existed; the first
> quality run's FAILURE was the born-red gate by design — verbatim log:
> "missing: Session idea … badge still says in-progress".)

- **📊 Model:** claude-fable-5 · worker · routine-fired build slice (continuous mode, slice 14 — 03:31Z nudge) — family reported by this session's own harness ("You are powered by … claude-fable-5" system context), NOT read off the Routines screen, per ORDER 010's ground-truth rule.

**What this session was about:** the 03:31Z send_later continuation.
`scripts/open_work.py` at wake surfaced a NEW branch → open PR #94: the
manager relaying **ORDER 010** (model-attribution ground truth, P3) onto the
bus; the relay session had ended, so this chain merged #94 to unblock the
bus, claimed 010 on main (PR #95, `claimed-by: 010 websites-continuous-wake
2026-07-11T03:36Z`), and executed it here — rung 1. Bundled rung-3 picks
(b) the **cron-slot helper** (this chain shipped five heartbeats with the
same wrong hand-computed cron slot) and (c) the **review-row auto-check**
(the fleet review-queue's binding 50-line rule is enforced by memory; this
repo owes rows for #67/#72/#75/#77 and nobody flagged them mechanically).

## What was done

- **ORDER 010, all three parts**: (1) the session-card template DOES carry
  the `📊 Model:` line — verified in `.sessions/README.md` (gate marker
  needle, the template's own Model line, the ender-checklist family-only
  item; shipped with PR #64); nothing to add. (2) This card records the
  harness-reported family (the Model line above — the system context names
  the model; the Routines screen was NOT consulted). (3) Standing rule kept
  — already doctrine in `docs/project/project-instructions.md` § Model
  names. The done-when ("the next fired session's committed card carries a
  real family-level line and the template includes it") is satisfied BY
  this merged card; `done=010` flips in the closing heartbeat.
- **(b) `scripts/cron_slots.py`** (+ provenance header): 5-field cron →
  next wall-clock UTC slots; numbers, `*`, `*/N`, comma lists, ranges;
  standard dom/dow either-match semantics; malformed input is a loud
  ValueError, never a guess; 366-day walk bound. **Live run**: next
  healthcheck slots 06:17Z, 12:17Z — confirming the verdict timing.
- **(c) `scripts/review_row_check.py`** (+ provenance header): sums
  runtime/product changed lines over a git range with the ledger's exact
  exclusions (docs/, control/, .sessions/, .substrate/, tests, markdown;
  binary numstat `-` counts 0 — unknown, never guessed); prints ROW OWED
  past the binding 50-line threshold; informational, exit 0 always.
  **First live run**: `e1b9026^!` (the #81 squash) → ROW OWED, mechanically
  confirming the heartbeat's standing manager ask.
- **`tests/test_cron_and_review_tools.py`** (+7, suites 217 → 224): the
  pinned incident case (21:03Z merge → 00:17Z first slot, not "+6h", not
  02:17); hourly/list/range forms; strictly-after-now semantics; loud
  malformed parses; the ledger's exclusion matrix; numstat summing incl.
  binary-zero; the threshold constant pinned to the ledger's 50.
- **Backlog:** cron-slot helper → Built; review-row auto-check → Built.
- **Bus work en route**: merged the manager's relay PR #94 (control-only,
  green, relay session ended) and claimed 010 via PR #95 before building —
  claim-first held even for a P3.

## Close-out (auto-drafted 2026-07-11 — edit, don't author)

<!-- substrate:auto-draft -->

**Evidence (auto-collected — verify, then keep or correct):**

- files touched: `scripts/cron_slots.py` (new),
  `scripts/review_row_check.py` (new),
  `tests/test_cron_and_review_tools.py` (new), `docs/ideas/backlog.md`,
  this card — the auto-draft had no session-start anchor; list verified by
  hand against `git diff origin/main --stat`.
- git: branch `claude/order-010-and-tooling`, HEAD 66c893af0 at draft time
  (this flip commit supersedes it).
- verify: `python3 -m pytest tests/ botsite/tests dashboard/tests -q` —
  **224 passed**; `python3 bootstrap.py check --strict` — **all checks
  passed** with this card complete (kit v1.8.0); both scripts executed live
  (outputs above).

**Judgment (the half only the session knows — resolve every slot):**

- Decisions made: ORDER 010 executed as verification-not-build (the
  template already complied — the order's own done-when made this card the
  deliverable); claim-first held for a P3 order; review_row_check stays
  informational (exit 0) because the row-append is a fleet-manager write
  this lane cannot make — a failing gate nobody can satisfy locally would
  be doctrine theater.
- Next session should know: **healthcheck cron verdict at 06:17Z**
  (`cron_slots.py` now computes slots mechanically); `done=010` flips in
  the heartbeat landing right after this PR; remaining backlog picks: nav
  overflow guard, board-row conveyor chips, backlog fact-check pass, and
  the relay-merge protocol line (this slice's 💡).

⚑ Self-initiated: no — ORDER 010 (rung 1, claimed) + coordinator picks
(b)+(c) (rung 3).

## 💡 Session idea

**Relay-PR merge protocol on the bus** — the manager's ORDER 010 relay sat
as an open PR with its session ended; the bus was blocked until this chain
happened to wake and merge it. Worth having: one line in
`control/README.md` ("a `control/inbox.md`-only relay PR from the manager
may be merged by ANY lane session that finds it green — the inbox has one
WRITER, not one MERGER") so relays never depend on a second wake of their
author. Deduped against `docs/ideas/backlog.md` + queue-state NEXT: nothing
covers relay-merge protocol. Captured in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

Slice 13 (same chain, PR #92) shipped a self-verifying deliverable —
wait_deploy proving its own merge was the cleanest verification loop of the
wake; what it missed: nothing material, but its live `/ideas` smoke grepped
word occurrences instead of asserting one exact rendered chip — counts can
pass on coincidence; assert one exact expected string (this slice's tool
runs printed exact expected outputs instead).
