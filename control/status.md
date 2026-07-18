# websites · status

updated: 2026-07-18T17:30:00Z
phase: BUILD+LAND — site-consolidation CUTOVER-PLAN doc + the residual prose/URL corrections, one PR (#410). Part A: `docs/plans/site-consolidation-cutover.md` — an owner-reviewable URL-cutover plan (keep-vs-retire inventory, steps sequenced review→botsite→dashboard with a rollback per step, gated destructive retirement, live-probe verification). Part B: corrected the last prose/URL references that still named the retire target (`f027`) as the canonical review service → `fc91` (the KEEP service), matching #407. Docs-only + one AI system-prompt string + one tester-task URL; no runtime/route change. Destructive steps in the plan are gated on the owner's explicit go — nothing in this PR executes any Railway mutation.
health: green — origin/main advanced (fleet-prompt-state panel #408 landed, main @ `02e1589`). Four service suites pass (1886) unchanged; `check --strict` green apart from the by-design born-red HOLD on THIS PR's card, released at the closing flip.
last-shipped: #408 — /owner Prompt-state panel snapshot-age warning + fleet-manager outbox asks (on origin/main @ `02e1589`).
blockers: none
orders: acked=001-032 done=001-019,020,023-031 — this PR (#410) is a coordinator-dispatched consolidation-track follow-up (the cutover plan-doc + residual prose corrections #407 flagged), not an order.
routine: failsafe cron `trig_01FYyvu2EytWF5NSEzLU2qLD` "Websites failsafe wake" (cron `45 */2 * * *`) bound to the coordinator session; a ~15-min `send_later` pacemaker chain is kept alive coordinator-side. Old failsafe `trig_01VRT9F6jYNXym3nn18vVQQK` retiring (not re-armed). Tool wall: the capitalized alias `mcp__Claude_Code_Remote__list_triggers` is classifier-blocked; lowercase `mcp__claude-code-remote__list_triggers` works.
landing: pushed-unmerged claude/consolidation-cutover-plan — PR #410 READY (site-consolidation cutover plan + prose f027 corrections); merges via auto-merge-enabler on green.
deployed: origin/main head `02e1589` · four Railway services live (control-plane-…-abb0 / botsite-…-cfd7 / dashboard-…-a91b / review-…-fc91, the superbot-websites project). PR #410 is docs-only (`docs/plans/site-consolidation-cutover.md` new; `CONSTITUTION.md`, `docs/current-state.md`, `docs/owner/OWNER-ACTIONS.md`, `docs/eap-closeout-walkthrough-2026-07-14.md`, `docs/plans/discovery-inventory.md`, `review/data/evidence/01-provenance.md` prose) plus one AI system-prompt string (`review/ai.py`) and one tester-task URL (`botsite/testing_tasks.json`) — no route/state surface. O-020 owner writeback is LIVE; the Railway account API (RAILWAY_API_KEY) is available for self-verifying/setting deployed env (see docs/CAPABILITIES.md).
claims: no active claims (no claim filed — committed branch-claims orphan on squash-merge).
notes: the cutover plan is a PLAN only — the keep-vs-retire split is #407's live-Railway ground truth (KEEP superbot-websites abb0/a91b/cfd7/fc91; RETIRE reliable-grace review `f027` + menno420/superbot `superbot-dashboard`/`superbot-app`; NEVER the Discord `worker` bot or the two Postgres DBs). Retirement is a stop→watch→delete sequence with the delete GATED on the owner's explicit per-service go, relayed by the coordinator.
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
1. CONSOLIDATION RETIREMENT (multi-session track) — DESTRUCTIVE, HOLD for the owner's explicit go: FIRST stop/scale-to-zero the reliable-grace olds — review (`review-production-f027`), dashboard (`superbot-dashboard`), botsite (`superbot-app`) — then WATCH for breakage, then delete permanently only on the owner's per-service go. NEVER touch the `worker` Discord bot or the two Postgres DBs. Sequenced + rollback-per-step in `docs/plans/site-consolidation-cutover.md`.
2. FLEET-MANAGER outbox asks (`control/outbox.md`) await manager action — cross-repo: refresh the frozen triggers snapshot + arm the CCR fallback routine, update projects/websites/meta.md to the current paste, and add the self-healing per-seat stamp-at-session-ender rule.
- Blocked-not-mine: ASK-0002 Discord OAuth reuse (gated on ASK-0001 / Q-0004); the R10 auto-draft review-edition workflow (won't self-land, depends on R8 + owner-side hub decision).
- Note: O-020 owner writeback is LIVE; the Railway account API (RAILWAY_API_KEY) is available for self-verifying/setting deployed env (see docs/CAPABILITIES.md).

kit: v1.17.0
