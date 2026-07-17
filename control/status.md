# websites · status

updated: 2026-07-17T00:16:58Z
phase: failsafe-wake lane, overnight work-loop cycle 11 (ORDER 032) — no change since cycle 10 (main unchanged, no new order, ASK-0017 still unresolved). Judgment call: throttling back to check-only cycles for now rather than opening a 16th branch — 15 unlanded branches already carry a full night's real work (5 feature/test slices + 2 filed asks + 8 heartbeats); more unlandable branches add pile, not value. Will resume building the moment ASK-0017 lands, a new inbox order arrives, or a genuinely high-value idea surfaces. Updated THIS heartbeat in place rather than branching again, same as cycles 4/5's precedent.
health: green — origin/main unchanged @ e0a3cc0 (#374). No code touched this cycle — no suite re-run; last real run (cycle 9) was 1644 passed.
orders: acked=001-032 done=001-019,023-031 (020/021 owner-gated; 022 standing; 031 ack'd; 032 STANDING — overnight autonomy, superseding 031's re-arm caution for tonight).
landed-tonight: 7 PRs on main — #345, #357, #362, #365, #368, #369, #370 (per #374's coordinator heartbeat) — unchanged.
open-PRs (per #374's coordinator heartbeat, unchanged, not independently re-verified): #359 automated fleet-data bake, blocked on ASK-0008; #361/#363/#367 rescue straggler-card drafts, born-red by design, held.
staged (owner-gated, per #374): the auto-merge draft-gap patch awaits the owner's first-hand go.
⚑ FINDINGS awaiting your review (unchanged since cycle 10, both filed as proper asks — see needs-owner): ASK-0018, a real public-facing catalog-status error (the-paper-orange).
landing simplification for whoever lands this lane's work: of the 15 branches below, 7 are sequential heartbeat-only overwrites (2049→2350) where only the LATEST (claude/heartbeat-20260716-2350, this one) matters — the other 6 are fully superseded and safe to ignore/close without opening their PRs. The remaining 8 are each independent and worth landing on their own: arcade-catalog-blockers + games-availability-summary (pre-dating this failsafe session), and this lane's own fastlane-pin-map, storefront-freshness-pin, claim-pr-fallback, catalog-sha-drift-pin, catalog-drift-review, and pr-tooling-ask.
blocked (this lane, all carrying ASK-0017 — org GitHub App not connected, re-verified this cycle, verbatim unchanged all night): claude/failsafe-heartbeat-20260716-2049 (superseded), claude/arcade-catalog-blockers, claude/games-availability-summary, claude/pr-tooling-ask-20260716 (files ASK-0017), claude/heartbeat-20260716-2145 (superseded), claude/fastlane-pin-map-20260716, claude/heartbeat-20260716-2215 (superseded), claude/storefront-freshness-pin-20260716, claude/heartbeat-20260716-2245 (superseded), claude/claim-pr-fallback-20260716, claude/heartbeat-20260716-2310 (superseded), claude/catalog-sha-drift-pin-20260716, claude/heartbeat-20260716-2335 (superseded), claude/catalog-drift-review-20260716 (files ASK-0018), claude/heartbeat-20260716-2350 (current, this overwrite) — 15 branches, 7 superseded / 8 worth landing. Per ORDER 032 item 1, expected, not a stall.
routine: this lane's 15-min work-loop chain re-armed every cycle tonight (11 cycles since ~20:53Z) · fixed 45-*/2 failsafe cron also present, trig_01Cn7F2UvE62uDykSYQCDhtF.
needs-owner: the 16 ⚑ rows in docs/owner/OWNER-ACTIONS.md (mirror below) PLUS ASK-0017 (org GitHub App — blocks all 15 branches above) PLUS ASK-0018 (catalog.json content fixes — see finding above; note both ASK-0017 and ASK-0018 are filed on different unmerged branches from this lane and may need a number reconciled at landing time, see the ASK-0018 block's own note).

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
- ASK-0017 — connect the Claude GitHub App for the org (unlanded — see blocked above).
- ASK-0018 — review + apply the catalog.json drift fixes, esp. the-paper-orange's status error (unlanded — see NEW FINDING above).

## NEXT-2-TASKS baton
1. Owner lands the staged auto-merge draft-gap patch, and separately connects the GitHub App (ASK-0017) — either unblocks a large backlog of already-built, already-green work (15 branches from this lane alone, spanning 5 real feature/test/review slices).
2. This lane: baton is otherwise open — pick fresh self-initiated work from docs/ideas/backlog.md (check `built`/`retired` status first), or continue the manual-review pattern this cycle established on other drift-pin findings if any more surface.

kit: v1.17.0
