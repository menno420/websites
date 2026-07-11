# substrate-kit upgrade report — v1.11.0 → v1.12.0

> Generated 2026-07-11 by `bootstrap.py upgrade`. Rollback: `python3 bootstrap.py upgrade --rollback`.

**Docs:** consumer-edited: 15 · diverged: 2 · template-improved: 1 · unchanged: 4

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
| docs/ideas/README.md | consumer-edited | template unchanged — consumer-owned, nothing to apply |
| .session-journal.md | consumer-edited | template unchanged — consumer-owned, nothing to apply |
| control/README.md | consumer-edited | template unchanged — consumer-owned, nothing to apply |
| control/inbox.md | consumer-edited | template unchanged — consumer-owned, nothing to apply |
| control/status.md | consumer-edited | template unchanged — consumer-owned, nothing to apply |
| control/claims/README.md | unchanged | template identical across versions |
| scripts/env-setup.sh | consumer-edited | template unchanged — consumer-owned, nothing to apply |
| .claude/CLAUDE.md | template-improved | consumer-untouched + template improved — safe to apply with `upgrade --apply-docs` |

## Carve-out scan

- carve-out scan: ran — no kit-owned live workflow installed, nothing to scan.

## Applied (--apply-docs)

- applied: .claude/CLAUDE.md (template@new, hash re-recorded)

## Template deltas for diverged docs

### CONSTITUTION.md

```diff
--- CONSTITUTION.md (template@old, current slots)
+++ CONSTITUTION.md (template@new, current slots)
@@ -15,20 +15,16 @@
   cross-agent report) against source and the binding docs before acting.
 - **Approved plan = execute.** Once a plan is approved, finish it in the same
   session, with the planning context still loaded — no re-confirming.
-- **Understand-and-reflect.** The owner often hands over a rough fragment, not
-  a full spec — and sometimes doesn't know yet if the idea is even possible.
-  Before substantive work, restate the fuller picture built from the ask —
-  the specs it implied but didn't state, and, when feasibility is uncertain,
-  the possibility space — inline in the first substantive response, never as
-  a separate blocking question. Two payoffs, not one: it catches a misread
-  before work happens, and the filled-in picture is itself new material the
-  owner reasons against and redirects.
-- **Capabilities are discovered, never assumed.** `docs/CAPABILITIES.md` is
-  the verified ledger of what sessions here can and cannot do — read it at
-  session start. Before declaring a wall or a missing credential: check that
-  file → check the environment (`printenv`, tool lists) → attempt once and
-  capture the exact error → append the finding same session. An imagined
-  wall stalls the session; an unrecorded real one taxes every later session.
+- **Understand-and-reflect.** The owner hands over fragments, not full
+  specs. Before substantive work, restate the fuller picture built from the
+  ask — the implied specs, and the possibility space when feasibility is
+  uncertain — inline in the first substantive response, never as a blocking
+  question. It catches a misread early, and the filled-in picture is itself
+  new material the owner redirects.
+- **Capabilities are discovered, never assumed.** Before declaring a wall or
+  a missing credential: check `docs/CAPABILITIES.md` (the verified ledger) →
+  check the environment → attempt once and capture the exact error → append
+  the finding same session.
 - When a doc and a source file disagree: Source code and merged PRs win over any doc. When a doc and a source file disagree, treat the doc as stale, follow the source, and fix the doc in the same session — drift you can see (a wrong ledger entry, a stale pointer) is fixed on sight, not deferred.
 
 ## Autonomy rails — act vs. ask
@@ -40,12 +36,11 @@
   genuinely ambiguous. No live owner to ask? Record the question in
   `docs/question-router.md` instead of skipping it or guessing.
 - **Owner attention is the scarcest resource.** Before routing anything to
-  the owner: attempt it yourself, or cite the exact wall (the
-  `docs/CAPABILITIES.md` discipline) — assumption-based asks are banned.
-  Every ask carries the OWNER-ACTION fields — WHAT / WHERE / HOW /
-  WHY-IT-MATTERS / UNBLOCKS / VERIFIED-NEEDED (format:
-  `control/README.md`) — phrased so a non-technical owner can act on it
-  directly. Expire stale asks; fewer, clearer asks beat complete lists.
+  the owner: attempt it yourself, or cite the exact wall — assumption-based
+  asks are banned. Every ask carries the OWNER-ACTION fields — WHAT / WHERE
+  / HOW / WHY-IT-MATTERS / UNBLOCKS / VERIFIED-NEEDED (format:
+  `control/README.md`) — phrased so a non-technical owner can act directly.
+  Expire stale asks; fewer, clearer asks beat complete lists.
 
 ## Changing the rules — propose, don't apply
 
@@ -60,15 +55,11 @@
 
 Rulings that bind **every** repo in this program live canonically in the
 substrate-kit repo at `docs/program/rulings.md` — the [PL-NNN] register
-(https://github.com/menno420/substrate-kit/blob/main/docs/program/rulings.md):
-PL-001 decide-and-flag · PL-002 never-wait rebuild autonomy · PL-003
-rail-before-scale · PL-004 empirical model allocation · PL-005 observe-first
-budgets · PL-006 source-wins / false-green · PL-007 enforce-don't-exhort ·
-PL-008 adopt-freely with a kill-switch · PL-009 the kit-lab's rails.
-**Cite PL-IDs — never copy ruling bodies into this repo.** The register is
-the one home; a local copy is drift by construction. Repo-local rulings stay
-in `docs/decisions.md` / `docs/question-router.md`; a local ruling promoted
-program-wide becomes a PL-block there and a pointer here.
+(https://github.com/menno420/substrate-kit/blob/main/docs/program/rulings.md),
+e.g. PL-001 decide-and-flag · PL-006 source-wins / false-green.
+**Cite PL-IDs — never copy ruling bodies into this repo** (the register is
+the one home; a local copy is drift by construction). Repo-local rulings
+stay in `docs/decisions.md` / `docs/question-router.md`.
 
 ## Rails specific to websites
 
```

### docs/AGENT_ORIENTATION.md

```diff
--- docs/AGENT_ORIENTATION.md (template@old, current slots)
+++ docs/AGENT_ORIENTATION.md (template@new, current slots)
@@ -7,11 +7,9 @@
 
 ## Start every session
 
-1. `.claude/CLAUDE.md` — the working agreement.
-2. `docs/current-state.md` — the living status ledger.
-3. `docs/CAPABILITIES.md` — verified session capabilities & walls (the
-   discovery rule lives there; append what you learn).
-4. This file — task-specific reading routes.
+The boot set lives in `.claude/CLAUDE.md` § "Orientation — read first" (one
+list, one home). This file is not boot reading — open it when a task needs
+a route into the deeper docs.
 
 ## Binding contracts
 
@@ -33,6 +31,4 @@
 
 ## Verifying any change
 
-```
-python3 -m pytest tests/ -q (app tests); python3 bootstrap.py check --strict (kit gate)
-```
+See `.claude/CLAUDE.md` § "Verifying a change" (one home, never two copies).
```

