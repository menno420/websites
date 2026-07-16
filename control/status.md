# websites · status

updated: 2026-07-16T23:10:41Z
phase: failsafe-wake lane, overnight work-loop cycle 8 (ORDER 032) — third backlog slice this lane: claim-bullet PR-number fallback closing the claims-drift gate's pruned-ref blind spot (2026-07-14 idea). Re-probed the API wall before writing this heartbeat — still blocked, verbatim unchanged from earlier tonight.
health: green — origin/main unchanged @ e0a3cc0 (#374) this cycle. Full four-suite run THIS session: **1636 passed** (1631 baseline + 5 new); `bootstrap check --strict` green.
orders: acked=001-032 done=001-019,023-031 (020/021 owner-gated; 022 standing; 031 ack'd; 032 STANDING — overnight autonomy, superseding 031's re-arm caution for tonight).
landed-tonight: 7 PRs on main — #345, #357, #362, #365, #368, #369, #370 (per #374's coordinator heartbeat) — unchanged this cycle.
open-PRs (per #374's coordinator heartbeat, unchanged this cycle, not independently re-verified): #359 automated fleet-data bake, blocked on ASK-0008; #361/#363/#367 rescue straggler-card drafts, born-red by design, held.
staged (owner-gated, per #374): the auto-merge draft-gap patch awaits the owner's first-hand go.
blocked (this lane, all carrying ASK-0017 — org GitHub App not connected, re-verified this cycle via a direct API probe, verbatim unchanged: "An org admin must connect the Claude GitHub App for this organization"): claude/failsafe-heartbeat-20260716-2049, claude/arcade-catalog-blockers, claude/games-availability-summary, claude/pr-tooling-ask-20260716 (files ASK-0017), claude/heartbeat-20260716-2145, claude/fastlane-pin-map-20260716, claude/heartbeat-20260716-2215, claude/storefront-freshness-pin-20260716, claude/heartbeat-20260716-2245, claude/claim-pr-fallback-20260716 (this cycle's slice), claude/heartbeat-20260716-2310 (this overwrite) — 11 branches. Per ORDER 032 item 1, expected, not a stall.
routine: this lane's 15-min work-loop chain re-armed every cycle tonight (8 cycles since ~20:53Z) · fixed 45-*/2 failsafe cron also present, trig_01Cn7F2UvE62uDykSYQCDhtF — that cron independently fired once this cycle (verify-in-one-line check, confirmed alive, no action taken).
needs-owner: the 16 ⚑ rows in docs/owner/OWNER-ACTIONS.md (mirror below) PLUS ASK-0017 (unlanded — connect the org's Claude GitHub App; the single blocker on all 11 branches above, now 4 cycles running with zero movement).

## ⚑ OWNER-ACTION mirror (canonical: docs/owner/OWNER-ACTIONS.md)
- ASK-0001 — answer Q-0004: where live bot control lives (or keep /admin dry-run).
- ASK-0002 — create the Discord OAuth app for the future armed panel (after Q-0004).
- ASK-0003 — provision the scoped control-API token + separate armed Railway service (after Q-0004).
- ASK-0004 — create the botsite submissions PostgreSQL + connection string.
- ASK-0005 — set up PayPal Payouts + put its two credentials on the botsite service.
- ASK-0006 — set SITE_PASSWORD on the botsite Railway service.
- ASK-0007 — mint the fine-grained contents-write PAT → GITHUB_TOKEN on control-plane + botsite.
- ASK-0008 — extend that PAT with PR write + store as BAKE_PAT Actions secret (unblocks hands-off nightly bake).
- ASK-0009 — delete the unused SITE_PASSWORD variable from the dashboard service.
- ASK-0010 — publish the lumen-drift-v1.3 release on gba-homebrew (unblocks the arcade Download button; machine-probed — the #365 drift pass now watches it every healthcheck).
- ASK-0011 — flip product-forge Settings → Pages → Source to GitHub Actions (unblocks the games-web Play link; machine-probed — same drift-pass watch).
- ASK-0012 — run the Gumroad publish pass for the ten publish-ready titles/products (details in docs/owner/OWNER-ACTIONS.md).
- ASK-0013 — hand off the full-res photo originals for the two wallpaper packs (details in docs/owner/OWNER-ACTIONS.md).
- ASK-0014 — pick the Ultramarine title: "The Widow's Blue" or keep Ultramarine (details in docs/owner/OWNER-ACTIONS.md).
- ASK-0015 — decide the §5 illustration gate for the two picture books + three Puddle Museum editions (details in docs/owner/OWNER-ACTIONS.md).
- ASK-0016 — arrange the native-speaker Dutch proofread for de-papieren-sinaasappel (details in docs/owner/OWNER-ACTIONS.md).

## NEXT-2-TASKS baton
1. Owner lands the staged auto-merge draft-gap patch, and separately connects the GitHub App (ASK-0017) — either one unblocks a large backlog of already-built, already-green work across lanes (11 branches from this lane alone, spanning 3 real feature/test slices plus heartbeats).
2. This lane: docs/ideas/backlog.md still has many un-built `captured` entries needing no live GitHub API — next session should re-scan for one not already superseded (check `built`/`retired` status first; this lane found one already-shipped idea by mistake early tonight before verifying).

kit: v1.17.0
