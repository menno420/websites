# websites · status

updated: 2026-07-18T20:26:37Z
phase: Fleet Arcade goes fully live — the owner published lumen-drift-v1.3 (ASK-0010) and deployed games-web to Pages (ASK-0011); this session flipped both arcade.json entries (lumen-drift → download, games-web → live), rebaked release-drift (drift_count 1 → 0), and marked both ledger rows satisfied. Two owner asks close; 13 remain. Branch claude/lumen-drift-live pushed for coordinator PR.
health: green — four service suites green + kit check --strict green on this branch (arcade now all-reachable: 3 live, 0 blocked); release-drift bake clean.
last-shipped: in flight — claude/lumen-drift-live (arcade flip ASK-0010/0011 + review release-drift rebake + ledger rows P/Q + tests); predecessor terminal work: NAV-completeness guards (PRs #416/#418, merges 0e769d5 / 13c1804) on origin/main.
blockers: none
orders: acked=001-033 done=001-020,022-033 (021 open, owner-gated — the ORDER 021 owner-environments hub).
routine: failsafe cron `trig_01FYyvu2EytWF5NSEzLU2qLD` "Websites failsafe wake" `45 */2 * * *` ARMED, still bound to the predecessor session (successor bridge by design); rebind rides the hub venue (this coordinator's trigger/send_later arming is classifier-denied 2026-07-18). send_later chain: none pending.
landing: pushed-unmerged claude/lumen-drift-live — born-red claim+card first commit, then the arcade flip; coordinator opens the PR.
deployed: origin/main at 07b4bb9 · four Railway services live (control-plane-…-abb0 / botsite-…-cfd7 / dashboard-…-a91b / review-…-fc91, the superbot-websites project). O-020 owner writeback LIVE + verified; RAILWAY_API_KEY enables self-verifying/setting deployed env (docs/CAPABILITIES.md).
claims: `claude/lumen-drift-live` active (arcade data + review bake + ledger); README.md otherwise.
needs-owner: the 13 ⚑ rows in docs/owner/OWNER-ACTIONS.md (mirror below) — ASK-0010 + ASK-0011 closed this session (Decided rows P/Q).

## NEXT-2-TASKS baton
1. HUB VENUE — wire `python3 review/gen_releases.py` into `.github/workflows/review-bake.yml` (daily auto-rebake of review/data/releases.json for hands-off release-drift refresh) AND rebind the failsafe cron to a live session. Both are `.github/workflows/**` / trigger changes → hub venue, not a seat PR.
2. OWNER-GATED LADDER — the 13 remaining ⚑ asks in docs/owner/OWNER-ACTIONS.md await owner input; SITE-CONSOLIDATION RETIREMENT (docs/plans/site-consolidation-cutover.md) is DESTRUCTIVE and awaits the owner's explicit "go". FOLLOW-UP flagged this session: app/data/web_presence.json still labels Lumen Drift + games-web "pending" on the control-plane /directory page — stale after this flip; a control-plane seat can refresh it (out of this session's arcade/review/ledger scope).

## ⚑ OWNER-ACTION mirror (canonical: docs/owner/OWNER-ACTIONS.md) — 13 open
ASK-0007 satisfied a prior session (Decided row O); ASK-0010 + ASK-0011 satisfied THIS session (Decided rows P/Q — release published + Pages deployed, both verified live). ASK-0002 open with the SuperBot-reuse recon note.
- ASK-0001 — answer Q-0004: where live bot control lives (or keep /admin dry-run).
- ASK-0002 — create the Discord OAuth app for the future armed panel (after Q-0004). RECON 2026-07-18: 0/4 websites-repo services have Discord login; REUSE of the existing SuperBot Discord app is the recommended cheapest path vs a fresh one — pending owner preference. Still OPEN.
- ASK-0003 — provision the scoped control-API token + separate armed Railway service (after Q-0004).
- ASK-0004 — create the botsite submissions PostgreSQL + connection string.
- ASK-0005 — set up PayPal Payouts + put its two credentials on the botsite service.
- ASK-0006 — decide the unwired SITE_PASSWORD on the botsite Railway service (wire or remove).
- ASK-0008 — extend the O-020 PAT with PR write + store as BAKE_PAT Actions secret. NOTE 2026-07-18: the PAT-scope half is already covered — the live control-plane GITHUB_TOKEN holds contents:write + pull-requests:write; only the BAKE_PAT Actions-secret half remains open (unblocks hands-off nightly bake).
- ASK-0009 — delete the unused SITE_PASSWORD variable from the dashboard service.
- ASK-0012 — run the Gumroad publish pass for the ten publish-ready titles/products (details in docs/owner/OWNER-ACTIONS.md).
- ASK-0013 — hand off the full-res photo originals for the two wallpaper packs (details in docs/owner/OWNER-ACTIONS.md).
- ASK-0014 — pick the Ultramarine title: "The Widow's Blue" or keep Ultramarine (details in docs/owner/OWNER-ACTIONS.md).
- ASK-0015 — decide the §5 illustration gate for the two picture books + three Puddle Museum editions (details in docs/owner/OWNER-ACTIONS.md).
- ASK-0016 — arrange the native-speaker Dutch proofread for de-papieren-sinaasappel (details in docs/owner/OWNER-ACTIONS.md).

kit: v1.17.0
