# websites · status

updated: 2026-07-18T17:20:00Z
phase: O-020 writeback routed through a branch + auto-merging PR (Q2=b, owner-confirmed). RUNTIME code change on the deployed control-plane: each gated /owner/queue writeback now commits its append to a per-submit `claude/owner-writeback-<n>` branch and opens a READY auto-merging PR into main, instead of a direct Contents-API PUT to main (impossible — main is ruleset-protected and the PAT cannot bypass it, owner-confirmed). The runtime PR is control/**-only so the CI control fast-lane grades it green with no session card: note/complete relocated from docs/owner/owner-notes.md to control/owner-notes.md, and the generated assist ORDER gained the done-when: field the inbox append-only gate requires. Honest-degrade preserved (no token / branch-create / PUT / PR-open failures stay queued with the exact error; committed claimed only with a verified SHA + open PR). No direct-to-main escape hatch (owner removed it). Branch `claude/writeback-branch-pr`.
health: green — origin/main advanced (X2 test bundle #395; ledger-truth #397 landing). This PR #398 is READY; the four service suites pass 1839 and strict is green apart from the by-design born-red card hold released at the closing flip. Live end-to-end verify is PENDING the deploy + the Railway control-plane GITHUB_TOKEN paste (ASK-0007) — build + unit-tested here with mocks.
last-shipped: #395 — X2 test-coverage bundle on origin/main; #397 ledger-truth landing.
blockers: none
orders: acked=001-032 done=001-019,023-031 — unchanged. This writeback branch+PR change is the O-020 build slice (activation is still the owner's GITHUB_TOKEN paste + live verify), not an order-status completion.
routine: failsafe cron `trig_01FYyvu2EytWF5NSEzLU2qLD` "Websites failsafe wake" (cron `45 */2 * * *`) bound to the coordinator session; a pacemaker chain is kept alive coordinator-side. Old failsafe `trig_01VRT9F6jYNXym3nn18vVQQK` retiring (not re-armed). Tool wall: the capitalized alias `mcp__Claude_Code_Remote__list_triggers` is classifier-blocked; lowercase `mcp__claude-code-remote__list_triggers` works.
landing: pushed-unmerged claude/writeback-branch-pr — PR #398 READY (O-020 writeback via branch+auto-PR, Q2=b; note/complete relocated to control/owner-notes.md + assist ORDER done-when: added for the inbox gate); merges via the server-side auto-merge-enabler on green (agents cannot self-merge). Open PRs: this one (+ #397 ledger-truth if still open).
deployed: origin/main head · four Railway services live (control-plane/botsite/dashboard/review). This PR is RUNTIME product code (app/writeback.py, app/owner.py, owner_queue.html) + control/owner-notes.md (relocated target seed) + docs/owner/owner-notes.md (back-compat pointer) + tests. It deploys with the control-plane; the live writeback chain is verified after deploy + the GITHUB_TOKEN paste.
claims: no active claims (no claim filed — a committed branch-claims file orphans on squash-merge and reds main post-merge; the #387 cleanup class).
notes: Q2=(b) is OWNER-CONFIRMED ("create a PR and auto merge it; I don't think it's possible to commit straight to main with the PAT") — the direct-to-main path was intentionally removed, not kept behind a flag. The PAT the owner pastes needs contents:write AND pull-requests:write (it opens the PR itself); the branch prefix `claude/owner-writeback-` is env-overridable (WRITEBACK_BRANCH_PREFIX) and is what the auto-merge workflows arm.
needs-owner: the 16 ⚑ rows in docs/owner/OWNER-ACTIONS.md (mirror below) — none resolved this session; ASK-0007 now needs only the Railway control-plane GITHUB_TOKEN paste + a live commit/PR confirm (the writeback code, now branch+PR, is fully built/merged-pending).

## ⚑ OWNER-ACTION mirror (canonical: docs/owner/OWNER-ACTIONS.md) — 16 open; ASK-0007 is now paste-and-verify only (writeback branch+PR built)
- ASK-0001 — answer Q-0004: where live bot control lives (or keep /admin dry-run).
- ASK-0002 — create the Discord OAuth app for the future armed panel (after Q-0004). RECON 2026-07-18: 0/4 websites-repo services have Discord login; REUSE of the existing SuperBot Discord app is the recommended cheapest path vs a fresh one — pending owner preference. Still OPEN.
- ASK-0003 — provision the scoped control-API token + separate armed Railway service (after Q-0004).
- ASK-0004 — create the botsite submissions PostgreSQL + connection string.
- ASK-0005 — set up PayPal Payouts + put its two credentials on the botsite service.
- ASK-0006 — decide the unwired SITE_PASSWORD on the botsite Railway service (wire or remove).
- ASK-0007 — mint the fine-grained PAT (contents:write + pull-requests:write) → GITHUB_TOKEN on control-plane. CLARIFIED 2026-07-18: O-020 writeback is fully built and now routes through a branch + auto-merging PR (Q2=b, owner-confirmed via PR #398); only remaining step is the Railway control-plane GITHUB_TOKEN paste + a live submit→branch→PR→auto-merge confirm. Still OPEN.
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
1. O-020 activation — the owner pastes a fine-grained PAT (contents:write + pull-requests:write) into the Railway control-plane `GITHUB_TOKEN`, then the seat live-verifies the full chain: a /owner/queue submit → commit on a `claude/owner-writeback-<n>` branch → auto-merging PR into main → merge on green. The seat cannot verify PAT scope itself (CAPABILITIES 2026-07-18 proxy wall); verify live on Railway.
2. B6 — config-drift flags on the dashboard /env surface: a names-only committed manifest diffed against the live env the dashboard cannot read (Q1=a — names-only). Buildable once the manifest source is chosen.
- Blocked-not-mine: O-021 / ASK-0002 (the Discord OAuth app — REUSE of the SuperBot app recommended, pending owner); R10 (workflow-touch / hub-venue — needs the owner-side hub decision).

kit: v1.17.0
