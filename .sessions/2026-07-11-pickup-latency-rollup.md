# 2026-07-11 — Fleet-wide pickup-latency rollup on /orders (rung 3)

> **Status:** `complete` — PR #135, branch `claude/pickup-latency-rollup`.

- **📊 Model:** claude-fable-5 · worker · routine-fired build slice (continuous mode, slice 29 — 14:32Z nudge) — family from this session's own harness, per ORDER 010.

**What this session was about:** the 14:32Z nudge; ritual clean (no new
orders, no collision; sibling PR #132 re-checked per the decision tree:
still OPEN, quality green, unchanged 52 min — under the 2h stale
threshold, hands off), so rung 3 with the designated pick: **fleet-wide
pickup-latency rollup** — slice 28 made per-order filed→claimed latency
visible; per-order latency is trivia until it trends.

## What was done

- `app/orders.py` — `_pickup_rollup(cards)`: median/max over every
  measurable `pickup_latency_mins` across the fleet;
  `summary.pickup = {count, median_mins/_human, max_mins/_human}` or
  None — NEVER a fabricated zero — when nothing is measurable (claims
  drop on completion; quiet fleets legitimately have nothing to
  aggregate). Each repo card gains `pickup_median_mins/_human`.
- `app/templates/orders.html` — summary chip
  "pickup: median X · slowest Y" (tooltip carries the measurable-claim
  count) + per-repo "pickup ~X" chip.
- `tests/test_json_contracts.py` — ORDERS_SUMMARY (+pickup) and
  ORDERS_CARD (+2 keys) pins moved SAME-PR per protocol.
- `tests/test_orders.py` (+2) — exact median/max over a mixed fixture
  (30.0/50.0, count 3); honest-None on unmeasurable worlds; summary +
  card key coverage under frozen now=NOW. Pure aggregation — no
  wall-clock read; the #114/#130 guards untouched.
- `docs/ideas/backlog.md` — rollup bullet moved to Built; fresh 💡
  captured (persist latencies before claims clear, below).

## Close-out (auto-drafted 2026-07-11 — edit, don't author)

<!-- substrate:auto-draft -->

**Evidence (regenerated from `git diff origin/main --stat`):**

- code touched (1): `app/orders.py`
- templates touched (1): `app/templates/orders.html`
- tests touched (2): `tests/test_orders.py` (+2),
  `tests/test_json_contracts.py` (2 pins moved)
- docs touched (1): `docs/ideas/backlog.md` (close-out commit)
- sessions touched (1): `.sessions/2026-07-11-pickup-latency-rollup.md`
- git: branch `claude/pickup-latency-rollup`, born-red card first commit
  `6c35101`, build commit `680e416`, this close-out commit flips the
  gate.
- verify: `python3 -m pytest tests/ -q` → **195 passed** (193 + 2);
  orders/contracts/polish modules green together (24 passed);
  `bootstrap.py check --strict` before push → only the designed
  born-red HOLD (flips with this commit, PR #135).

**Judgment (the half only the session knows — resolve every slot):**

- Decisions made: no D-entry — presentation-layer aggregation over
  already-computed numbers with the pin-move protocol followed. Honesty
  decision recorded: summary.pickup is None (chip absent), never 0, when
  no order carries a measurable latency.
- Next session should know: the rollup's blind spot is structural —
  latency data vanishes when a claim clears (done orders drop the
  annotation), so the fleet chip will often read from few claims; the
  captured persistence idea (manager-side convention) is the real fix.
  Remaining buildable: nav-scan glob, inbox provenance advisory,
  persistence ask, cross-service clock (dormant).

## 💡 Session idea

**Persist pickup latencies before claims clear** — captured in
`docs/ideas/backlog.md`. Worth having because the SLO's history vanishes
exactly when an order completes (the moment it becomes most meaningful —
live-verified on ORDER 011 post-#133); the honest fix is a one-line
manager-side convention (executor's done= move appends `pickup: 011 19m`
to the heartbeat notes) that /orders can parse into durable per-lane
history — protocol layer, not scraping.

## ⟲ Previous-session review

Slice 28 (#133 pickup latency + heartbeat #134): clean — the honest-None
design decision paid off immediately (the live 011 check read as
correct-by-design instead of a bug hunt), and this slice's rollup
inherited the same rule cheaply. The sibling-watch decision tree in the
nudge worked as written: one MCP get + one check-runs call settled
"hands off" in under a minute, no stranded-work guesswork. Nothing to
correct from slice 28.
