# 2026-07-11 — Order pickup latency on /orders (rung 3, backlog promotion)

> **Status:** `in-progress` — branch `claude/order-pickup-latency`; flips to
> `complete` + the real PR number after the PR exists.

- **📊 Model:** claude-fable-5 · worker · routine-fired build slice (continuous mode, slice 28 — 13:56Z nudge) — family from this session's own harness, per ORDER 010.

**What this session was about:** the 13:56Z nudge; ritual found a NEW
sibling branch (claude/anthropic-review-site) — checked before picking:
its PR #132 is OPEN and active (owner-directed review site, opened
13:37Z), NOT stranded — hands off, no rescue, no double-build. No new
orders, so rung 3 with the designated pick: **order pickup latency** —
the fleet's routing SLO (filed→claimed) is currently invisible; /orders
already parses both halves (the ORDER header's filed timestamp and each
lane's claimed-by stamp) and just never subtracts them. Also riding
along per the nudge: HANDOFF.md → .gitignore (kit v1.11.0 regenerates it
untracked by design; git check-ignore exits 1 today, so a stray
`git add .` would commit it).

## What was done

- (work in progress — filled at close-out)
