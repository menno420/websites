# websites · status

updated: 2026-07-18T14:30:00Z
phase: ledger/doc truth PR — a DOCS/LEDGER truth correction (no product code, serialized JSON, env, or workflow touched). Corrects a factually wrong wind-down claim and appends dated recon/clarify notes to two open owner asks. (A) the repo does NOT go read-only 2026-07-21 — only the Claude Code Projects EAP session surface winds down; the repo + all four Railway services stay live/writable and the owner continues via normal chat, so the deadline-pressure framing is removed. (B) ASK-0002 (Discord OAuth) gains a dated recon note — 0/4 websites-repo services have Discord login (the working login the owner saw is the SuperBot dashboard in a different fleet repo); status stays OPEN. (C) ASK-0007 (the O-020 write PAT) gains a status clarification — writeback code is fully built/merged; only the Railway control-plane `GITHUB_TOKEN` paste + a live commit-SHA confirm remains, plus the direct-to-main vs `WRITEBACK_BRANCH`+PR design question; stays OPEN. (D) CAPABILITIES records the PAT-proxy wall. Branch `claude/ledger-truth-fixes`.
health: green — origin/main @ 42da7b7 (PR #395, X2 test-coverage bundle, landed). This PR #397 adds docs/ledger corrections only; the four service suites pass 1828 and strict is green apart from the by-design born-red card hold released at the closing flip.
last-shipped: #395 — origin/main head 42da7b7.
orders: acked=001-032 done=001-019,023-031 — unchanged. This ledger-truth PR is a coordinator-dispatched correction, not an order completion.
routine: failsafe cron `trig_01FYyvu2EytWF5NSEzLU2qLD` "Websites failsafe wake" (cron `45 */2 * * *`) bound to the coordinator session; a pacemaker chain is kept alive coordinator-side. Old failsafe `trig_01VRT9F6jYNXym3nn18vVQQK` retiring (not re-armed). Tool wall: the capitalized alias `mcp__Claude_Code_Remote__list_triggers` is classifier-blocked; lowercase `mcp__claude-code-remote__list_triggers` works.
blockers: none
landing: pushed-unmerged claude/ledger-truth-fixes — PR #397 READY (ledger/doc truth fixes: read-only claim corrected + ASK-0002/0007 recon/clarify notes + CAPABILITIES PAT-proxy wall); merges via server-side auto-merge-enabler on green (agents cannot self-merge, classifier since 2026-07-15). Open PRs: this one.
deployed: 42da7b7 · four Railway services live (control-plane/botsite/dashboard/review). This PR is docs/ledger only — edits to `docs/current-state.md`, `docs/owner/OWNER-ACTIONS.md`, `docs/CAPABILITIES.md`, `docs/seat-digest.md` (derived render), `control/status.md` (this heartbeat), + the session card. No product code, env, workflow, or serialized JSON touched.
claims: no active claims (no claim filed — committed branch-claims orphan on squash-merge, so a branch-named claim would outlive its branch and red main post-merge; the #387 cleanup class).
notes: read-only 07-21 claim CORRECTED — only the EAP session surface (the Projects agent apparatus) winds down ~2026-07-21; the repo stays a normal writable GitHub repo and the owner keeps working via normal chat outside Projects. No repo freeze, no land-before-then deadline. The four Railway services stay live. (Prior heartbeats carried the wrong "repo goes READ-ONLY 2026-07-21" framing — this PR removes it from the tracked docs.)
needs-owner: the 16 ⚑ rows in docs/owner/OWNER-ACTIONS.md (mirror below) — none resolved this session; ASK-0002 + ASK-0007 gained dated recon/clarification notes (both still OPEN).

## ⚑ OWNER-ACTION mirror (canonical: docs/owner/OWNER-ACTIONS.md) — 16 open; ASK-0002 + ASK-0007 gained recon/clarification notes this session (still open)
- ASK-0001 — answer Q-0004: where live bot control lives (or keep /admin dry-run).
- ASK-0002 — create the Discord OAuth app for the future armed panel (after Q-0004). RECON 2026-07-18: 0/4 websites-repo services have Discord login; the working login the owner saw is the SuperBot dashboard (different fleet repo). Cheapest path likely REUSE of the existing SuperBot Discord app vs a fresh one — pending owner preference. Still OPEN.
- ASK-0003 — provision the scoped control-API token + separate armed Railway service (after Q-0004).
- ASK-0004 — create the botsite submissions PostgreSQL + connection string.
- ASK-0005 — set up PayPal Payouts + put its two credentials on the botsite service.
- ASK-0006 — decide the unwired SITE_PASSWORD on the botsite Railway service (wire or remove).
- ASK-0007 — mint the fine-grained contents-write PAT → GITHUB_TOKEN on control-plane + botsite. CLARIFIED 2026-07-18: O-020 writeback code is fully built/merged; only remaining step is the Railway control-plane GITHUB_TOKEN paste + a live commit-SHA confirm, plus the direct-to-main vs WRITEBACK_BRANCH+PR design choice. Still OPEN.
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
1. O-020 activation is an owner infra step — paste a contents:write PAT into the Railway control-plane `GITHUB_TOKEN` — plus a design choice: direct-to-main (if the PAT is a ruleset bypass actor) vs `WRITEBACK_BRANCH`+PR (reviewable, ruleset-safe). The seat cannot verify PAT write scope (CAPABILITIES 2026-07-18 proxy wall) — verify live on Railway.
2. B6 — config-drift flags on the dashboard /env surface — parked pending an owner a/b design call (a names-only committed manifest vs the live env the dashboard cannot read).
- Blocked-not-mine: O-021 / ASK-0002 (the Discord OAuth app — reuse-vs-fresh pending owner); R10 (workflow-touch / hub-venue — needs the owner-side hub decision).

kit: v1.17.0
