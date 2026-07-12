# substrate-kit upgrade report — v1.12.1 → v1.13.0

> Generated 2026-07-12 by `bootstrap.py upgrade`. Rollback: `python3 bootstrap.py upgrade --rollback`.

**Docs:** consumer-edited: 15 · diverged: 2 · template-improved: 1 · unchanged: 5

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
| docs/SKILLS.md | unchanged | template identical across versions |
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
@@ -25,6 +25,9 @@
   a missing credential: check `docs/CAPABILITIES.md` (the verified ledger) →
   check the environment → attempt once and capture the exact error → append
   the finding same session.
+- **Recurring actions run through the skill index.** `docs/SKILLS.md` names
+  every kit-shipped skill and when to reach for it — check it before
+  improvising a procedure or repo-searching "how do we do X here".
 - When a doc and a source file disagree: Source code and merged PRs win over any doc. When a doc and a source file disagree, treat the doc as stale, follow the source, and fix the doc in the same session — drift you can see (a wrong ledger entry, a stale pointer) is fixed on sight, not deferred.
 
 ## Autonomy rails — act vs. ask
```

### docs/AGENT_ORIENTATION.md

```diff
--- docs/AGENT_ORIENTATION.md (template@old, current slots)
+++ docs/AGENT_ORIENTATION.md (template@new, current slots)
@@ -7,9 +7,9 @@
 
 ## Start every session
 
-The boot set lives in `.claude/CLAUDE.md` § "Orientation — read first" (one
-list, one home). This file is not boot reading — open it when a task needs
-a route into the deeper docs.
+The boot set lives in the working agreement — `.claude/CLAUDE.md` — and its
+orientation guidance (one list, one home). This file is not boot reading —
+open it when a task needs a route into the deeper docs.
 
 ## Binding contracts
 
@@ -26,9 +26,15 @@
 `docs/collaboration-model.md` · `docs/helper-policy.md` ·
 `docs/repo-navigation-map.md` · `docs/ai-project-workflow.md` ·
 `docs/owner-profile.md` · `docs/current-state.md` · `docs/decisions.md` ·
-`docs/question-router.md` · `docs/CAPABILITIES.md` · `docs/ideas/README.md` — plus the root
+`docs/question-router.md` · `docs/CAPABILITIES.md` · `docs/SKILLS.md` ·
+`docs/ideas/README.md` — plus the root
 `CONSTITUTION.md` (the working agreement) and `.session-journal.md`.
+
+Recurring action? **`docs/SKILLS.md`** — the skill index — names every
+kit-shipped skill and when to reach for it; check it before improvising a
+procedure.
 
 ## Verifying any change
 
-See `.claude/CLAUDE.md` § "Verifying a change" (one home, never two copies).
+See the working agreement (`.claude/CLAUDE.md`) and its verify guidance
+(one home, never two copies).
```

