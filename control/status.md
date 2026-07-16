# websites · status

updated: 2026-07-16T21:57:55Z
phase: records/hygiene session (coordinator-dispatched 2026-07-16 night) — landed the owner's live OVERNIGHT ORDER into control/inbox.md as ORDER 032 and refreshed this heartbeat; control/**-only fast-lane PR, no session card (control fast lane).
health: green — origin/main @ da63857 (#357). Last full four-suite run: 1588 passed on the #365 branch (2026-07-16); no code touched this session (control/** only), so no re-run.
orders: acked=001-032 done=001-019,023-031 (020/021 owner-gated; 022 standing; 031 ack'd — EAP extended to 2026-07-21, routines not re-armed pending owner per-seat go; 032 STANDING — owner live overnight-autonomy order, in force through morning).
landed-tonight: 7 PRs merged to main — #345, #357, #362, #365, #368, #369, #370 (coordinator live-verified 5: #345/#357/#368/#369/#370). origin/main HEAD da63857.
open-PRs:
- #359 — automated fleet-data bake (data-only, bot-authored); blocker: hands-off nightly bake needs ASK-0008 (BAKE_PAT PR-write secret); base predates #362's land.
- #361 — rescue: straggler session card; draft, born-red by design (unresolved [[fill:]] slots) — held; a close-out session completes it or owner/coordinator closes.
- #363 — rescue: second straggler card (detached-HEAD session); draft, born-red — held, owner/coordinator disposes.
- #367 — rescue: third straggler card (main-boot auto-draft); draft, born-red — held.
staged (owner-gated): the auto-merge draft-gap patch is staged in a session awaiting the owner's first-hand go-ahead (workflow write needs owner provenance). Green PRs opened overnight wait as ready-to-land drafts pending the owner's morning auto-merge go-ahead.
overnight: planning sessions writing a veto-ready menu of proposals + a build session on contained/reversible slices, per ORDER 032.
routine: failsafe cron 45 */2 present — trig_01VRT9F6jYNXym3nn18vVQQK "Websites failsafe wake" (ORDER 031: routines not re-armed pending the owner's per-seat go).
needs-owner: the 16 ⚑ rows in docs/owner/OWNER-ACTIONS.md (mirror below).

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
1. Owner lands the staged auto-merge draft-gap patch — then it sweeps the green overnight PRs into main.
2. Resume the build loop (contained/reversible slices, one PR each, landed on green) once landing is unblocked.

kit: v1.17.0
