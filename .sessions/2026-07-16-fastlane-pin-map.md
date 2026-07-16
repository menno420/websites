# 2026-07-16 — fast-lane grammar-pin map drift pin (ORDER 032 overnight slice)

> **Status:** `complete` — branch `claude/fastlane-pin-map-20260716`; one
> contained, reversible test-only slice: pins `quality.yml`'s fast-lane
> pin-selection mapping against a drift check.

- **📊 Model:** Claude Sonnet 5 · medium · test writing

**What this session was about:** ORDER 032 (owner's live overnight
autonomy order, 2026-07-16T21:57:55Z) — work the backlog slice by slice,
one PR each, never stall on a blocker. `docs/ideas/backlog.md` already had
a captured, un-built idea from 2026-07-13 (fastlane-outbox-gate session):
`.github/workflows/quality.yml`'s fast-lane grammar-pin mapping (which
control file triggers which pytest pin: `control/outbox.md` →
`test_outbox_grammar_pin.py`, `control/status.md` → `test_own_heartbeat.py`,
`control/claims/` → `test_claims_drift_gate.py`) is shell text nothing ever
executes — rename a pin test or add a fourth machine-read control file
without updating the workflow and the gate goes hollow while staying
green. Picked because it's small, needs no GitHub API, and closes a real
decay class the outbox pin (PR #314 lineage) already proved happens.

## What was done

- `tests/test_fastlane_pin_map.py` (new) — parses the "control fast lane"
  step straight out of `.github/workflows/quality.yml` (never hand-copies
  the mapping) via a regex over the `grep '<trigger>'; then / pin_tests=`
  shell pairs, then asserts (1) the parsed trigger→test map equals the set
  of control files this repo's own code actually machine-reads
  (`app.briefing.OUTBOX_PATH`, `control/status.md`, `control/claims/`) and
  (2) every referenced pin test file exists on disk. Verified the test is
  not vacuous: it correctly failed (missing the claims trigger) before a
  regex fix (the `-q '^control/claims/'` grep uses a `^`-anchored prefix
  match, not `-Fxq` exact match like the other two — the fix strips the
  optional `^` so all three triggers compare as plain paths), then passed
  once the parsing matched reality.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — **1634 passed** (1631 baseline this session already
  established + 3 new); `python3 bootstrap.py check --strict` — all
  checks passed.

⚑ Self-initiated: yes — ORDER 032 says work the backlog slice by slice
when the coordinator/inbox has no discrete next order; this is the
highest-value ready-to-build item in `docs/ideas/backlog.md` that needs no
live GitHub API (this session has none — ASK-0017) and touches no
`.github/workflows/**` file itself (a new `tests/*.py` only reads the
workflow text, so it doesn't trip the do-not-automerge workflow-diff
label).

## Landing

Same named blocker as every branch this lane has pushed tonight: **ASK-0017**
(org-level GitHub App not connected) — this session has no PR-creation
tooling and a direct push to `main` is rejected by branch protection
(GH013). Pushed `claude/fastlane-pin-map-20260716` for an interactive
session or the owner to open/merge. Per ORDER 032 ("a blocked PR carries
its named blocker; take the next slice, never stall") this is expected,
not a stall — moving to the heartbeat write next.

## 💡 Session idea

No new idea this session — the slice built was itself a previously-captured
idea from the backlog, not a source of a new one. Honest "nothing new"
rather than forced filler.

## ⟲ Previous-session review

The cycle-3/4/5 heartbeat-only cycles made the right call at the time
(holding back on new feature branches while 5+ were already stuck
unlanded) — but ORDER 032 landed mid-loop and explicitly supersedes that
caution: "a blocked PR carries its named blocker; take the next slice,
never stall." What those cycles missed, in hindsight: they couldn't have
known ORDER 032 was coming, but the general lesson is to keep checking
inbox.md every cycle even when nothing else changes — which they did do,
correctly, and it's exactly how this session caught ORDER 032 within one
cycle of it landing.
