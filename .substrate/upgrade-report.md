# substrate-kit upgrade report — v1.15.0 → v1.16.0

> Generated 2026-07-14 by `bootstrap.py upgrade`. Rollback: `python3 bootstrap.py upgrade --rollback`.

**Docs:** consumer-edited: 14 · diverged: 4 · template-improved: 3 · unchanged: 4

| planted doc | class | note |
|---|---|---|
| CONSTITUTION.md | diverged | both the template and the doc moved — manual merge |
| docs/decisions.md | consumer-edited | template unchanged — consumer-owned, nothing to apply |
| docs/architecture.md | consumer-edited | template unchanged — consumer-owned, nothing to apply |
| docs/ownership.md | consumer-edited | template unchanged — consumer-owned, nothing to apply |
| docs/runtime_contracts.md | consumer-edited | template unchanged — consumer-owned, nothing to apply |
| docs/repo-navigation-map.md | consumer-edited | template unchanged — consumer-owned, nothing to apply |
| docs/helper-policy.md | unchanged | template identical across versions |
| docs/collaboration-model.md | diverged | both the template and the doc moved — manual merge |
| docs/ai-project-workflow.md | unchanged | template identical across versions |
| docs/owner-profile.md | unchanged | template identical across versions |
| docs/AGENT_ORIENTATION.md | diverged | both the template and the doc moved — manual merge |
| docs/current-state.md | consumer-edited | template unchanged — consumer-owned, nothing to apply |
| docs/question-router.md | consumer-edited | template unchanged — consumer-owned, nothing to apply |
| docs/CAPABILITIES.md | diverged | both the template and the doc moved — manual merge |
| docs/SKILLS.md | template-improved | consumer-untouched + template improved — safe to apply with `upgrade --apply-docs` |
| docs/ROUTINES.md | template-improved | consumer-untouched + template improved — safe to apply with `upgrade --apply-docs` |
| docs/reading-path.md | unchanged | template identical across versions |
| docs/ideas/README.md | consumer-edited | template unchanged — consumer-owned, nothing to apply |
| .session-journal.md | consumer-edited | template unchanged — consumer-owned, nothing to apply |
| control/README.md | consumer-edited | template unchanged — consumer-owned, nothing to apply |
| control/inbox.md | consumer-edited | template unchanged — consumer-owned, nothing to apply |
| control/status.md | consumer-edited | template unchanged — consumer-owned, nothing to apply |
| control/claims/README.md | template-improved | consumer-untouched + template improved — safe to apply with `upgrade --apply-docs` |
| scripts/env-setup.sh | consumer-edited | template unchanged — consumer-owned, nothing to apply |
| .claude/CLAUDE.md | consumer-edited | template unchanged — consumer-owned, nothing to apply |

## Carve-out scan

- carve-out scan: .github/workflows/auto-merge-enabler.yml — ran, 0 found

## Capability-ledger seed refresh

- capability-seed: NOT refreshed — the fenced seed block in docs/CAPABILITIES.md differs from the kit-form fence (edited inside the fence, or the old templates are unavailable). The fence is kit-owned: move your own findings BELOW the fence into the append log, restore the block between the BEGIN/END markers to kit form (copy it from the new template render), and the next upgrade refreshes it automatically.

This upgrade ships the venue-scoped capability ledger (grounded-skills §4.2): entries carry a venue token (owner-live · autonomous-project · routine-fired · subagent · any) and the ledger's kit-owned seed block carries the posture decision rule. If this repo carries a local prose copy of the boot-triad/venue-posture rule (superbot Q-0270), that copy is now superseded by docs/CAPABILITIES.md's posture rule — collapse the local copy into a pointer.

## Seat-digest refresh

- seat-digest: NOT regenerated — docs/seat-digest.md differs from the last kit-written render (hand-edited, or no hash recorded). It is a derived render, never a copy of record: move any real finding into the capability ledger / skill index, then regenerate with `python3 bootstrap.py seat-digest` (overwrites this file only; the sources are untouched).

## Applied (--apply-docs)

- applied: docs/SKILLS.md (template@new, hash re-recorded)
- applied: docs/ROUTINES.md (template@new, hash re-recorded)
- applied: control/claims/README.md (template@new, hash re-recorded)

