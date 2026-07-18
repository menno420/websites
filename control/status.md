# websites · status

updated: 2026-07-18T16:10:00Z
phase: BUILD+LAND — fleet-prompt-state panel remediation, one PR. The /owner "Prompt state" panel reads the fleet-manager registry LIVE and is correct, but rendered the failsafe-snapshot `captured_at` as a bare timestamp with no age/attribution — so a snapshot frozen upstream (manager-wake telemetry, frozen 2026-07-17T16:32:25Z, >24h) read as OUR bug. FIX (PR #408): (A) compute the snapshot AGE against the injectable `app.clock` (never naive wall-clock) and render it + a ">24h stale — awaiting an upstream fleet-manager refresh" warning that attributes the freeze upstream; (B) draft the 4 cross-repo fleet-manager outbox asks that fix the underlying DATA (refresh the frozen snapshot + arm the CCR fallback routine; update projects/websites/meta.md to the current v3.7 paste; optional new-seat stub note; a self-healing per-seat stamp-at-session-ender rule). Panel reads live — the root fix is cross-repo. Decide-and-flag, reversible (code + control docs only).
health: green — origin/main advanced (inventory-fix #407 landed, main @ `8b29123`). Four service suites pass (1886) with the +4 new deterministic snapshot-age tests; `check --strict` green apart from the by-design born-red HOLD on THIS PR's card, released at the closing flip.
last-shipped: #407 — un-invert the canonical/duplicate service inventory to match live Railway (on origin/main @ `8b29123`).
blockers: none
orders: acked=001-032 done=001-019,020,023-031 — this PR (#408) is a coordinator-dispatched fleet-prompt-state remediation, not an order.
routine: failsafe cron `trig_01FYyvu2EytWF5NSEzLU2qLD` "Websites failsafe wake" (cron `45 */2 * * *`) bound to the coordinator session; a ~15-min `send_later` pacemaker chain is kept alive coordinator-side. Old failsafe `trig_01VRT9F6jYNXym3nn18vVQQK` retiring (not re-armed). Tool wall: the capitalized alias `mcp__Claude_Code_Remote__list_triggers` is classifier-blocked; lowercase `mcp__claude-code-remote__list_triggers` works.
landing: pushed-unmerged claude/fleet-prompt-staleness — PR #408 READY (snapshot-age warning + fleet-manager outbox asks); merges via auto-merge-enabler on green.
deployed: origin/main head `8b29123` · four Railway services live (control-plane-…-abb0 / botsite-…-cfd7 / dashboard-…-a91b / review-…-fc91, the superbot-websites project). PR #408 touches `app/prompts.py` (console_rollup age enrichment), `app/templates/owner.html` (age + stale banner), `tests/test_prompt_surfacing.py` (+4 tests), and `control/outbox.md` (the 4 cross-repo asks) — GET view only, no CSRF/state-changing surface. O-020 owner writeback is LIVE; the Railway account API (RAILWAY_API_KEY) is available for self-verifying/setting deployed env (see docs/CAPABILITIES.md).
claims: no active claims (no claim filed — committed branch-claims orphan on squash-merge).
notes: the panel is CORRECT — it reads the fleet-manager `telemetry/triggers-snapshot.json` failsafe snapshot LIVE and renders it honestly. The stale DATA is upstream: the snapshot is a manager-wake `list_triggers` dump that froze when the manager seat parked, and `projects/websites/meta.md` still records the superseded 2026-07-10 gen-2/v1 state. Part A makes that unmistakable + attributed; the actual data refresh is routed to the manager via the 4 Part-B outbox asks (cross-repo, await manager action).
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
1. DUPLICATE-SITES CONSOLIDATION (multi-session track): inventory now un-inverted (#407). NEXT = the URL-cutover PLAN doc (KEEP the superbot-websites estate abb0/a91b/cfd7/fc91, RETIRE the reliable-grace olds — review f027 + the menno420/superbot dashboard/botsite, NEVER the Discord worker) PLUS the prose f027 corrections still carrying the old inverted canonical: `CONSTITUTION.md`, `docs/current-state.md`, `docs/owner/OWNER-ACTIONS.md`, `review/ai.py`, `botsite/testing_tasks.json`.
2. FLEET-MANAGER outbox asks (this PR's Part B) await manager action — cross-repo: refresh the frozen triggers snapshot + arm the CCR fallback routine, update projects/websites/meta.md to v3.7, and add the self-healing per-seat stamp-at-session-ender rule.
- Blocked-not-mine: ASK-0002 Discord OAuth reuse (gated on ASK-0001 / Q-0004); the R10 auto-draft review-edition workflow (won't self-land, depends on R8 + owner-side hub decision).
- Note: O-020 owner writeback is LIVE; the Railway account API (RAILWAY_API_KEY) is available for self-verifying/setting deployed env (see docs/CAPABILITIES.md).

kit: v1.17.0
