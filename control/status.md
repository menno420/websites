# websites · status

updated: 2026-07-16T22:26:29Z
phase: failsafe-wake lane, overnight work-loop cycle 6 (ORDER 032) — acked ORDER 032, built + landed-attempted a contained test-only slice (fast-lane grammar-pin map drift pin, backlog idea from 2026-07-13), never stalled on the standing landing blocker per 032's instruction.
health: green — origin/main unchanged @ e0a3cc0 (#374, the coordinator's ORDER-032 control-only heartbeat) this cycle. Full four-suite run THIS session (deps installed fresh this lane): **1634 passed** (1631 baseline + 3 new from the pin-map slice); `bootstrap check --strict` green on the new branch.
orders: acked=001-032 done=001-019,023-031 (020/021 owner-gated; 022 standing; 031 ack'd — EAP extended to 2026-07-21; 032 STANDING — owner live overnight-autonomy order, superseding 031's re-arm caution for tonight specifically: "run autonomously... never stall" is read as the per-seat go for this session's work-loop chain).
landed-tonight: 7 PRs on main — #345, #357, #362, #365, #368, #369, #370 (per #374's coordinator heartbeat, live-verified 5) — unchanged this cycle, this lane's own work has not landed (see blocked below).
open-PRs (per #374's coordinator heartbeat, unchanged this cycle — not independently re-verified, no GitHub API): #359 automated fleet-data bake, data-only, blocked on ASK-0008 (BAKE_PAT); #361/#363/#367 rescue straggler-card drafts, born-red by design, held for a close-out session or owner/coordinator disposal.
staged (owner-gated, per #374): the auto-merge draft-gap patch awaits the owner's first-hand go (workflow write needs owner provenance) — once landed it sweeps the green overnight PRs into main.
blocked (this lane, all carrying the same named blocker — ASK-0017, org GitHub App not connected, this session has no PR-creation tooling and direct push to main is GH013-rejected): claude/failsafe-heartbeat-20260716-2049, claude/arcade-catalog-blockers (730e540), claude/games-availability-summary (d0ead52), claude/pr-tooling-ask-20260716 (files ASK-0017 itself — not yet on main, so the canonical docs/owner/OWNER-ACTIONS.md mirror below is still the pre-ASK-0017 16 rows), claude/fastlane-pin-map-20260716 (this cycle's slice), claude/heartbeat-20260716-2215 (this overwrite). Per ORDER 032 item 1 ("a blocked PR carries its named blocker; take the next slice, never stall") this is expected, not a stall.
overnight: this lane resumed the build loop (contained/reversible slices) per ORDER 032 after 3 heartbeat-only cycles spent confirming the landing wall was structural, not transient.
routine: this lane's 15-min continue-the-work-loop chain re-armed every cycle tonight (6 cycles since ~20:53Z) · fixed 45-*/2 failsafe cron also present, trig_01Cn7F2UvE62uDykSYQCDhtF.
needs-owner: the 16 ⚑ rows in docs/owner/OWNER-ACTIONS.md (mirror below) PLUS ASK-0017 (filed on this lane's unlanded claude/pr-tooling-ask-20260716 — connect the org's Claude GitHub App; until landed it won't show in the canonical doc, but it's the single blocker on everything else in "blocked" above).

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
1. Owner lands the staged auto-merge draft-gap patch, and separately connects the GitHub App (ASK-0017) — either one unblocks a large backlog of already-built, already-green work across lanes.
2. This lane: next backlog candidate is the "shared drift_report() renderer" idea (docs/ideas/backlog.md, 2026-07-16) — also self-contained, no GitHub API needed, matches ORDER 032's "small, contained, reversible" bar.

kit: v1.17.0