## Template deltas for diverged docs

### CONSTITUTION.md

```diff
--- CONSTITUTION.md (template@old, current slots)
+++ CONSTITUTION.md (template@new, current slots)
@@ -40,6 +40,12 @@
   `docs/question-router.md` as a proposal — never self-applied — unless the
   owner directs the change live in-session, recorded with its provenance id
   ("Changing the rules" below; superbot Q-0194 · Q-0106 · Q-0172).
+  The reflex generalizes beyond incidents to **opportunities** — the
+  rationalization checkpoint: at natural pauses (a slice lands · a
+  lesson/workaround surfaces · session enders) ask *"should this action
+  also be executed?"* and *"does this lesson deserve a permanent home —
+  skill / checker / template / idea — I can ship NOW?"* Method + routing
+  table: the `rationalize` skill (Q-0273).
 - **Evidence — verify, don't trust.** A record is a claim; the live surface
   is the proof — probe the registry/API/tree before acting on any recorded
   state (probe-not-record). The committed **tree wins over a self-report**:
@@ -56,12 +62,46 @@
 
 ## Autonomy rails — act vs. ask
 
+The full twelve-item autonomy rider is PL-012 (cite it, don't copy it);
+these rails are its adopter-side operating form:
+
 - **Act** on contained, reversible, verifiable changes — including a
-  root-cause fix discovered mid-task.
-- **Ask** before anything irreversible (data loss, external publish),
-  large / cross-cutting (architectural), or when the goal itself is
-  genuinely ambiguous. No live owner to ask? Record the question in
-  `docs/question-router.md` instead of skipping it or guessing.
+  root-cause fix discovered mid-task. Every reversible design / technical
+  / planning call — architectural included — is **decided-and-flagged**:
+  decide it, one-line rationale, flag it on the run report; route to the
+  owner only genuine product-intent forks (PL-001 · PL-012).
+- **Owner absent = normal; silence = consent.** Unattended execution is
+  the design: "wait for the owner to review / approve / confirm" is a
+  hallucinated gate unless it names an owner-only class below — proceed.
+  Ship on green CI; unremarked work is accepted — owner control is
+  reaction after visibility, never pre-approval (PL-012).
+- **An open PR is never a reason to stop.** Open READY (never draft) →
+  arm auto-merge while checks pend → it lands itself; blocked branch →
+  update it (merge, never force) and re-arm; a real, verbatim
+  arming/merge denial → park the PR ready, queue ONE owner item for the
+  systemic cause, take the next slice the same turn (PL-012).
+- **Ask first only for the owner-only classes:** repo settings / rulesets
+  / required checks · secrets / env vars / host provisioning · external
+  publish + spending money · destructive prod-data ops · account/portal
+  steps — or a goal that is genuinely product-ambiguous.
+  **Queue-and-continue:** the ask goes to the owner queue your program
+  uses (no live owner? record it in `docs/question-router.md`) and you
+  keep working — never end a turn "waiting". A wall is declared only per
+  the capabilities discovery rule above — attempt once, verbatim error;
+  one refusal ≠ a permanent wall (PL-012).
+- **Never idle on a drained queue.** Work ladder: standing orders → the
+  session's stated targets → the backlog / roadmap docs → the generative
+  rung (orientation, guards, ideas — substrate work is first-class).
+  Uncertainty unsettleable from source in ~15 minutes is **routed, not
+  blocking**: post it where your program routes questions and keep
+  building (PL-012).
+- **Volatile facts expire.** Any PR# / SHA / "X is blocked / missing" in
+  a prompt or brief was true when written — re-verify at HEAD before
+  acting; the committed tree wins, and a stale "blocked" is not a reason
+  to skip (PL-006 · PL-012).
+- **The quality floor is unchanged.** Never-wait ≠ bypass CI: merging
+  requires green. Honest nulls and honest failures are deliverables; a
+  faked green or a papered-over stall is the only true failure (PL-012).
 - **Owner attention is the scarcest resource.** Before routing anything to
   the owner: attempt it yourself, or cite the exact wall — assumption-based
   asks are banned. Every ask carries the OWNER-ACTION fields — WHAT / WHERE
@@ -87,7 +127,8 @@
 Rulings that bind **every** repo in this program live canonically in the
 substrate-kit repo at `docs/program/rulings.md` — the [PL-NNN] register
 (https://github.com/menno420/substrate-kit/blob/main/docs/program/rulings.md),
-e.g. PL-001 decide-and-flag · PL-006 source-wins / false-green.
+e.g. PL-001 decide-and-flag · PL-006 source-wins / false-green ·
+PL-012 the autonomy rider.
 **Cite PL-IDs — never copy ruling bodies into this repo** (the register is
 the one home; a local copy is drift by construction). Repo-local rulings
 stay in `docs/decisions.md` / `docs/question-router.md`.
```

