# 2026-07-16 — Arcade: launch-blocker panels join asks by ask_id

> **Status:** in-progress

**Goal:** the arcade per-game launch-blocker panels (PR #349) and the owner
console's verification chips (PR #358) tell the same story from the same
facts — but they share NO join key. The only machine join between a blocker
and its ask today is `app/askverify.py`'s two arcade probe entries
(`lumen-drift-release`, `product-forge-pages`), which sit `ask_id=None` and
bind purely by brittle keyword signatures over ask headline text. This slice
switches that join to the ledger's stable `ASK-NNNN` id as the PRIMARY key,
keeping the signature scan as the fallback for id-less rows.

**Scope (matches `control/claims/2026-07-16-arcade-askid-join.md`):**

- `docs/owner/OWNER-ACTIONS.md` — the two arcade owner clicks become real
  ledger rows with stable ids (append-only scheme: next free numbers
  ASK-0010 / ASK-0011); they were previously promises on the public arcade
  page with no ledger row at all.
- `app/askverify.py` — the two arcade REGISTRY entries flip from
  `ask_id=None` (signature-only) to their new exact ids; `match()` already
  prefers exact-ID with signature fallback (PR #358), so the join flips key.
- `botsite/data/arcade.json` + `botsite/arcade.py` — each `blocker` object
  gains an optional, fail-soft `ask_id` referencing its ledger row; the
  detail page renders the ledger ref. Both surfaces now flip from one
  ledger edit.
- Tests: botsite suite (schema + panel), tests/ suite (ID-primary join even
  when the old brittle key would mismatch; ID-less signature fallback;
  committed arcade.json ↔ ledger ↔ registry consistency pin).

**Plan:** ledger rows first (ids minted), registry ids second, arcade
schema + template third, tests alongside each; full four-suite verify +
`bootstrap.py check --strict` before every push; heartbeat overwrite
(coordinator-delegated) on this branch; card flips complete last.

⚑ Self-initiated: no — coordinator-dispatched slice promoted from the
NEXT-2-TASKS baton (`.sessions/2026-07-15-arcade-detail.md` idea, promoted
by `control/status.md` at a0a6e66).

## Close-out (auto-drafted 2026-07-16 — edit, don't author)

<!-- substrate:auto-draft -->

**Evidence (auto-collected — verify, then keep or correct):**

- code touched (69): `app/activity.py`, `app/askverify.py`, `app/briefing.py`, `app/config.py`, `app/envdrift.py`, `app/envhub.py`, `app/environments.py`, `app/fleet.py`, `app/freshness.py`, `app/github.py`, `app/ideas.py`, `app/journal.py`, `app/listfilter.py`, `app/main.py`, `app/nav.py` (+54 more)
- docs touched (26): `docs/AGENT_ORIENTATION.md`, `docs/CAPABILITIES.md`, `docs/RAILWAY-SAFETY.md`, `docs/ROUTINES.md`, `docs/SKILLS.md`, `docs/ai-project-workflow.md`, `docs/architecture.md`, `docs/audits/2026-07-13-fleet-cleanup-audit.md`, `docs/audits/README.md`, `docs/audits/eap-project-audit-2026-07-14.md`, `docs/botsite.md`, `docs/collaboration-model.md`, `docs/current-state.md`, `docs/dashboard.md`, `docs/eap-closeout-walkthrough-2026-07-14.md` (+11 more)
- other touched (105): `.claude/CLAUDE.md`, `.github/workflows/auto-merge-enabler.yml`, `.github/workflows/host-automerge-extras.yml`, `.github/workflows/quality.yml`, `.github/workflows/review-bake.yml`, `.github/workflows/smoke-crawl.yml`, `.gitignore`, `.session-journal.md`, `HANDOFF.md`, `app/data/environments.json`, `app/data/web_presence.json`, `app/static/favicon.svg`, `app/templates/_listfilter.html`, `app/templates/_prompt_artifact.html`, `app/templates/activity.html` (+90 more)
- sessions touched (204): `.sessions/2026-07-09-activity-atom-feed.md`, `.sessions/2026-07-09-activity-ideas-views.md`, `.sessions/2026-07-09-adopt-substrate-kit.md`, `.sessions/2026-07-09-botsite-content-depth.md`, `.sessions/2026-07-09-console-feed-contract.md`, `.sessions/2026-07-09-control-plane-site.md`, `.sessions/2026-07-09-dashboard-autodeploy-fix.md`, `.sessions/2026-07-09-dashboard-botsite-rework-plan.md`, `.sessions/2026-07-09-dashboard-stub-denylist.md`, `.sessions/2026-07-09-drop-auth.md`, `.sessions/2026-07-09-engage-kit.md`, `.sessions/2026-07-09-fix-born-red-gate.md`, `.sessions/2026-07-09-fleet-retro-order.md`, `.sessions/2026-07-09-harden-verify.md`, `.sessions/2026-07-09-journal-search-mobile.md` (+189 more)
- tests touched (92): `botsite/tests/test_agent_pr_check.py`, `botsite/tests/test_arcade.py`, `botsite/tests/test_arcade_probe.py`, `botsite/tests/test_botsite.py`, `botsite/tests/test_botsite_filters.py`, `botsite/tests/test_catalog.py`, `botsite/tests/test_clarity_structure.py`, `botsite/tests/test_env_parse_hardening.py`, `botsite/tests/test_field_manual.py`, `botsite/tests/test_graveyard.py`, `botsite/tests/test_import_roundtrip.py`, `botsite/tests/test_import_schema_drift.py`, `botsite/tests/test_products.py`, `botsite/tests/test_puddle_museum.py`, `botsite/tests/test_rubric.py` (+77 more)
- git: branch `claude/arcade-askid-join`, HEAD 5381fdba1 → d8ac52514 (commits made this session).
- commits this session (2): "rescue: uncommitted .substrate/state.json from prior session" · "session: open born-red card + claim for arcade-askid-join"
- verify: run `python3 -m pytest tests/ botsite/tests dashboard/tests review/tests -q (all four service suites); python3 bootstrap.py check --strict (kit gate)` and record the result → [[fill: verify result — the engine cannot execute commands]]

**Judgment (the half only the session knows — resolve every slot):**

- Decisions made: [[fill: decisions taken this session, or none]]
- Next session should know: [[fill: the handoff pointer — where to pick up]]

## 💡 Session idea

[[fill: one idea you genuinely believe in — never filler]]

## ⟲ Previous-session review

[[fill: one genuine remark on the previous session + one workflow improvement]]

- **📊 Model:** [[fill: model · effort · task-class (Q-0248 taxonomy)]]
