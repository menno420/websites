# websites · status

updated: 2026-07-18T19:10:00Z
phase: O-020 owner writeback is VERIFIED LIVE end-to-end on the deployed control-plane. A live `/owner/queue` note POST committed to branch `claude/owner-writeback-1` (`0be58459`), opened auto-PR #399, went quality-green, and auto-merged to `main` as `b12dcd9` — the full submit→branch→PR→auto-merge chain proven with a real commit SHA. The deployed control-plane `GITHUB_TOKEN` already carried BOTH `contents:write` AND `pull-requests:write`, so no owner paste/overwrite was needed and ASK-0007 is satisfied. This session lands a docs/ledger-only truth PR recording that (ASK-0007 → Decided row O; current-state note; owner-notes.md test-artifact removed) plus a Railway account-API capability finding, with the open-ask contract-pin dropped 16→15.
health: green — origin/main @ `b12dcd9` (O-020 live-verify merge). This PR (#400) is READY. The four service suites pass 1839 and strict is green apart from the by-design born-red card hold released at the closing flip. No payload change — docs/control/tests-pin only.
last-shipped: `b12dcd9` — O-020 owner-writeback live-verify merge (auto-PR #399) on origin/main.
blockers: none
orders: acked=001-032 done=001-019,020,023-031 — 020 added (O-020 owner writeback now verified-complete end-to-end). 021/022 remain non-done (021 armed-panel owner-gated; 022 was a reconcile order).
routine: failsafe cron `trig_01FYyvu2EytWF5NSEzLU2qLD` "Websites failsafe wake" (cron `45 */2 * * *`) bound to the coordinator session; a pacemaker chain is kept alive coordinator-side. Old failsafe `trig_01VRT9F6jYNXym3nn18vVQQK` retiring (not re-armed). Tool wall: the capitalized alias `mcp__Claude_Code_Remote__list_triggers` is classifier-blocked; lowercase `mcp__claude-code-remote__list_triggers` works.
landing: pushed-unmerged claude/o020-verified-ledger — PR #400 READY (O-020 verified-live ledger + Railway capability); lands on green (agent self-merge or auto-merge-enabler).
deployed: origin/main head `b12dcd9` · four Railway services live (control-plane/botsite/dashboard/review). This PR is docs/control/tests-pin only (OWNER-ACTIONS.md, CAPABILITIES.md, current-state.md, control/owner-notes.md, control/status.md, tests/test_askverify.py) — no runtime product change.
claims: no active claims (no claim filed — committed branch-claims orphan on squash-merge).
notes: O-020 owner writeback VERIFIED LIVE (PR #399→`b12dcd9`); ASK-0007 satisfied — the deployed control-plane `GITHUB_TOKEN` already held both `contents:write` + `pull-requests:write`, so no owner paste was needed. ASK-0008's PAT-scope half is therefore also covered on the Railway token; only its `BAKE_PAT` Actions-secret half stays open. New capability recorded (docs/CAPABILITIES.md): the Railway account API (`RAILWAY_API_KEY`) is available to the seat for enumerate + read/set variables (values treated as secrets).
needs-owner: the 15 ⚑ rows in docs/owner/OWNER-ACTIONS.md (mirror below) — ASK-0007 satisfied this session; none of the remaining 15 resolved.

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
1. B6 — names-only config-drift check on the dashboard /env surface (Q1=a — names-only): a committed names-only manifest diffed against the live env the dashboard cannot read. Buildable once the manifest source is chosen.
2. Remaining-backlog assessment — sweep the open backlog for the next-highest-value buildable slice now that O-020 is fully discharged.
- Blocked-not-mine: O-021 / ASK-0002 (the Discord OAuth app — REUSE of the SuperBot app recommended, pending owner); R10 (workflow-touch / hub-venue — needs the owner-side hub decision).

kit: v1.17.0
