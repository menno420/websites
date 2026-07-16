# websites · status

updated: 2026-07-16T23:37:13Z
phase: failsafe-wake lane, overnight work-loop cycle 9 (ORDER 032) — fourth backlog slice this lane: catalog sha-drift pin, live-verified against the real repo before shipping. Notable: found this lane had wrongly written off the idea twice on an unverified assumption ("needs live API") — testing the actual wall (raw.githubusercontent.com, not api.github.com) reopened it.
health: green — origin/main unchanged @ e0a3cc0 (#374) this cycle. Full four-suite run THIS session: **1644 passed** (1631 baseline + 13 new); `bootstrap check --strict` green (also regenerated docs/seat-digest.md, stale after the CAPABILITIES.md append).
orders: acked=001-032 done=001-019,023-031 (020/021 owner-gated; 022 standing; 031 ack'd; 032 STANDING — overnight autonomy, superseding 031's re-arm caution for tonight).
landed-tonight: 7 PRs on main — #345, #357, #362, #365, #368, #369, #370 (per #374's coordinator heartbeat) — unchanged this cycle.
open-PRs (per #374's coordinator heartbeat, unchanged this cycle, not independently re-verified): #359 automated fleet-data bake, blocked on ASK-0008; #361/#363/#367 rescue straggler-card drafts, born-red by design, held.
staged (owner-gated, per #374): the auto-merge draft-gap patch awaits the owner's first-hand go.
⚑ NEW FINDING (not owner-blocking, but worth a look this morning): the catalog sha-drift pin's first live run found **9 of 22** `botsite/data/catalog.json` entries have drifted from their pinned venture-lab sha — merge-wall-cookbook, ultramarine, de-waag, het-trage-woord, de-papieren-sinaasappel, bundle-starter, photo-packs, the-night-kiln, the-paper-orange. Two (ultramarine, de-papieren-sinaasappel) line up with your own open ASK-0014/ASK-0016 decisions, plausibly not coincidence. Follow-up idea captured in docs/ideas/backlog.md; nobody has re-verified the actual content diffs yet.
blocked (this lane, all carrying ASK-0017 — org GitHub App not connected, re-verified this cycle, verbatim unchanged): claude/failsafe-heartbeat-20260716-2049, claude/arcade-catalog-blockers, claude/games-availability-summary, claude/pr-tooling-ask-20260716 (files ASK-0017), claude/heartbeat-20260716-2145, claude/fastlane-pin-map-20260716, claude/heartbeat-20260716-2215, claude/storefront-freshness-pin-20260716, claude/heartbeat-20260716-2245, claude/claim-pr-fallback-20260716, claude/heartbeat-20260716-2310, claude/catalog-sha-drift-pin-20260716 (this cycle's slice), claude/heartbeat-20260716-2335 (this overwrite) — 13 branches. Per ORDER 032 item 1, expected, not a stall.
routine: this lane's 15-min work-loop chain re-armed every cycle tonight (9 cycles since ~20:53Z) · fixed 45-*/2 failsafe cron also present, trig_01Cn7F2UvE62uDykSYQCDhtF.
needs-owner: the 16 ⚑ rows in docs/owner/OWNER-ACTIONS.md (mirror below) PLUS ASK-0017 (unlanded — connect the org's Claude GitHub App; the single blocker on all 13 branches above) PLUS the catalog-drift finding above (not a formal ask yet, just flagged for a look).

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
1. Owner lands the staged auto-merge draft-gap patch, and separately connects the GitHub App (ASK-0017) — either unblocks a large backlog of already-built, already-green work (13 branches from this lane alone, spanning 4 real feature/test slices).
2. This lane: re-verify the 9 drifted catalog entries against their current venture-lab packets (docs/ideas/backlog.md, "Regenerate catalog.json's stale pins", 2026-07-16) — now that raw.githubusercontent.com is confirmed reachable, this doesn't need ASK-0017 either.

kit: v1.17.0
