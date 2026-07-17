# websites · status

updated: 2026-07-17T13:18:21Z
phase: fresh-start cleanup (owner-authorized) — docs-only wind-down pass on branch `claude/fresh-start-cleanup`: trued `docs/current-state.md`, added the classifier-safe landing doctrine, added `docs/NEXT-TASKS.md` (curated menus) + `docs/OWNER-STEPS.md` (console-only, names-only), fixed the CONSTITUTION 4th-service (review/) omission, and banner-marked the retiring `control/` + routine apparatus.
health: green — origin/main @ ecbe2bf (#383). Last full four-suite run 1588 (2026-07-16, #365 branch); grown since with #371–#383. This session is docs-only (no app/ source touched).
wind-down: the Claude Code Projects EAP goes READ-ONLY 2026-07-21 (read-only Tuesday). A ~2026-07-15 permission-classifier change froze autonomous merges (agents can no longer ready-flip or REST/MCP-merge). The autonomous apparatus is being RETIRED and the Project will be RECREATED. This heartbeat / message-bus is part of the retirement set — see `docs/NEXT-TASKS.md` → "Wind-down / retirement".
open-PRs: none. The 13 frozen recon PRs (#359–#380) are cleared — the 8 green drafts + bake #380 merged; bake #359 (superseded) and rescue cards #361/#363/#367 closed; follow-on #381/#382/#383 landed.
claims: none active (`control/claims/` holds only its README).
routine: failsafe cron `trig_01VRT9F6jYNXym3nn18vVQQK` ("Websites failsafe wake") — to be retired with the apparatus (owner/console); not re-armed.
landing: PR-tooling — this session opens ONE ready non-draft PR via the GitHub API and does NOT self-merge (classifier-denied); the server-side `auto-merge-enabler` disposition is the owner's.
needs-owner: the 16 ⚑ rows in `docs/owner/OWNER-ACTIONS.md` (mirror below). The console-only subset for this repo is curated names-only in `docs/OWNER-STEPS.md`.

## ⚑ OWNER-ACTION mirror (canonical: docs/owner/OWNER-ACTIONS.md)
- ASK-0001 — answer Q-0004: where live bot control lives (or keep /admin dry-run).
- ASK-0002 — create the Discord OAuth app for the future armed panel (after Q-0004).
- ASK-0003 — provision the scoped control-API token + separate armed Railway service (after Q-0004).
- ASK-0004 — create the botsite submissions PostgreSQL + connection string.
- ASK-0005 — set up PayPal Payouts + put its two credentials on the botsite service.
- ASK-0006 — decide the unwired SITE_PASSWORD on the botsite Railway service (wire or remove).
- ASK-0007 — mint the fine-grained contents-write PAT → GITHUB_TOKEN on control-plane + botsite.
- ASK-0008 — extend that PAT with PR write + store as BAKE_PAT Actions secret (unblocks hands-off nightly bake).
- ASK-0009 — delete the unused SITE_PASSWORD variable from the dashboard service.
- ASK-0010 — publish the lumen-drift-v1.3 release on gba-homebrew (unblocks the arcade Download button).
- ASK-0011 — flip product-forge Settings → Pages → Source to GitHub Actions (unblocks the games-web Play link).
- ASK-0012 — run the Gumroad publish pass for the ten publish-ready titles/products (details in docs/owner/OWNER-ACTIONS.md).
- ASK-0013 — hand off the full-res photo originals for the two wallpaper packs (details in docs/owner/OWNER-ACTIONS.md).
- ASK-0014 — pick the Ultramarine title: "The Widow's Blue" or keep Ultramarine (details in docs/owner/OWNER-ACTIONS.md).
- ASK-0015 — decide the §5 illustration gate for the two picture books + three Puddle Museum editions (details in docs/owner/OWNER-ACTIONS.md).
- ASK-0016 — arrange the native-speaker Dutch proofread for de-papieren-sinaasappel (details in docs/owner/OWNER-ACTIONS.md).

## NEXT-2-TASKS baton
1. Owner: recreate the Project from `main` once the EAP successor is chosen; strip the retired routine/heartbeat/coordinator apparatus (this file included) per `docs/NEXT-TASKS.md`.
2. Land the curated service backlog in `docs/NEXT-TASKS.md` and clear the console steps in `docs/OWNER-STEPS.md`.

kit: v1.17.0
