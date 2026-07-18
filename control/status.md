# websites · status

updated: 2026-07-18T18:42:02Z
phase: NAV-guard sweep landed — all four service router-introspection NAV-completeness tests are on origin/main (review PR #416, botsite+dashboard PR #418); claims dir clear; no in-progress card. Backlog is owner-gated ladder + hub-venue wiring (baton below).
health: green — four service suites green on origin/main (1926 passed at the #418 landing), kit check --strict green, zero born-red holds (claims/ holds only README.md).
last-shipped: NAV-completeness guards — review PR #416 (merge 0e769d5) + botsite/dashboard PR #418 (merge 13c1804), with claim cleanups #417 / #419; all terminal on origin/main.
blockers: none
orders: acked=001-033 done=001-020,022-033 (021 open, owner-gated — the ORDER 021 owner-environments hub).
routine: failsafe cron `trig_01FYyvu2EytWF5NSEzLU2qLD` "Websites failsafe wake" `45 */2 * * *` ARMED, still bound to the predecessor session (successor bridge by design); rebind rides the hub venue (this coordinator's trigger/send_later arming is classifier-denied 2026-07-18). send_later chain: none pending.
landing: all-merged — PRs #414–#419 terminal on origin/main, 0 open coordinator PRs (draft #413 = coordinator rescue doc, close-without-merge disposition, excluded from the landing count).
deployed: origin/main at 60c67fd · four Railway services live (control-plane-…-abb0 / botsite-…-cfd7 / dashboard-…-a91b / review-…-fc91, the superbot-websites project). O-020 owner writeback LIVE + verified; RAILWAY_API_KEY enables self-verifying/setting deployed env (docs/CAPABILITIES.md).
claims: none active — claims/ holds only README.md.
needs-owner: the 15 ⚑ rows in docs/owner/OWNER-ACTIONS.md (mirror below).

## NEXT-2-TASKS baton
1. HUB VENUE — wire `python3 review/gen_releases.py` into `.github/workflows/review-bake.yml` (daily auto-rebake of review/data/releases.json for hands-off release-drift refresh) AND rebind the failsafe cron to a live session. Both are `.github/workflows/**` / trigger changes → hub venue, not a seat PR.
2. OWNER-GATED LADDER — the 15 ⚑ asks in docs/owner/OWNER-ACTIONS.md await owner input; SITE-CONSOLIDATION RETIREMENT (docs/plans/site-consolidation-cutover.md) is DESTRUCTIVE and awaits the owner's explicit "go". No non-gated seat-buildable increment blocks these.

## ⚑ OWNER-ACTION mirror (canonical: docs/owner/OWNER-ACTIONS.md) — 15 open
ASK-0007 satisfied a prior session; ASK-0002 open with the SuperBot-reuse recon note. ASK-0010 (publish lumen-drift-v1.3) is the release the ORDER 033 drift banner surfaces.
- ASK-0001 — answer Q-0004: where live bot control lives (or keep /admin dry-run).
- ASK-0002 — create the Discord OAuth app for the future armed panel (after Q-0004). RECON 2026-07-18: 0/4 websites-repo services have Discord login; REUSE of the existing SuperBot Discord app is the recommended cheapest path vs a fresh one — pending owner preference. Still OPEN.
- ASK-0003 — provision the scoped control-API token + separate armed Railway service (after Q-0004).
- ASK-0004 — create the botsite submissions PostgreSQL + connection string.
- ASK-0005 — set up PayPal Payouts + put its two credentials on the botsite service.
- ASK-0006 — decide the unwired SITE_PASSWORD on the botsite Railway service (wire or remove).
- ASK-0008 — extend the O-020 PAT with PR write + store as BAKE_PAT Actions secret. NOTE 2026-07-18: the PAT-scope half is already covered — the live control-plane GITHUB_TOKEN holds contents:write + pull-requests:write; only the BAKE_PAT Actions-secret half remains open (unblocks hands-off nightly bake).
- ASK-0009 — delete the unused SITE_PASSWORD variable from the dashboard service.
- ASK-0010 — publish the lumen-drift-v1.3 release on gba-homebrew (unblocks the arcade Download button).
- ASK-0011 — flip product-forge Settings → Pages → Source to GitHub Actions (unblocks the games-web Play link).
- ASK-0012 — run the Gumroad publish pass for the ten publish-ready titles/products (details in docs/owner/OWNER-ACTIONS.md).
- ASK-0013 — hand off the full-res photo originals for the two wallpaper packs (details in docs/owner/OWNER-ACTIONS.md).
- ASK-0014 — pick the Ultramarine title: "The Widow's Blue" or keep Ultramarine (details in docs/owner/OWNER-ACTIONS.md).
- ASK-0015 — decide the §5 illustration gate for the two picture books + three Puddle Museum editions (details in docs/owner/OWNER-ACTIONS.md).
- ASK-0016 — arrange the native-speaker Dutch proofread for de-papieren-sinaasappel (details in docs/owner/OWNER-ACTIONS.md).

kit: v1.17.0
