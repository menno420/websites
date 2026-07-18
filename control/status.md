# websites · status

updated: 2026-07-18T21:33:11Z
phase: botsite durable /submit intake shipped (ORDER 034 / ASK-0004) — `botsite/submissions_store.py` (DATABASE_URL-keyed, psycopg/SQLite, fail-soft), `/submit` persists behind the shared same-origin + rate-limit guard, owner-authed `/submit/queue.json`; live the moment the owner sets DATABASE_URL. Backlog stays the owner-gated ladder + hub-venue wiring.
health: green — four service suites green on this branch (1937 passed), kit check --strict green after the ORDER 034 card flip; zero born-red holds (claims/ holds only README.md).
last-shipped: botsite durable /submit storage — PR #425 (`claude/botsite-durable-submissions`): submissions_store.py + wired /submit + /submit/queue.json + psycopg[binary]==3.3.4 pin + DATABASE_URL declared across the env registry; test_submit.py (9 tests).
blockers: none
orders: acked=001-034 done=001-020,022-033 (021 + 034 open, owner-gated: 034 code shipped via PR #425, awaiting owner DATABASE_URL paste — ASK-0004).
routine: failsafe cron `trig_01FYyvu2EytWF5NSEzLU2qLD` "Websites failsafe wake" `45 */2 * * *` ARMED, still bound to the predecessor session (successor bridge by design); rebind rides the hub venue (this coordinator's trigger/send_later arming is classifier-denied 2026-07-18). send_later chain: none pending / classifier-walled.
landing: pushed-unmerged claude/botsite-durable-submissions — PR #425 ready, auto-merge squash armed, releases on the green card flip; 0 open coordinator PRs.
deployed: origin/main at 5689537 · four Railway services live (control-plane-…-abb0 / botsite-…-cfd7 / dashboard-…-a91b / review-…-fc91, the superbot-websites project). O-020 owner writeback LIVE + verified; RAILWAY_API_KEY enables self-verifying/setting deployed env READS — but Railway mutation-provisioning is classifier-walled (reads work, mutations denied at spawn 2026-07-18, docs/CAPABILITIES.md) → ASK-0004 owner-gated.
claims: none active — claims/ holds only README.md.
needs-owner: the 15 ⚑ rows in docs/owner/OWNER-ACTIONS.md (mirror below); ASK-0004 is now code-shipped (PR #425) and narrowed to the one DATABASE_URL paste.

## NEXT-2-TASKS baton
1. HUB VENUE — wire `python3 review/gen_releases.py` into `.github/workflows/review-bake.yml` (daily auto-rebake of review/data/releases.json for hands-off release-drift refresh) AND rebind the failsafe cron to a live session. Both are `.github/workflows/**` / trigger changes → hub venue, not a seat PR.
2. OWNER-GATED LADDER — the 15 ⚑ asks in docs/owner/OWNER-ACTIONS.md await owner input; ASK-0004 (botsite /submit) is now one DATABASE_URL paste from live (code shipped, PR #425). SITE-CONSOLIDATION RETIREMENT (docs/plans/site-consolidation-cutover.md) is DESTRUCTIVE and awaits the owner's explicit "go". No non-gated seat-buildable increment blocks these.

## ⚑ OWNER-ACTION mirror (canonical: docs/owner/OWNER-ACTIONS.md) — 15 open
ASK-0007 satisfied a prior session; ASK-0002 open with the SuperBot-reuse recon note. ASK-0010 (publish lumen-drift-v1.3) is the release the ORDER 033 drift banner surfaces. ASK-0004 is code-shipped (PR #425) — one DATABASE_URL paste from live.
- ASK-0001 — answer Q-0004: where live bot control lives (or keep /admin dry-run).
- ASK-0002 — create the Discord OAuth app for the future armed panel (after Q-0004). RECON 2026-07-18: 0/4 websites-repo services have Discord login; REUSE of the existing SuperBot Discord app is the recommended cheapest path vs a fresh one — pending owner preference. Still OPEN.
- ASK-0003 — provision the scoped control-API token + separate armed Railway service (after Q-0004).
- ASK-0004 — create the botsite submissions PostgreSQL + set DATABASE_URL on botsite. CODE SHIPPED (PR #425); goes live the moment the variable lands (railway.app project 70198ece → New → Database → PostgreSQL; botsite → Variables → DATABASE_URL = ${{Postgres.DATABASE_URL}}). Provisioning attempted this session via the account API — classifier-walled ×2 (docs/CAPABILITIES.md 2026-07-18); owner UI action.
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
