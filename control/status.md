# websites · status

updated: 2026-07-18T17:55:43Z
phase: ORDER 033 landed (review release-drift banner merged via PR #414, claim cleanup #415); this session adds a router-introspection NAV-completeness guard test to the review service — PR #416 open on `claude/review-nav-guard`, born-red card holding, awaiting the completion flip.
health: green locally — four service suites (1920 passed, 1 warning) + kit check --strict green except the DESIGNED born-red hold on this session's in-progress card (PR #416, claude/review-nav-guard). ORDER 033 terminal on origin/main.
last-shipped: ORDER 033 review release-drift banner landed — PR #414 (merge d700938) then claim cleanup #415; both terminal on origin/main.
blockers: none
orders: acked=001-033 done=001-020,022-033 (021 open/owner-gated).
routine: failsafe cron `trig_01FYyvu2EytWF5NSEzLU2qLD` "Websites failsafe wake" `45 */2 * * *` remains ARMED, still bound to the predecessor session (successor bridge kept by design).
    • This coordinator's trigger / send_later arming is classifier-denied (worker relays blocked at spawn), so the rebind-then-delete of the failsafe cron rides the hub venue.
    • send_later chain: none pending (walled).
    • Business crons: none created by this seat.
landing: `pushed-unmerged claude/review-nav-guard` — review NAV-completeness guard test (PR #416 open, born-red card holding, awaiting completion flip).
deployed: origin/main at latest · four Railway services live (control-plane-…-abb0 / botsite-…-cfd7 / dashboard-…-a91b / review-…-fc91, the superbot-websites project). O-020 owner writeback is LIVE + verified; RAILWAY_API_KEY enables self-verifying/setting deployed env (see docs/CAPABILITIES.md).
claims: 1 active — `claude/review-nav-guard` (review NAV-completeness guard test), 2026-07-18; delete at session close.
needs-owner: the 15 ⚑ rows in docs/owner/OWNER-ACTIONS.md (mirror below).

## NEXT-2-TASKS baton
1. WIRE gen_releases.py INTO THE DAILY BAKE — add `python3 review/gen_releases.py` to `.github/workflows/review-bake.yml` so `review/data/releases.json` auto-rebakes daily (hands-off release-drift refresh). Workflow diff → rides the hub venue, deliberately NOT in the ORDER 033 PR.
2. FLEET-MANAGER OUTBOX ASKS 1-4 in `control/outbox.md` await the fleet-manager manager seat (refresh frozen triggers-snapshot.json; update fleet-manager/projects/websites/meta.md to v3.7 / 2026-07-15; self-healing per-seat deployed-version stamp rule).
- Also gated: SITE-CONSOLIDATION RETIREMENT — DESTRUCTIVE, GATED on the owner's explicit "go"; plan at `docs/plans/site-consolidation-cutover.md` (KEEP superbot-websites: control-plane-abb0 / dashboard-a91b / botsite-cfd7 / review-fc91; RETIRE reliable-grace review-production-f027 + old superbot-repo superbot-dashboard / superbot-app; NEVER the reliable-grace `worker` Discord bot or the Postgres DBs).
- Also gated: ASK-0002 Discord OAuth (reuse the existing SuperBot app — owner); R10 auto-draft review edition (workflow / hub-venue).
- Note for the successor: O-020 owner writeback is LIVE + verified; RAILWAY_API_KEY enables self-verifying/setting deployed env (see docs/CAPABILITIES.md).

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
