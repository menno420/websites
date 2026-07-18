# websites · status

updated: 2026-07-18T14:40:00Z
phase: BUILD+LAND — one contained dashboard PR for the duplicate-sites consolidation track. The OLD dashboard (`superbot-dashboard.up.railway.app`, legacy `menno420/superbot`) serves `/games` and `/reviews`; the NEW dashboard (`dashboard/`, this repo) 404s on both because that content was deliberately RE-HOMED (games → the botsite service, reviews → the review service). FIX: add GET `/games` + `/reviews` routes on the new dashboard that 302-redirect to the re-homed surfaces so inbound links survive cutover. Targets are env-overridable (`BOTSITE_GAMES_URL` / `REVIEW_REVIEWS_URL`) with the repo's canonical NEW service URLs as defaults (botsite-…-cfd7/games, review-…-f027/reviews — NOT the …-fc91 parallel copy that is itself retired at consolidation); honest-degrade to a linking page if a target resolves empty. Redirects, NOT re-adds — the content stays re-homed by doctrine. GET-only, no CSRF surface.
health: green — origin/main advanced (overview #404 + owner-auth-ratelimit landed, main @ `9e5aa75`). Four service suites pass (1882 with the new redirect tests); both strict kit gates green apart from the by-design born-red hold on THIS PR's card, released at the closing flip.
last-shipped: `9e5aa75` — /fleet overview count-badge drill-downs + mobile legibility (PR #404) on origin/main.
blockers: none
orders: acked=001-032 done=001-019,020,023-031 — this PR (#406) is a coordinator-dispatched consolidation-track slice, not an order; 021/022 remain non-done (021 armed-panel owner-gated; 022 was a reconcile order).
routine: failsafe cron `trig_01FYyvu2EytWF5NSEzLU2qLD` "Websites failsafe wake" (cron `45 */2 * * *`) bound to the coordinator session; a ~15-min `send_later` pacemaker chain is kept alive coordinator-side. Old failsafe `trig_01VRT9F6jYNXym3nn18vVQQK` retiring (not re-armed). Tool wall: the capitalized alias `mcp__Claude_Code_Remote__list_triggers` is classifier-blocked; lowercase `mcp__claude-code-remote__list_triggers` works.
landing: pushed-unmerged claude/dashboard-consolidation-redirects — PR #406 READY (dashboard /games+/reviews redirects for site consolidation); merges via auto-merge-enabler on green.
deployed: origin/main head `9e5aa75` · four Railway services live (control-plane/botsite/dashboard/review). PR #406 touches dashboard route code (`dashboard/app.py`) + the env-consistency ledgers the two new env vars cascade to (`app/railway.py` manifest, `app/data/env_coderefs.json` snapshot, `app/data/environments.json` inventory, the hostile-env poison list, the dashboard clarity-gate classification) + tests — no template/content change, no state-changing surface. O-020 owner writeback is LIVE; the Railway account API (RAILWAY_API_KEY) is available for self-verifying/setting deployed env (see docs/CAPABILITIES.md).
claims: no active claims (no claim filed — committed branch-claims orphan on squash-merge).
notes: env-var-with-default idiom for the redirect targets mirrors data_source.py's feed URLs; declared in the dashboard manifest so the B6 env-drift panel reads in-sync. Reconciliation flagged: the coordinator brief's suggested default review URL `…-fc91` is the `review-dup-fc91` parallel copy ("pending consolidation") — pointing a redirect there would BREAK at cutover, so the default uses `review-production-f027` (the repo's canonical review service per app/config.py SERVICE_DEPLOY_TARGETS). Env-overridable, so fully reversible if the coordinator prefers otherwise.
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
1. DUPLICATE-SITES CONSOLIDATION (multi-session track): review=identical, botsite=superset, dashboard gaps=these 2 redirects (now closed by #406). NEXT = a URL-cutover plan doc + retire the OLD reliable-grace parallel services (review-dup-fc91 / botsite-dup-cfd7 / superbot-dashboard — NOT the Discord worker) after owner go.
2. FLEET-PROMPT-STATE panel accuracy fix (trace in progress).
- Blocked-not-mine: ASK-0002 Discord OAuth reuse (gated on ASK-0001 / Q-0004); the R10 auto-draft review-edition workflow (won't self-land, depends on R8 + owner-side hub decision).
- Note: O-020 owner writeback is LIVE; the Railway account API (RAILWAY_API_KEY) is available for self-verifying/setting deployed env (see docs/CAPABILITIES.md).

kit: v1.17.0
