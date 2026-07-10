# 2026-07-10 — /fleet.json shape-contract test (backlog promotion)

> **Status:** `complete` — PR #83 (`claude/fleet-json-contract`),
> squash-merge on `quality` green. (Flipped after the PR existed.)

- **📊 Model:** claude-fable-5 · worker · routine-fired build slice (continuous mode, slice 9 — 23:48Z nudge)

**What this session was about:** the 23:48Z send_later continuation.
Collision check first (per the posted 00:00Z rule): heartbeat at HEAD still
carried this session's own 23:32Z stamp — the 4-hourly fresh session had not
fired yet, no collision. Inbox at HEAD has no order past 009. Work-ladder
rung 3 — this chain's designated pick: the **`/fleet.json` shape-contract
test** (captured last slice): the payload was extended three times today
(enrichment, /orders reuse, polish batch) and the manager + `/queue` +
`/orders` all machine-consume it — a key rename today breaks consumers
silently; a pinned-shape test makes it a named red (the console.json
pinned-contract lesson applied to our own JSON).

## What was done

- **`tests/test_fleet_json_contract.py`** (+3 tests, suites 194 → 197):
  pinned key sets for the whole payload — TOP_KEYS / SUMMARY_KEYS (incl.
  `kit_versions` item shape) / LANE_KEYS (with `body_html` confirmed
  stripped) / ORDERS_INFO_KEYS / ROUTINE_INFO_KEYS / LANDING_INFO_KEYS /
  HEALTH_KEYS / FRESHNESS_KEYS. Drift asserts print the symmetric
  difference, so a red NAMES the drifted keys. Third test pins the
  **degraded-lane same-shape guarantee**: missing/errored lanes carry the
  identical key set with honest defaults — consumers never need per-state
  key handling.
- **Contract-change protocol** (docstring): update the pinned sets in the
  SAME PR that changes the payload, and say so in the PR body — the test is
  the conscious-change gate, not a freeze.
- **Backlog:** shape-contract bullet `captured` → Built. Test-only change —
  deliberately no decision-ledger entry (no product-surface decision).

## Close-out (auto-drafted 2026-07-10 — edit, don't author)

<!-- substrate:auto-draft -->

**Evidence (auto-collected — verify, then keep or correct):**

- files touched: `tests/test_fleet_json_contract.py` (new),
  `docs/ideas/backlog.md`, this card (auto-draft had no session-start
  anchor — verified by hand against `git diff origin/main --stat`).
- git: branch `claude/fleet-json-contract`, HEAD ad12d786e at draft time
  (this flip commit supersedes it).
- verify: `python3 -m pytest tests/ botsite/tests dashboard/tests -q` —
  **197 passed**; `python3 bootstrap.py check --strict` — **all checks
  passed** with this card complete (kit v1.7.1).

**Judgment (the half only the session knows — resolve every slot):**

- Decisions made: none ledger-worthy (test-only pin; the change protocol
  lives in the test docstring).
- Next session should know: remaining backlog picks for this chain —
  `?repo=` filter on the activity views (next designated), open-PR-awareness
  script, review-row auto-check, wait-deploy.py, ladder-rung telemetry; the
  PR #9 rework-dashboard salvage re-check stays RESERVED for the 00:00Z
  fresh session (per the collision rule posted in the slice-8 heartbeat).
  Manager still owes review-queue rows for #67/#72/#75/#77 (+#81
  borderline).

⚑ Self-initiated: no — backlog promotion (rung 3), this chain's designated
pick from the slice-8 heartbeat NEXT-WORK POINTER.

## 💡 Session idea

**Same-shape contract tests for the other machine endpoints** —
`/orders.json`, `/queue.json`, `/projects.json`, `/reviews.json` each now
have machine consumers (the manager's round-trip explicitly so) but only
`/fleet.json` has a pinned shape. Worth having because the marginal cost is
near-zero (the pattern file now exists to copy) while each endpoint has the
same silent-rename risk the fleet pin just closed — one small test file per
endpoint, or one parametrized file for all four. Deduped against
`docs/ideas/backlog.md` + queue-state NEXT: the fleet pin (Built) covers
only /fleet.json; nothing covers the other four. Captured in
`docs/ideas/backlog.md`.

## ⟲ Previous-session review

Slice 8 (same wake, PR #81) bundled three captures cleanly and live-smoked
against the real fleet before merge — the "zero new fetches" framing kept
the batch reviewable; what it missed: its /queue.json test was written
against an assumed item shape (`fields.WHAT`) instead of reading
`_make_item` first, costing two failed runs before checking the real
contract — read the producing function before writing the consuming
assertion (cheaper than debugging backwards from an empty string).
