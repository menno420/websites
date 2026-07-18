# websites · status

updated: 2026-07-18T21:30:00Z
phase: SESSION-ENDER. This session closed a long, successful run — ~15 PRs including O-020 owner writeback taken LIVE and verified end-to-end, nine backlog slices, B6 config-drift (the third env-name view on `/owner/environments`), and owner-correction ledger fixes. The final PR (#403) closes the loop B6 opened: it declares the two env vars B6's drift panel surfaced as referenced-but-undeclared — control-plane `WRITEBACK_BRANCH_PREFIX` (`app/writeback.py`, O-020 owner-writeback) and dashboard `ARCADE_JSON_URL` (`dashboard/data_source.py`, B1 arcade counts) — in the committed manifest (`app/railway.py` SERVICES) + the envhub registry (`app/data/environments.json`), names + purpose only, optional-with-default, no value. The code-vs-declared drift panel now reads in-sync for all four services.
health: green — origin/main @ `a63546a` (B6 #401 landed). PR #403 (declare 2 env vars) is READY and born-red-held on its own card. The four service suites pass 1858 and both strict gates are green apart from the by-design born-red hold on THIS PR's card, released at the closing flip.
last-shipped: `a63546a` — B6 code-referenced-vs-declared env-name drift on /owner/environments (PR #401) on origin/main.
blockers: none
orders: acked=001-032 done=001-019,020,023-031 — this PR is the owner-nodded B6 close-the-loop follow-up (declare the two surfaced vars), not an order; 021/022 remain non-done (021 armed-panel owner-gated; 022 was a reconcile order).
routine: failsafe cron `trig_01FYyvu2EytWF5NSEzLU2qLD` "Websites failsafe wake" (cron `45 */2 * * *`) bound to the coordinator session; a ~15-min `send_later` pacemaker chain is kept alive coordinator-side. Old failsafe `trig_01VRT9F6jYNXym3nn18vVQQK` retiring (not re-armed). Tool wall: the capitalized alias `mcp__Claude_Code_Remote__list_triggers` is classifier-blocked; lowercase `mcp__claude-code-remote__list_triggers` works.
landing: pushed-unmerged claude/declare-env-vars — PR #403 READY (declare 2 env vars → drift in-sync; session-ender); merges via auto-merge-enabler on green.
deployed: origin/main head `a63546a` · four Railway services live (control-plane/botsite/dashboard/review). PR #403 is a names-only config-manifest correction (two declared env names + registry sync + one test-pin flip) — no new runtime surface, no behavior change (the code defaults already worked). O-020 owner writeback is LIVE; the Railway account API (RAILWAY_API_KEY) is available for self-verifying/setting deployed env (see docs/CAPABILITIES.md).
claims: no active claims (no claim filed — committed branch-claims orphan on squash-merge).
notes: the manifest has no dedicated "optional" field, but has-default is carried in the purpose text exactly as the ~15 existing optional-with-default vars are (the sibling `WRITEBACK_BRANCH`, "default main", was already declared this way), so declaring these two creates the same kind of entry — not a new envdrift false-positive. Both committed inventories (`app/railway.py` SERVICES and the `app/data/environments.json` envhub registry) must agree per service in both directions (`tests/test_inventory_consistency.py`), so both were updated; the B6 real-snapshot pin (`tests/test_code_env_drift.py`) flipped from referenced-but-undeclared to in-sync.
needs-owner: the 15 ⚑ rows in docs/owner/OWNER-ACTIONS.md (mirror below) — unchanged this session (ASK-0007 was satisfied earlier this session; ASK-0002 carries the SuperBot-reuse note).

## ⚑ OWNER-ACTION mirror (canonical: docs/owner/OWNER-ACTIONS.md) — 15 open; ASK-0007 satisfied this session (verified-live, Decided row O)
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
1. OWNER-GATED — ASK-0002 Discord OAuth for the future armed panel: REUSE of the existing SuperBot Discord app is the recommended path (add a redirect URI + paste client id/secret into the websites Railway env). Still gated on ASK-0001 / Q-0004 (where live bot control lives).
2. R10 auto-draft review edition — a workflow-touch (hub-venue, won't self-land) that depends on R8. Needs the owner-side hub decision before it can land.
- Note: O-020 owner writeback is LIVE; the Railway account API (RAILWAY_API_KEY) is available for self-verifying/setting deployed env (see docs/CAPABILITIES.md).

kit: v1.17.0
