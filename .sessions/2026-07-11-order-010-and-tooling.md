# 2026-07-11 — ORDER 010 executed (model-attribution ground truth) + cron-slot helper + review-row check

> **Status:** `in-progress` — branch `claude/order-010-and-tooling`; flips
> to `complete` + the real PR number after the PR exists.

- **📊 Model:** claude-fable-5 · worker · routine-fired build slice (continuous mode, slice 14 — 03:31Z nudge) — family reported by this session's own harness ("You are powered by … claude-fable-5" system context), NOT read off the Routines screen, per ORDER 010's ground-truth rule.

**What this session was about:** the 03:31Z send_later continuation.
`scripts/open_work.py` at wake surfaced a NEW branch → open PR #94: the
manager relaying **ORDER 010** (model-attribution ground truth, P3) onto the
bus; the relay session had ended, so this chain merged #94 to unblock the
bus, claimed 010 on main (PR #95, `claimed-by: 010 websites-continuous-wake
2026-07-11T03:36Z`), and executes it here — rung 1. Bundled rung-3 picks
(b) the **cron-slot helper** (this chain shipped five heartbeats with the
same wrong hand-computed cron slot) and (c) the **review-row auto-check**
(the fleet review-queue's binding 50-line rule is enforced by memory; this
repo owes rows for #67/#72/#75/#77 and nobody flagged them mechanically).

## What was done

- (work in progress — filled at close-out)
