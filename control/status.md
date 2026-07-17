# websites · status

updated: 2026-07-17T11:01:08Z
phase: failsafe-wake lane, overnight/morning work-loop cycle 37 (ORDER 032) — fleet activity continues: 2 more PRs landed (#382, #383) since the last check. This lane's branches still weren't part of any sweep. Synced this heartbeat branch onto the newest main rather than opening yet another branch — updating in place given the sweep hasn't reached this lane's work yet.
health: green — origin/main @ ecbe2bf (#383), fast-forwarded cleanly. No code touched this cycle (heartbeat sync only) — no suite re-run; cycle 36's real run on main was 1713 passed.
orders: acked=001-032 done=001-019,023-031 (020/021 owner-gated; 022 standing; 031 ack'd; 032 STANDING — overnight autonomy, superseded in spirit now that real morning activity is visible, but not formally closed — no new inbox order yet).
landed-this-morning: #371-#383 (13 PRs total now) from OTHER sessions/lanes with working PR tooling, not this one — most recent: #382 (dashboard /ideas lifecycle-status filter), #383 (review hero evidence-citation tally).
open-PRs (unverified this session, no GitHub API — inferred from git branch state): #359 (fleet-data bake, blocked on ASK-0008), #361/#363/#367 (rescue straggler-card drafts, born-red by design, held).
⚑ THIS LANE'S UNLANDED WORK (unchanged status — still needs a PR-capable session or the owner): 15 branches, all pushed, none merged. 8 are independent and worth landing: `arcade-catalog-blockers`, `games-availability-summary` (predate this failsafe session), and this lane's own `fastlane-pin-map-20260716`, `storefront-freshness-pin-20260716`, `claim-pr-fallback-20260716`, `catalog-sha-drift-pin-20260716`, `catalog-drift-review-20260716`, `pr-tooling-ask-20260716` (files ASK-0017). The other 7 are sequential heartbeat overwrites — only `claude/heartbeat-20260717-1035` (this one) matters, the rest (2049→2350) are superseded and can be ignored/closed unopened.
⚑ TWO ASKS STILL AWAITING REVIEW, not yet in the canonical docs/owner/OWNER-ACTIONS.md on main (they're on this lane's unlanded branches): **ASK-0017** (connect the org's Claude GitHub App — this session re-verified it blocked, verbatim unchanged, every cycle tonight including just now) and **ASK-0018** (catalog.json content fixes — a real public-facing status error on `the-paper-orange`, full details on `claude/catalog-drift-review-20260716`).
routine: this lane's work-loop chain re-armed every cycle since ~20:53Z (36 cycles; widened to 30-min spacing after cycle 10 given a long stable no-change stretch) · fixed 45-*/2 failsafe cron also present, trig_01Cn7F2UvE62uDykSYQCDhtF.
needs-owner: the 16 ⚑ rows in docs/owner/OWNER-ACTIONS.md (mirror below) PLUS ASK-0017 PLUS ASK-0018, both unlanded — see the flags above.

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
- ASK-0017 — connect the Claude GitHub App for the org (unlanded — filed on claude/pr-tooling-ask-20260716; blocks all 15 branches above).
- ASK-0018 — review + apply the catalog.json drift fixes, esp. the-paper-orange's status error (unlanded — filed on claude/catalog-drift-review-20260716).

## NEXT-2-TASKS baton
1. If you're reading this while active: opening PRs for the 8 independent branches listed above (arcade-catalog-blockers, games-availability-summary, fastlane-pin-map, storefront-freshness-pin, claim-pr-fallback, catalog-sha-drift-pin, catalog-drift-review, pr-tooling-ask) would land a full night's real, tested work in one pass — each is self-contained and already green.
2. This lane: resume picking fresh backlog slices from docs/ideas/backlog.md now that real activity confirms the fleet is live again.

kit: v1.17.0
