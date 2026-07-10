# 2026-07-10 — Heartbeat enrichment: machine-readable fields + /fleet support (queue-state NEXT item 4)

> **Status:** `in-progress` — branch `claude/heartbeat-enrichment`; flips to
> `complete` + PR number as the deliberate LAST code step.

- **📊 Model:** claude-fable-5 · worker · routine-fired build slice (continuous mode, slice 2)

**What this session was about:** slice 2 of the 20:00Z continuous-mode wake
(manager Q-0265). Work-ladder rung 2 again: inbox at HEAD has nothing past
008; queue-state NEXT item 4 / the `planned` backlog bullet — **heartbeat
enrichment** (retro G3): machine-readable outstanding-orders + the `routine:`
(armed-but-silently-dead wake clocks) and `landing:` (stranded-work catch)
sibling captures, parsed by `app/fleet.py` and surfaced on `/fleet` so the
manager computes "what's left" without diffing inbox vs status vs git.

## What was done

- (work in progress — filled at close-out)
