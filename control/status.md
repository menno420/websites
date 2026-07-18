# websites · status

updated: 2026-07-18T20:05:30Z
phase: Planning pass landed: groomed next-cycle queue (docs/plans/next-cycle-2026-07-18.md); NEXT-TASKS pruned, current-state refreshed to #421, orphaned claim cleared.
health: green — four service suites green (1928 passed at this planning pass), kit check --strict green apart from the designed born-red hold on the in-progress planning card `claude/next-cycle-plan` (releases at the closing flip); claims/ orphan cleared.
last-shipped: NAV-completeness guard sweep — review PR #416 + botsite/dashboard PR #418 + off-nav reachability PR #421, with claim cleanups #417/#419 and the coordinator-heartbeat true-up #420; all terminal on origin/main (HEAD 07b4bb9).
blockers: none
orders: acked=001-033 done=001-020,022-033 (021 open, owner-gated — the ORDER 021 owner-environments hub).
routine: failsafe cron `trig_01FYyvu2EytWF5NSEzLU2qLD` "Websites failsafe wake" `45 */2 * * *` ARMED, still bound to the predecessor session (successor bridge by design); rebind rides the hub venue (this coordinator's trigger/send_later arming is classifier-denied 2026-07-18). send_later chain: none pending.
landing: pushed-unmerged claude/next-cycle-plan — planning pass PR #423; the born-red planning card holds it red until the closing flip; 0 other open coordinator PRs.
deployed: origin/main at 07b4bb9 · four Railway services live (control-plane-…-abb0 / botsite-…-cfd7 / dashboard-…-a91b / review-…-fc91, the superbot-websites project). O-020 owner writeback LIVE + verified; RAILWAY_API_KEY enables self-verifying/setting deployed env (docs/CAPABILITIES.md).
claims: nav-reachability-guard orphan cleared this pass; control/claims/next-cycle-plan.md is this pass's own in-flight claim (removed at the closing flip per claims README step 4).
needs-owner: the 15 ⚑ rows in docs/owner/OWNER-ACTIONS.md (mirror below).

## NEXT-2-TASKS baton
1. B6 — dashboard `/env` config-drift flags (M · seat · no gate). Cross-check `/env` usage against a committed manifest, flag referenced-but-unset / set-but-unused vars. `dashboard/app.py` `env_page` currently renders only `data_source.env_usage(data)` with no manifest cross-check. Groomed detail: docs/plans/next-cycle-2026-07-18.md §1.
2. review `/questions` empty-state polish (S · verify-first). Confirm `/questions` renders a graceful "no questions answered yet" empty state (`questions.json` is intentionally `[]`); add one if missing. Consistent with the honest-empty design. Groomed detail: docs/plans/next-cycle-2026-07-18.md §4.

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
