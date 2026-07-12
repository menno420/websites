# substrate-kit upgrade report — v1.14.0 → v1.15.0

> Generated 2026-07-12 by `bootstrap.py upgrade`. Rollback: `python3 bootstrap.py upgrade --rollback`.

**Docs:** consumer-edited: 13 · diverged: 5 · template-improved: 1 · unchanged: 5

| planted doc | class | note |
|---|---|---|
| CONSTITUTION.md | diverged | both the template and the doc moved — manual merge |
| docs/decisions.md | consumer-edited | template unchanged — consumer-owned, nothing to apply |
| docs/architecture.md | consumer-edited | template unchanged — consumer-owned, nothing to apply |
| docs/ownership.md | consumer-edited | template unchanged — consumer-owned, nothing to apply |
| docs/runtime_contracts.md | consumer-edited | template unchanged — consumer-owned, nothing to apply |
| docs/repo-navigation-map.md | consumer-edited | template unchanged — consumer-owned, nothing to apply |
| docs/helper-policy.md | unchanged | template identical across versions |
| docs/collaboration-model.md | consumer-edited | template unchanged — consumer-owned, nothing to apply |
| docs/ai-project-workflow.md | unchanged | template identical across versions |
| docs/owner-profile.md | unchanged | template identical across versions |
| docs/AGENT_ORIENTATION.md | diverged | both the template and the doc moved — manual merge |
| docs/current-state.md | consumer-edited | template unchanged — consumer-owned, nothing to apply |
| docs/question-router.md | consumer-edited | template unchanged — consumer-owned, nothing to apply |
| docs/CAPABILITIES.md | consumer-edited | template unchanged — consumer-owned, nothing to apply |
| docs/SKILLS.md | template-improved | consumer-untouched + template improved — safe to apply with `upgrade --apply-docs` |
| docs/ROUTINES.md | unchanged | template identical across versions |
| docs/ideas/README.md | consumer-edited | template unchanged — consumer-owned, nothing to apply |
| .session-journal.md | consumer-edited | template unchanged — consumer-owned, nothing to apply |
| control/README.md | diverged | both the template and the doc moved — manual merge |
| control/inbox.md | consumer-edited | template unchanged — consumer-owned, nothing to apply |
| control/status.md | diverged | both the template and the doc moved — manual merge |
| control/claims/README.md | unchanged | template identical across versions |
| scripts/env-setup.sh | consumer-edited | template unchanged — consumer-owned, nothing to apply |
| .claude/CLAUDE.md | diverged | both the template and the doc moved — manual merge |

## ⚠️ Gate carve-outs (host additions the kit-owned regen could not keep)

