# websites · status

updated: 2026-07-18T20:05:00Z
phase: B6 config-drift built and landing. The gated `/owner/environments` page already held the COMMITTED per-service declared env manifest (`app/railway.py` SERVICES) and the committed-vs-LIVE Railway name diff (`app/envdrift.py`); B6 adds the missing third axis — code-referenced-vs-declared drift (Q1=a: contained, names-only, static). A build-time AST scan (`app/gen_env_coderefs.py`, the `review/gen_*.py` idiom) bakes the env-var NAMES each service's runtime code reads into a committed names-only snapshot (`app/data/env_coderefs.json`); `app/codedrift.py` diffs it against the manifest and flags referenced-but-undeclared (a deploy silently gets an empty value) and declared-but-unreferenced (stale) per service, with PORT/GIT_SHA/RAILWAY_* carved out as informational (consistent with envdrift). No source scan and no Railway call at request time — the deployed control-plane reads the baked snapshot. First real finds surfaced by the feature: control-plane `WRITEBACK_BRANCH_PREFIX` and dashboard `ARCADE_JSON_URL` are read by runtime code but absent from the manifest; botsite and review are in sync.
health: green — origin/main @ `e0d94f2` (O-020 verified-live #400 landed). PR #401 (B6) is READY. The four service suites pass 1858 (1839 + 19 new) and strict is green apart from the by-design born-red card hold released at the closing flip.
last-shipped: `e0d94f2` — O-020 verified-live ledger + Railway-API capability (PR #400) on origin/main.
blockers: none
orders: acked=001-032 done=001-019,020,023-031 — B6 is a backlog item (owner-decided Q1=a), not an order; 021/022 remain non-done (021 armed-panel owner-gated; 022 was a reconcile order).
routine: failsafe cron `trig_01FYyvu2EytWF5NSEzLU2qLD` "Websites failsafe wake" (cron `45 */2 * * *`) bound to the coordinator session; a pacemaker chain is kept alive coordinator-side. Old failsafe `trig_01VRT9F6jYNXym3nn18vVQQK` retiring (not re-armed). Tool wall: the capitalized alias `mcp__Claude_Code_Remote__list_triggers` is classifier-blocked; lowercase `mcp__claude-code-remote__list_triggers` works.
landing: pushed-unmerged claude/env-config-drift — PR #401 READY (B6 names-only code-vs-declared config-drift on /owner/environments); merges via auto-merge-enabler on green.
deployed: origin/main head `e0d94f2` · four Railway services live (control-plane/botsite/dashboard/review). PR #401 adds a read-only names-only drift section to the gated /owner/environments page + a build-time generator + committed snapshot + tests — no new runtime network surface.
claims: no active claims (no claim filed — committed branch-claims orphan on squash-merge).
notes: B6 surface chosen after verifying where an env surface actually lives — the control-plane `/owner/environments` page (the real env-manifest surface), not the dashboard `/env` (which renders the Discord bot's env usage from superbot JSON, a different domain). The declared manifest (ii) reuses the existing `app/railway.py` SERVICES; the code-reference source (i) is a committed static-scan snapshot because the deployed control-plane image ships only `app/` (`COPY app ./app`) and cannot scan the other services' source at runtime. Contract-pin added: `tests/test_env_coderefs_snapshot.py` fails the build if the snapshot drifts from a fresh scan.
needs-owner: the 15 ⚑ rows in docs/owner/OWNER-ACTIONS.md (mirror below) — unchanged this session (ASK-0007 was satisfied last session).

## ⚑ OWNER-ACTION mirror (canonical: docs/owner/OWNER-ACTIONS.md) — 15 open; ASK-0007 satisfied (verified-live, Decided row O)
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
1. Honest remaining-backlog assessment — the leftover backlog is largely owner-gated (ASK-0002 Discord OAuth reuse, ASK-0003 armed token/service) or workflow (R10 hub-venue, needs the owner-side hub decision) or superseded by the shipped environments-hub / env-drift surfaces. Sweep for any self-contained buildable slice; otherwise the value is in the assessment itself.
2. Await owner direction — Q-0004 (where live bot control lives) still gates the armed-panel chain (ASK-0001/0002/0003).
- Blocked-not-mine: O-021 / ASK-0002 (the Discord OAuth app — REUSE of the SuperBot app recommended, pending owner); R10 (workflow-touch / hub-venue — needs the owner-side hub decision).

kit: v1.17.0
