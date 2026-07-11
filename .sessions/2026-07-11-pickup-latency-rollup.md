# 2026-07-11 — Fleet-wide pickup-latency rollup on /orders (rung 3)

> **Status:** `in-progress` — branch `claude/pickup-latency-rollup`; flips
> to `complete` + the real PR number after the PR exists.

- **📊 Model:** claude-fable-5 · worker · routine-fired build slice (continuous mode, slice 29 — 14:32Z nudge) — family from this session's own harness, per ORDER 010.

**What this session was about:** the 14:32Z nudge; ritual clean (no new
orders, no collision; sibling PR #132 re-checked: still OPEN, green
check, unchanged 52 min — under the stale threshold, hands off), so rung
3 with the designated pick: **fleet-wide pickup-latency rollup** — slice
28 made per-order filed→claimed latency visible, but per-order latency
is trivia until it trends: a median/max summary chip plus a per-repo
median turns the routing SLO into a manageable number the manager sweep
can watch, and a single slow-pickup lane is exactly what it should catch
early. Medians resist the one-weird-timestamp outlier; the rollup is
honest when zero orders carry latency (no invented stats).

## What was done

- (work in progress — filled at close-out)
