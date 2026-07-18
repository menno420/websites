# websites · status

updated: 2026-07-18T15:45:00Z
phase: BUILD+LAND — one contained data-integrity PR for the duplicate-sites consolidation track. The repo's service inventory had the OLD/NEW (canonical vs duplicate) project membership INVERTED vs live Railway ground truth: the superbot-websites deploys (control-plane-…-abb0 / dashboard-…-a91b / botsite-…-cfd7 / review-…-fc91) were labeled duplicates and the reliable-grace ones (review-…-f027 + the menno420/superbot dashboard/botsite) canonical — so a consolidation cutover run off this data would retire the estate we KEEP, and the review redirect + deploy-drift healthchecks pointed at / probed the retire target (f027). FIX: un-invert the inventory across the config/data/scripts and the tests that pin them so canonical = superbot-websites (abb0/a91b/cfd7/fc91) and old/duplicate = reliable-grace (review f027, superbot-dashboard, superbot-app); review redirect default corrected f027→fc91. Decide-and-flag, reversible (all in git); prerequisite for a safe cutover.
health: green — origin/main advanced (redirects #406 landed, main @ `d8ad1d9`). Four service suites pass (1882) after the inventory correction; both strict kit gates green apart from the by-design born-red hold on THIS PR's card, released at the closing flip.
last-shipped: `d8ad1d9` — dashboard /games+/reviews consolidation redirects (PR #406) on origin/main.
blockers: none
orders: acked=001-032 done=001-019,020,023-031 — this PR (#407) is a coordinator-dispatched consolidation-track data-integrity fix, not an order; 021/022 remain non-done (021 armed-panel owner-gated; 022 was a reconcile order).
routine: failsafe cron `trig_01FYyvu2EytWF5NSEzLU2qLD` "Websites failsafe wake" (cron `45 */2 * * *`) bound to the coordinator session; a ~15-min `send_later` pacemaker chain is kept alive coordinator-side. Old failsafe `trig_01VRT9F6jYNXym3nn18vVQQK` retiring (not re-armed). Tool wall: the capitalized alias `mcp__Claude_Code_Remote__list_triggers` is classifier-blocked; lowercase `mcp__claude-code-remote__list_triggers` works.
landing: pushed-unmerged claude/fix-inverted-service-inventory — PR #407 READY (correct inverted canonical/duplicate service inventory to match live Railway; prerequisite for cutover); merges via auto-merge-enabler on green.
deployed: origin/main head `d8ad1d9` · four Railway services live (control-plane-…-abb0 / botsite-…-cfd7 / dashboard-…-a91b / review-…-fc91, the superbot-websites project). PR #407 touches inventory config/data/scripts (`dashboard/app.py` redirect default, `app/config.py` deploy target, `app/railway.py` SERVICES, `app/data/web_presence.json` + `environments.json`, `scripts/healthcheck.py` + `smoke_crawl.py`, `review/story.py`) + the three tests that pin them — no template/content change, no state-changing surface. O-020 owner writeback is LIVE; the Railway account API (RAILWAY_API_KEY) is available for self-verifying/setting deployed env (see docs/CAPABILITIES.md).
claims: no active claims (no claim filed — committed branch-claims orphan on squash-merge).
notes: ground truth for the correction was coordinator-verified via the Railway API + live `/version` reads (authoritative) — KEEP = superbot-websites (abb0/a91b/cfd7/fc91), OLD/retire = reliable-grace (review f027 = menno420/websites old copy; superbot-dashboard + superbot-app = menno420/superbot). This supersedes the previous session's #406 default reasoning (which held f027 canonical on a self-consistent but inverted repo). Dup row ids renamed off the now-canonical hashes so the id no longer contradicts the url.
needs-owner: the 15 ⚑ rows in docs/owner/OWNER-ACTIONS.md (mirror below) — unchanged this session.

## ⚑ OWNER-ACTION mirror (canonical: docs/owner/OWNER-ACTIONS.md) — 15 open
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

## NEXT-2-TASKS baton
1. DUPLICATE-SITES CONSOLIDATION (multi-session track): review=identical, botsite=superset, dashboard gaps=redirects (closed by #406); inventory now un-inverted (#407). NEXT = the URL-cutover plan doc — KEEP the superbot-websites estate (abb0/a91b/cfd7/fc91), RETIRE the reliable-grace olds (review f027 + the menno420/superbot dashboard/botsite), NEVER the Discord worker — after owner go.
2. FLEET-PROMPT-STATE panel accuracy: snapshot-age banner PR + the 4 fleet-manager outbox asks.
- Blocked-not-mine: ASK-0002 Discord OAuth reuse (gated on ASK-0001 / Q-0004); the R10 auto-draft review-edition workflow (won't self-land, depends on R8 + owner-side hub decision).
- Note: O-020 owner writeback is LIVE; the Railway account API (RAILWAY_API_KEY) is available for self-verifying/setting deployed env (see docs/CAPABILITIES.md).

kit: v1.17.0
