# 2026-07-11 — Order pickup latency on /orders (rung 3, backlog promotion)

> **Status:** `complete` — PR #133, branch `claude/order-pickup-latency`.

- **📊 Model:** Claude Fable 5 · worker · routine-fired build slice (continuous mode, slice 28 — 13:56Z nudge) — family from this session's own harness, per ORDER 010.

**What this session was about:** the 13:56Z nudge; ritual found a NEW
sibling branch (claude/anthropic-review-site) — checked before picking:
its PR #132 is OPEN and active (owner-directed review site, opened
13:37Z), NOT stranded — hands off, no rescue, no double-build. No new
orders, so rung 3 with the designated pick: **order pickup latency** —
the fleet's routing SLO (filed→claimed) was invisible; /orders already
parsed both halves and never subtracted them.

## What was done

- `app/orders.py` — `classify_order` exposes `claimed_at`;
  `pickup_latency(issued, claimed_at)` computes exact minutes with honest
  None on unparseable/absent stamps or a negative delta (hand-written
  clock skew) — latency is never guessed; every order dict carries
  `pickup_latency_mins` + `pickup_latency_human`.
- `app/templates/orders.html` — claimed orders render a
  "picked up in X" chip (tooltip names the metric); /orders.json carries
  the keys via the existing body_html-drop serializer.
- `tests/test_json_contracts.py` — ORDERS_ORDER pin moved SAME-PR per
  protocol (+2 keys).
- `tests/test_orders.py` (+2) — exact 19.0-min pin (ORDER 011's real
  pickup ride: filed 09:59Z → claimed 10:18Z), four honest-None cases,
  overview carries the keys with open orders honestly None; runs under
  frozen now=NOW (the #114/#130 guards pass untouched — the new math is
  pure timestamp subtraction, no wall-clock read).
- `.gitignore` — HANDOFF.md added (nudge rider): kit v1.11.0 regenerates
  it untracked by design; `git check-ignore` exited 1, so an accidental
  `git add .` would have committed kit machinery.
- `docs/ideas/backlog.md` — latency bullet moved to Built; fresh 💡
  captured (fleet-wide latency rollup, below).

## Close-out (auto-drafted 2026-07-11 — edit, don't author)

<!-- substrate:auto-draft -->

**Evidence (regenerated from `git diff origin/main --stat`):**

- code touched (1): `app/orders.py`
- templates touched (1): `app/templates/orders.html`
- tests touched (2): `tests/test_orders.py` (+2),
  `tests/test_json_contracts.py` (pin move)
- hygiene touched (1): `.gitignore` (HANDOFF.md)
- docs touched (1): `docs/ideas/backlog.md` (close-out commit)
- sessions touched (1): `.sessions/2026-07-11-order-pickup-latency.md`
- git: branch `claude/order-pickup-latency`, born-red card first commit
  `780d9c4`, build commit `51f760c`, this close-out commit flips the
  gate.
- verify: `python3 -m pytest tests/ -q` → **193 passed** (191 + 2);
  contract suite green with the moved pin; `bootstrap.py check --strict`
  before push → only the designed born-red HOLD (flips with this commit,
  PR #133).

**Judgment (the half only the session knows — resolve every slot):**

- Decisions made: no D-entry — a derived field over data /orders already
  parses, inside the existing layers; the one contract change (2 order
  keys) moved its pin in the same PR per the established protocol.
  Honesty decision recorded: negative deltas (claim stamp before filing)
  read as unknown, not zero — both stamps are hand-written.
- Next session should know: pickup latency is live per-order; the
  natural successor is the summary rollup (this slice's 💡). Remaining
  buildable: nav-scan glob, inbox provenance advisory, latency rollup,
  cross-service clock (dormant). Sibling PR #132 (review site) was OPEN
  at this slice's ritual — later wakes should re-check it rather than
  assume it merged.

## 💡 Session idea

**Fleet-wide pickup-latency rollup on /orders** — captured in
`docs/ideas/backlog.md`. Worth having because per-order latency is
trivia until it trends: a median/max summary chip plus a per-repo figure
turns the routing SLO into a manageable number the manager sweep can
watch, and a single slow-pickup lane is exactly what it should catch
early (medians resist the one-weird-timestamp outlier).

## ⟲ Previous-session review

Slice 27 (#130 clock freeze + heartbeat #131): clean — this slice built
ON it: the latency tests run under frozen now and the new code needed
zero wall-clock reads, exactly the rail the clock module laid. The
stranded-work protocol also did its job in reverse this wake: the new
sibling branch turned out to be an OPEN PR (#132), and checking its real
PR state via MCP before touching it prevented a wrongful relay of
another session's active work — the protocol's "check, don't assume
stranded" clause is as load-bearing as the rescue clause.