### docs/collaboration-model.md

```diff
--- docs/collaboration-model.md (template@old, current slots)
+++ docs/collaboration-model.md (template@new, current slots)
@@ -52,7 +52,8 @@
 Anything that interrupts a session's workflow — a stale file, a checker that
 lied, a footgun — is converted into the **cheapest enforcing prevention**
 before the session ends: checker / CI / test first, then hook, then written
-rule. Enforce, don't exhort.
+rule. Enforce, don't exhort. The same reflex runs on opportunities, not only
+interruptions — the rationalization checkpoint (`rationalize` skill, Q-0273).
 
 ## Guiding questions
 
@@ -68,7 +69,7 @@
 This model's program-wide form, and the rulings that bind every repo in the
 program, live canonically in the substrate-kit repo at
 `docs/program/rulings.md` (the [PL-NNN] register — e.g. PL-001
-decide-and-flag, PL-002 never-wait, PL-007 enforce-don't-exhort) and
+decide-and-flag, PL-007 enforce-don't-exhort, PL-012 the autonomy rider) and
 `docs/program/collaboration-model.md`
 (https://github.com/menno420/substrate-kit/tree/main/docs/program).
 **Cite PL-IDs — never copy ruling bodies into this repo.**
```

### docs/AGENT_ORIENTATION.md

```diff
--- docs/AGENT_ORIENTATION.md (template@old, current slots)
+++ docs/AGENT_ORIENTATION.md (template@new, current slots)
@@ -42,8 +42,9 @@
 `docs/repo-navigation-map.md` · `docs/ai-project-workflow.md` ·
 `docs/owner-profile.md` · `docs/current-state.md` · `docs/decisions.md` ·
 `docs/question-router.md` · `docs/CAPABILITIES.md` · `docs/SKILLS.md` ·
-`docs/ROUTINES.md` · `docs/ideas/README.md` — plus the root
-`CONSTITUTION.md` (the working agreement) and `.session-journal.md`.
+`docs/ROUTINES.md` · `docs/reading-path.md` · `docs/ideas/README.md` —
+plus the root `CONSTITUTION.md` (the working agreement) and
+`.session-journal.md`.
 
 Recurring action? **`docs/SKILLS.md`** — the skill index — names every
 kit-shipped skill and when to reach for it; check it before improvising a
@@ -54,6 +55,11 @@
 probe-not-record, scheduler-health signatures, pacing — read it before
 touching the trigger registry.
 
+Reading or acting across sibling repos in a fleet? **`docs/reading-path.md`**
+— the standing read authorization, the one-command fleet orient, the
+sibling/truth-file map, tiered depth, truth rules — read it before burning
+turns re-discovering what you may read.
+
 ## Verifying any change
 
 See the working agreement (`.claude/CLAUDE.md`) and its verify guidance
```

### docs/CAPABILITIES.md

```diff
--- docs/CAPABILITIES.md (template@old, current slots)
+++ docs/CAPABILITIES.md (template@new, current slots)
@@ -5,7 +5,7 @@
 > Generated by substrate-kit. What agent sessions in THIS environment can and
 > cannot do — **verified findings, never assumptions**. Read at session start
 > (it is in the orientation reading order); append at session close. Fleet
-> master copy: `menno420/fleet-manager` → `docs/capabilities.md` — sync new
+> master copy: `menno420/fleet-manager` → `docs/CAPABILITIES.md` — sync new
 > fleet-wide findings there via the manager when cross-repo access allows.
 
 ## Why this file exists
```