- carve-out: .github/workflows/auto-merge-enabler.yml — host-added job 'arm-on-open' (Arm native squash auto-merge (skip workflow-touching PRs)) [carried from the previous upgrade report]
- carve-out: .github/workflows/auto-merge-enabler.yml — host-added job 'sweep' (Arm auto-merge on every open eligible claude/* PR) [carried from the previous upgrade report]
- carve-out: full pre-regen enabler banked at .substrate/backup/auto-merge-enabler.pre-regen-c43c1c30.yml — host additions were NOT carried into the regenerated kit-owned enabler; move them into a separate workflow file (e.g. .github/workflows/host-ci.yml) and commit that before shipping this upgrade/adopt PR. [carried from the previous upgrade report]

## Carve-out scan

- carve-out scan: .github/workflows/auto-merge-enabler.yml — ran, 0 found
- carve-out scan: 3 carve-out line(s) reported above (see the ⚠️ section).

## Capability-ledger seed refresh

- capability-seed: docs/CAPABILITIES.md carries no kit-owned seed fence and its seed section does not match the old template — hand-adopt once: replace your discovery-rule + Capabilities/Walls seed sections with the fenced block (BEGIN/END markers) from the new template, keeping your append log below it; afterwards upgrades refresh the fence automatically.

This upgrade ships the venue-scoped capability ledger (grounded-skills §4.2): entries carry a venue token (owner-live · autonomous-project · routine-fired · subagent · any) and the ledger's kit-owned seed block carries the posture decision rule. If this repo carries a local prose copy of the boot-triad/venue-posture rule (superbot Q-0270), that copy is now superseded by docs/CAPABILITIES.md's posture rule — collapse the local copy into a pointer.

## Seat-digest refresh

- seat-digest: docs/seat-digest.md already current — nothing to refresh.

## Applied (--apply-docs)

- applied: docs/SKILLS.md (template@new, hash re-recorded)

## Template deltas for diverged docs

### CONSTITUTION.md

```diff
--- CONSTITUTION.md (template@old, current slots)
+++ CONSTITUTION.md (template@new, current slots)
@@ -28,6 +28,30 @@
 - **Recurring actions run through the skill index.** `docs/SKILLS.md` names
   every kit-shipped skill and when to reach for it — check it before
   improvising a procedure or repo-searching "how do we do X here".
+- **Skills self-propagate — the registration reflex.** A recurring action
+  with no skill — or a skill whose body doesn't actually cover it — is a
+  gap to register, not to route around: the standard move is to **add or
+  extend the skill** — a registry entry, not ad-hoc prose — via the growth
+  loop prose workflow → index row → promoted skill (`docs/SKILLS.md`
+  § "Growing the set"). The boundary: skill bodies, grounds, and index rows
+  are free to ship directly, flagged self-initiated on the run report;
+  **binding working-agreement text and executable config** (this file,
+  `CLAUDE.md`-level rules, hooks, settings) route through
+  `docs/question-router.md` as a proposal — never self-applied — unless the
+  owner directs the change live in-session, recorded with its provenance id
+  ("Changing the rules" below; superbot Q-0194 · Q-0106 · Q-0172).
+- **Evidence — verify, don't trust.** A record is a claim; the live surface
+  is the proof — probe the registry/API/tree before acting on any recorded
+  state (probe-not-record). The committed **tree wins over a self-report**:
+  heartbeat/registry `kit:` lines chronically lag the target repo's tree by
+  1–3 releases — verify against the tree. A red or green **check is judged
+  by its job log, never its name** (alias/mirror jobs red without measuring
+  anything; a designed hold is not a failure). Staleness-sensitive reads are
+  **cross-checked before acting** (MCP PR-state reads observed ~25 min
+  stale — confirm merge/CI state via git fetch or the Actions runs). A green
+  check that contradicts visible evidence is **a bug in the CHECK, not a
+  clearance** (PL-006). Every load-bearing claim cites a commit / PR / tag /
+  run.
 - When a doc and a source file disagree: Source code and merged PRs win over any doc. When a doc and a source file disagree, treat the doc as stale, follow the source, and fix the doc in the same session — drift you can see (a wrong ledger entry, a stale pointer) is fixed on sight, not deferred.
 
 ## Autonomy rails — act vs. ask
```

### docs/AGENT_ORIENTATION.md

```diff
--- docs/AGENT_ORIENTATION.md (template@old, current slots)
+++ docs/AGENT_ORIENTATION.md (template@new, current slots)
@@ -6,6 +6,21 @@
 > docs a given task needs. **NOT SOURCE OF TRUTH** — the binding contracts win.
 
 ## Start every session
+
+**Preflight first — land on origin's HEAD before reading anything else:**
+
+```
+git fetch origin main && git reset --hard origin/main
+```
+
+(or `git checkout -B main origin/main`; substitute your default branch).
+Then verify: local HEAD (`git rev-parse HEAD`) must equal
+`git ls-remote origin main`. A warm container clone can lag origin by
+dozens of commits, and a stale clone reads stale orders and stale state —
+every orientation read below assumes this step already ran. The hard reset
+discards uncommitted local changes by design: at session START there should
+be none; if `git status` shows work you did not author, stop and report it
+instead of resetting over it.
 
 The boot set lives in the working agreement — `.claude/CLAUDE.md` — and its
 orientation guidance (one list, one home). This file is not boot reading —
@@ -27,13 +42,18 @@
 `docs/repo-navigation-map.md` · `docs/ai-project-workflow.md` ·
 `docs/owner-profile.md` · `docs/current-state.md` · `docs/decisions.md` ·
 `docs/question-router.md` · `docs/CAPABILITIES.md` · `docs/SKILLS.md` ·
-`docs/ideas/README.md` — plus the root
+`docs/ROUTINES.md` · `docs/ideas/README.md` — plus the root
 `CONSTITUTION.md` (the working agreement) and `.session-journal.md`.
 
 Recurring action? **`docs/SKILLS.md`** — the skill index — names every
 kit-shipped skill and when to reach for it; check it before improvising a
 procedure.
 
+Arming, deleting, or auditing a scheduled trigger/routine/wake chain?
+**`docs/ROUTINES.md`** — binding choice, delivery verification,
+probe-not-record, scheduler-health signatures, pacing — read it before
+touching the trigger registry.
+
 ## Verifying any change
 
 See the working agreement (`.claude/CLAUDE.md`) and its verify guidance
```

### control/README.md

```diff
--- control/README.md (template@old, current slots)
+++ control/README.md (template@new, current slots)
@@ -131,6 +131,27 @@
 the latest `check --strict` verdict on this tree; `engaged:` = the post-adopt engagement gate
 (`yes` once no UNRENDERED banner/slot remains, live CI runs the gate, and the session loop
 has engaged).
+
+**Exact grammar or invisible — keep the `kit:` token PLAIN.** The parser accepts a bold label
+*before* a plain token (`- **kit heartbeat:** kit: v1.2.3 · check: green · engaged: yes` is a
+live valid shape), but bolding the token itself does NOT parse — the fleet registry then reads
+the row as "no `kit:` line" and the lane's engaged signal silently vanishes (a live adopter
+incident, not a hypothetical). The taught negative example:
+
+```markdown
+- **kit:** v1.2.3 · check: green · engaged: yes
+```
+
+← does NOT parse (`KIT_LINE_RE`, kit `src/engine/grammar.py` — the optional bold group cannot
+contain the `kit:` token). If your heartbeat wants a bold label, put it *before* a plain
+`kit:` token.
+
+**Version truth defers to the generated registry, never to this line.** Heartbeat `kit:`
+lines are self-reports and chronically lag 1–3 releases behind the tree (the fleet's
+recurring self-report DRIFT class); the kit repo's generated `docs/adopters.md` —
+regenerated from each adopter's committed tree — is the fleet's version truth, and your own
+committed tree (the vendored dist) is yours. Never hand-assert a fleet version spread from
+heartbeat lines; keep this line in sync as a courtesy signal, not as proof.
 
 ## ⚑ needs-owner — the OWNER-ACTION item format (quality contract)
 
```

### control/status.md

```diff
--- control/status.md (template@old, current slots)
+++ control/status.md (template@new, current slots)
@@ -13,3 +13,8 @@
 The `kit:` line is your kit self-report (substrate-coordinator visibility): keep the version in
 sync with your vendored kit on every upgrade, `check:` = your last `check --strict` verdict,
 `engaged:` = the post-adopt engagement gate (yes once `check` reports ENGAGED/green live CI).
+Keep the `kit:` token PLAIN — the bold-label form `- **kit:** v1.2.3 · check: green · engaged: yes`
+does NOT parse and the fleet registry reads it as no `kit:` line at all (grammar + the valid
+bold-label-before-plain-token shape: `control/README.md` § "status.md format"). And this line is
+a self-report, not version truth — self-reports chronically lag; the kit repo's generated
+`docs/adopters.md` and your committed tree are the version truth to defer to.
```

### .claude/CLAUDE.md

```diff
--- .claude/CLAUDE.md (template@old, current slots)
+++ .claude/CLAUDE.md (template@new, current slots)
@@ -12,6 +12,12 @@
 
 ## Orientation — read first, in order
 
+0. **Preflight — land on origin's HEAD before reading anything else:**
+   `git fetch origin main && git reset --hard origin/main` (or
+   `git checkout -B main origin/main`). A warm container clone can lag
+   origin by dozens of commits, and a stale clone reads stale orders.
+   Mechanics + safety notes: `docs/AGENT_ORIENTATION.md` § "Start every
+   session".
 1. This file — the working agreement.
 2. `HANDOFF.md` at repo root (when present) — the previous session's trail:
    newest session card + where to pick up. Regenerated at every session
@@ -27,7 +33,8 @@
 `docs/CAPABILITIES.md` (the verified can/cannot ledger) **before declaring
 any wall or missing credential** — its discovery rule: check the file →
 check the env → attempt once + capture the exact error → append the finding
-same session.
+same session — and `docs/ROUTINES.md` (the wake-chain/trigger doctrine)
+**before arming, deleting, or auditing any scheduled trigger/routine**.
 
 ## Kit machinery — search hygiene
 
```

