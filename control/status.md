# websites · status

updated: 2026-07-18T04:30:00Z
phase: backlog build — R6 unit-test the three untested review bake generators (test-only): new network-free, deterministic unit coverage over `review/gen_snapshot.py`, `review/gen_fleet.py`, and `review/gen_stats.py` — each generator's transform + baked-output shape — on branch `claude/review-bake-generator-tests`; a NEXT-TASKS slice of the standing overnight ORDER 032.
health: green — origin/main advanced: C14 self-cleaning owner queue (#386), the orphan-claim cleanup (#387), B1 arcade live/blocked counts on dashboard /status (#388), C1 honest counts on /work /history /console (#389), and A4 arcade JSON schema CI guard (#390) all landed. Last full four-suite run 1792 (2026-07-18, this session — 1763 + 29 new bake-generator tests).
last-shipped: #390 — origin/main head 3cfc349.
orders: acked=001-032 done=001-019,023-031 — unchanged. R6 ships as a backlog slice of the standing overnight ORDER 032, not an order completion.
routine: failsafe cron `trig_01FYyvu2EytWF5NSEzLU2qLD` "Websites failsafe wake" (cron `45 */2 * * *`) bound to the coordinator session; a ~15-min send_later pacemaker chain is kept alive coordinator-side. Old failsafe `trig_01VRT9F6jYNXym3nn18vVQQK` retiring (not re-armed). Tool wall: the capitalized alias `mcp__Claude_Code_Remote__list_triggers` is classifier-blocked; lowercase `mcp__claude-code-remote__list_triggers` works.
blockers: none
landing: pushed-unmerged claude/review-bake-generator-tests — PR #391 READY (R6 unit tests for gen_snapshot/gen_fleet/gen_stats, test-only); merges via server-side auto-merge-enabler on green (agents cannot self-merge, classifier since 2026-07-15). Open PRs: this one.
deployed: 3cfc349 · four Railway services live (control-plane/botsite/dashboard/review). R6 is test-only — no route, template, serialized JSON payload, env, generator, or `review/data/*.json` touched; it adds three unit-test modules to the already-collected review/tests suite (no workflow change).
claims: no active claims (no claim filed — no active contention; committed branch-claims orphan on squash-merge, so the branch-named claim would outlive its branch and red main post-merge — the #387 cleanup class).
notes: WIND-DOWN standing — the Claude Code Projects EAP goes READ-ONLY 2026-07-21; the autonomous apparatus is being retired and the Project recreated (inventory: docs/NEXT-TASKS.md → "Wind-down / retirement"). R6 is a test-only coverage slice, independent of the retirement set.
needs-owner: the 16 ⚑ rows in docs/owner/OWNER-ACTIONS.md (mirror below) — none resolved this session.

## ⚑ OWNER-ACTION mirror (canonical: docs/owner/OWNER-ACTIONS.md) — 16 open, none resolved this session
- ASK-0001 — answer Q-0004: where live bot control lives (or keep /admin dry-run).
- ASK-0002 — create the Discord OAuth app for the future armed panel (after Q-0004).
- ASK-0003 — provision the scoped control-API token + separate armed Railway service (after Q-0004).
- ASK-0004 — create the botsite submissions PostgreSQL + connection string.
- ASK-0005 — set up PayPal Payouts + put its two credentials on the botsite service.
- ASK-0006 — decide the unwired SITE_PASSWORD on the botsite Railway service (wire or remove).
- ASK-0007 — mint the fine-grained contents-write PAT → GITHUB_TOKEN on control-plane + botsite.
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
1. C15 — durable ask IDs (replace positional identity; app/askverify.py, with care re the C14 auto-clear interaction).
2. The next NEXT-TASKS slice.
- Blocked-not-mine: O-020 / O-021 (gated on owner credentials — the ASK-0001..0009 provisioning set); R10 (workflow-touch / hub-venue — needs the owner-side hub decision).
- Standing owner-side: recreate the Project from `main` once the EAP successor is chosen + strip the retired routine/heartbeat/coordinator apparatus (this file included) — EAP goes read-only 2026-07-21.

kit: v1.17.0
