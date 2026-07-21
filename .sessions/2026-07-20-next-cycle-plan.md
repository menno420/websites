# Session card — 2026-07-20 · product-frontier plan

> **Status:** `complete`

## Goal
Produce the 2026-07-20 product-frontier cycle plan and land it; queue the review edition auto-drafter as the top slice.

## What landed
- docs/plans/next-cycle-2026-07-20.md — 6 ranked executable slices + routed-out section.
- control/status.md baton refreshed: NEXT top = S1 edition auto-drafter.

## Evidence
- Product mining across arcade / review editions / owner console / botsite submissions / cross-site nav.
- Standout find: review editions are hand-authored, only edition-001 (2026-07-11) exists; review-bake.yml generates data mirrors but no editions — the "continuous review channel" is unbuilt, not owner-gated.

## Verify
- env -u DATABASE_URL python3 -m pytest tests/ botsite/tests dashboard/tests review/tests -q
- env -u DATABASE_URL python3 bootstrap.py check --strict

## Close-out (auto-drafted 2026-07-21 — edit, don't author)

<!-- substrate:auto-draft -->

**Evidence (auto-collected — verify, then keep or correct):**

- code touched (102): `app/__init__.py`, `app/activity.py`, `app/askverify.py`, `app/briefing.py`, `app/card_gating.py`, `app/clock.py`, `app/codedrift.py`, `app/config.py`, `app/discord_auth.py`, `app/envdrift.py`, `app/envhub.py`, `app/environments.py`, `app/fleet.py`, `app/freshness.py`, `app/gen_env_coderefs.py` (+87 more)
- docs touched (65): `docs/AGENT_ORIENTATION.md`, `docs/CAPABILITIES.md`, `docs/NEXT-TASKS.md`, `docs/OWNER-STEPS.md`, `docs/RAILWAY-SAFETY.md`, `docs/ROUTINES.md`, `docs/SKILLS.md`, `docs/ai-project-workflow.md`, `docs/architecture.md`, `docs/audits/2026-07-13-fleet-cleanup-audit.md`, `docs/audits/README.md`, `docs/audits/eap-project-audit-2026-07-14.md`, `docs/botsite.md`, `docs/collaboration-model.md`, `docs/current-state.md` (+50 more)
- other touched (189): `.claude/CLAUDE.md`, `.claude/settings.json`, `.gitattributes`, `.github/workflows/auto-merge-enabler.yml`, `.github/workflows/healthcheck.yml`, `.github/workflows/host-automerge-extras.yml`, `.github/workflows/quality-main-sweep.yml`, `.github/workflows/quality.yml`, `.github/workflows/review-bake.yml`, `.github/workflows/smoke-crawl.yml`, `.gitignore`, `.ignore`, `.session-journal.md`, `CONSTITUTION.md`, `Dockerfile` (+174 more)
- sessions touched (282): `.sessions/2026-07-09-activity-atom-feed.md`, `.sessions/2026-07-09-activity-ideas-views.md`, `.sessions/2026-07-09-adopt-substrate-kit.md`, `.sessions/2026-07-09-botsite-content-depth.md`, `.sessions/2026-07-09-console-feed-contract.md`, `.sessions/2026-07-09-control-plane-site.md`, `.sessions/2026-07-09-dashboard-autodeploy-fix.md`, `.sessions/2026-07-09-dashboard-botsite-rework-plan.md`, `.sessions/2026-07-09-dashboard-stub-denylist.md`, `.sessions/2026-07-09-drop-auth.md`, `.sessions/2026-07-09-engage-kit.md`, `.sessions/2026-07-09-fix-born-red-gate.md`, `.sessions/2026-07-09-fleet-manifest-live.md`, `.sessions/2026-07-09-fleet-retro-order.md`, `.sessions/2026-07-09-harden-verify.md` (+267 more)
- tests touched (150): `botsite/tests/__init__.py`, `botsite/tests/test_agent_pr_check.py`, `botsite/tests/test_arcade.py`, `botsite/tests/test_arcade_probe.py`, `botsite/tests/test_arcade_registry_integrity.py`, `botsite/tests/test_botsite.py`, `botsite/tests/test_botsite_filters.py`, `botsite/tests/test_catalog.py`, `botsite/tests/test_clarity_structure.py`, `botsite/tests/test_discord_auth.py`, `botsite/tests/test_env_parse_hardening.py`, `botsite/tests/test_field_manual.py`, `botsite/tests/test_graveyard.py`, `botsite/tests/test_import_roundtrip.py`, `botsite/tests/test_import_schema_drift.py` (+135 more)
- git: branch `claude/next-cycle-2026-07-20-plan`, HEAD 5381fdba1 → 7b68bb042 (commits made this session).
- commits this session (1): "plan: born-red card + claim for 2026-07-20 product-frontier cycle"
- verify: run `python3 -m pytest tests/ botsite/tests dashboard/tests review/tests -q (all four service suites); python3 bootstrap.py check --strict (kit gate)` and record the result → four-suite pytest 2132 passed; bootstrap check --strict clean apart from the born-red card HOLD (by design, released by this flip commit).

**Judgment (the half only the session knows — resolve every slot):**

- Decisions made: badged the plan doc `plan` (not the author's `planned` — that token is rejected by the strict badge gate) and linked it as the "Current groomed queue" from docs/NEXT-TASKS.md to clear the reachability/orphan finding. Baton kept the owner-gated Discord item, demoted to #2 under S1.
- Next session should know: execute S1 — write `review/gen_edition.py` to draft the next edition from the committed baked mirrors (stats/fleet/releases/snapshot json) per the editions.py reproducible-from-source doctrine; the review-bake.yml wiring is the routed-out hub follow-on. Queue after: S2 arcade catalog growth, S3 cross-service nav strip.

## 💡 Session idea

The strict badge gate rejected `planned` on a plan doc even though it lives in docs/plans/ — the allowed set is generic (plan/reference/binding/…). Plan docs would be self-documenting if gen_* stamped a canonical `plan` badge and the planner scaffolder emitted it, so authors never hand-type an invalid token. Small guard: a per-directory badge-allowlist so docs/plans/** must badge `plan`.

## ⟲ Previous-session review

The 2026-07-19 pass drained the seat-buildable hardening queue cleanly (through #460/#461, strict gate clean, 2132 green), which is exactly what let this cycle pivot to the product frontier without leftover hygiene debt. Workflow improvement: the born-red "EXACTLY this content" plan-doc handoff shipped an invalid badge token — coordinator-supplied doc bodies should be pre-validated against the strict badge/reachability gates so the worker isn't forced to deviate mid-flight.

- **📊 Model:** Opus 4.8 (1M) · medium · idea/planning
