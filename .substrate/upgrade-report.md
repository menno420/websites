# substrate-kit upgrade report — v1.2.0 → v1.6.0

> Generated 2026-07-09 by `bootstrap.py upgrade`. Rollback: `python3 bootstrap.py upgrade --rollback`.

**Docs:** consumer-edited: 13 · diverged: 5 · missing: 1 · template-improved: 1

| planted doc | class | note |
|---|---|---|
| CONSTITUTION.md | diverged | both the template and the doc moved — manual merge |
| docs/decisions.md | consumer-edited | template unchanged — consumer-owned, nothing to apply |
| docs/architecture.md | consumer-edited | template unchanged — consumer-owned, nothing to apply |
| docs/ownership.md | consumer-edited | template unchanged — consumer-owned, nothing to apply |
| docs/runtime_contracts.md | consumer-edited | template unchanged — consumer-owned, nothing to apply |
| docs/repo-navigation-map.md | consumer-edited | template unchanged — consumer-owned, nothing to apply |
| docs/helper-policy.md | consumer-edited | template unchanged — consumer-owned, nothing to apply |
| docs/collaboration-model.md | diverged | both the template and the doc moved — manual merge |
| docs/ai-project-workflow.md | consumer-edited | template unchanged — consumer-owned, nothing to apply |
| docs/owner-profile.md | consumer-edited | template unchanged — consumer-owned, nothing to apply |
| docs/AGENT_ORIENTATION.md | diverged | both the template and the doc moved — manual merge |
| docs/current-state.md | consumer-edited | template unchanged — consumer-owned, nothing to apply |
| docs/question-router.md | consumer-edited | template unchanged — consumer-owned, nothing to apply |
| docs/CAPABILITIES.md | missing | absent — upgrade's adopt pass replants it |
| docs/ideas/README.md | consumer-edited | template unchanged — consumer-owned, nothing to apply |
| .session-journal.md | consumer-edited | template unchanged — consumer-owned, nothing to apply |
| control/README.md | diverged | both the template and the doc moved — manual merge |
| control/inbox.md | consumer-edited | template unchanged — consumer-owned, nothing to apply |
| control/status.md | diverged | both the template and the doc moved — manual merge |
| .claude/CLAUDE.md | template-improved | consumer-untouched + template improved — safe to apply with `upgrade --apply-docs` |

## Template deltas for diverged docs

### CONSTITUTION.md

```diff
--- CONSTITUTION.md (template@old, current slots)
+++ CONSTITUTION.md (template@new, current slots)
@@ -23,6 +23,12 @@
   a separate blocking question. Two payoffs, not one: it catches a misread
   before work happens, and the filled-in picture is itself new material the
   owner reasons against and redirects.
+- **Capabilities are discovered, never assumed.** `docs/CAPABILITIES.md` is
+  the verified ledger of what sessions here can and cannot do — read it at
+  session start. Before declaring a wall or a missing credential: check that
+  file → check the environment (`printenv`, tool lists) → attempt once and
+  capture the exact error → append the finding same session. An imagined
+  wall stalls the session; an unrecorded real one taxes every later session.
 - When a doc and a source file disagree: Source code and merged PRs win over any doc. When a doc and a source file disagree, treat the doc as stale, follow the source, and fix the doc in the same session — drift you can see (a wrong ledger entry, a stale pointer) is fixed on sight, not deferred.
 
 ## Autonomy rails — act vs. ask
@@ -33,6 +39,13 @@
   large / cross-cutting (architectural), or when the goal itself is
   genuinely ambiguous. No live owner to ask? Record the question in
   `docs/question-router.md` instead of skipping it or guessing.
+- **Owner attention is the scarcest resource.** Before routing anything to
+  the owner: attempt it yourself, or cite the exact wall (the
+  `docs/CAPABILITIES.md` discipline) — assumption-based asks are banned.
+  Every ask carries the OWNER-ACTION fields — WHAT / WHERE / HOW /
+  WHY-IT-MATTERS / UNBLOCKS / VERIFIED-NEEDED (format:
+  `control/README.md`) — phrased so a non-technical owner can act on it
+  directly. Expire stale asks; fewer, clearer asks beat complete lists.
 
 ## Changing the rules — propose, don't apply
 
```

### docs/collaboration-model.md

```diff
--- docs/collaboration-model.md (template@old, current slots)
+++ docs/collaboration-model.md (template@new, current slots)
@@ -23,6 +23,17 @@
 - **Ask** when the change is irreversible (data loss / external publish),
   large and cross-cutting (architectural), or the goal itself is genuinely
   ambiguous.
+
+## Routing work to the owner
+
+The owner is the scarcest resource in the program. An ask reaches the owner
+only when the agent has **attempted the action itself** or can name the
+**exact wall** (error text, permission denial) proving only the owner can do
+it — assumption-based asks are banned. Every ask uses the OWNER-ACTION
+format — WHAT / WHERE / HOW / WHY-IT-MATTERS / UNBLOCKS / VERIFIED-NEEDED
+(canonical: `control/README.md`) — phrased so a non-technical owner can act
+directly: one plain sentence, an exact click path, paste-ready text.
+Withdraw asks that have gone stale; fewer, clearer asks beat complete lists.
 
 ## Friction → guard
 
```

### docs/AGENT_ORIENTATION.md

```diff
--- docs/AGENT_ORIENTATION.md (template@old, current slots)
+++ docs/AGENT_ORIENTATION.md (template@new, current slots)
@@ -9,7 +9,9 @@
 
 1. `.claude/CLAUDE.md` — the working agreement.
 2. `docs/current-state.md` — the living status ledger.
-3. This file — task-specific reading routes.
+3. `docs/CAPABILITIES.md` — verified session capabilities & walls (the
+   discovery rule lives there; append what you learn).
+4. This file — task-specific reading routes.
 
 ## Binding contracts
 
@@ -26,7 +28,7 @@
 `docs/collaboration-model.md` · `docs/helper-policy.md` ·
 `docs/repo-navigation-map.md` · `docs/ai-project-workflow.md` ·
 `docs/owner-profile.md` · `docs/current-state.md` · `docs/decisions.md` ·
-`docs/question-router.md` · `docs/ideas/README.md` — plus the root
+`docs/question-router.md` · `docs/CAPABILITIES.md` · `docs/ideas/README.md` — plus the root
 `CONSTITUTION.md` (the working agreement) and `.session-journal.md`.
 
 ## Verifying any change
```

### control/README.md

```diff
--- control/README.md (template@old, current slots)
+++ control/README.md (template@new, current slots)
@@ -19,10 +19,30 @@
 writer of its own `status.md`. Two writers never touch the same file, so there are no merge
 conflicts. Everything is append-only / overwrite-own — forward-only git.
 
+## Multi-Project repos — per-lane heartbeats (optional extension)
+
+A SHARED repo can host several Projects ("lanes" — e.g. a mining lane and an exploration lane
+cohabiting one game repo). The one-writer rule scales by **splitting the heartbeat, never by
+sharing it**:
+
+- **One status file per lane** — `control/status-<lane>.md` (e.g. `control/status-mining.md` +
+  `control/status-exploration.md`). Each lane is the sole writer of its own file and overwrites
+  it as its session's deliberate LAST step; no lane ever edits another lane's heartbeat.
+- **`control/inbox.md` stays single** — the manager remains its one writer; a lane-specific
+  order names its lane in `do:`.
+- **Declare every lane heartbeat to the kit** — `substrate.config.json` →
+  `"heartbeat_files": ["control/status-mining.md", "control/status-exploration.md"]` (default
+  when unset: `["control/status.md"]`). The status checker then gates each listed file
+  independently (missing / heartbeat-less lane = strict RED; per-lane staleness warns), and the
+  Stop hook's overwrite reminder clears when any lane's heartbeat is fresh (it cannot know which
+  lane a session belongs to). An empty list falls back to the default — misconfiguration never
+  silently disables the gate.
+
 ## Per-session ritual (every session, and every routine wake)
 
 - **FIRST:** git pull (a stale clone reads stale orders); read `control/inbox.md`; execute any
-  order whose status is `new`, in priority order (P0 before P1). An order's `do:` is a pointer to
+  order whose status is `new`, in priority order (P0 before P1) — **claim it first** (see
+  "Claiming an order" below). An order's `do:` is a pointer to
   a committed doc — read it. If an order is ambiguous or you disagree, do NOT guess: write it in
   your status under `⚑ needs-owner` and proceed with the rest.
 - **LAST (deliberate final step):** overwrite `control/status.md` — updated timestamp, current
@@ -34,6 +54,37 @@
 (strict = red), warns when the heartbeat goes stale, and the Stop hook reminds you when
 `status.md` was not overwritten this session.
 
+## Claiming an order — one executor per order (claim FIRST, build second)
+
+An order's `status: new` is visible to every session that wakes, so two readers can both
+believe they are its executor — a realized failure, not a theoretical one (substrate-kit
+PRs #50/#51: two lanes independently executed the same ORDER 005 the same day, and a whole
+session's work had to be reconciled as twins). The manager only flips `new→done` after
+seeing the status report; the claim covers the gap in between.
+
+Before executing any `new` order:
+
+1. **Re-read the bus at origin/main HEAD** — `control/inbox.md` AND every sibling status
+   file (`control/status*.md`). If another lane's status already claims the order
+   (`claimed-by:` naming its id) or reports it in `done=`, stand down and pick other work.
+2. **Claim FIRST, on your own status file's orders line** — append
+   `claimed-by: <order-ids> <lane-or-session> <ISO8601>` — and land it on **main** BEFORE
+   any build work (a control-only fast-lane PR, or a direct commit where your rules allow
+   one). A claim that exists only on a branch is invisible; only main counts.
+3. **Re-read once more after the claim merges** — two claims can race in flight; the
+   tiebreak is the earliest claim merged to main. The loser withdraws its claim line in
+   its next status overwrite and stands down.
+4. **Claims expire** — a claim with no visible build activity (no open PR, no fresh
+   heartbeat referencing the order) after ~24h may be treated as abandoned and re-claimed;
+   note the takeover in your status `notes:`. A dead lane must never deadlock an order.
+
+With an active claim the `orders:` line reads e.g.:
+`orders: acked=001-008 done=001-006 claimed-by: 007+008 coordinator-lane 2026-07-09T18:38Z`
+— the executor drops the `claimed-by:` annotation in the overwrite that moves those ids
+into `done=`. One writer per file is preserved: you only ever claim on your OWN status.
+(Shipped by inbox ORDER 007 — the root-cause fix for the twin-execution failure; the
+ritual was live-proven manually on this repo's own orders before graduating here.)
+
 ## `status.md` format (what you write every session — your heartbeat)
 
 ```markdown
@@ -41,12 +92,46 @@
 updated: <ISO8601>            # heartbeat — stale = the manager treats the Project as dark
 phase: <what I'm doing right now, one line>
 health: green | red-by-design (<why>) | broken (<what>)
+kit: v<X.Y.Z> · check: green|red · engaged: yes|no   # kit self-report — see below
 last-shipped: #<PR> — <one line>
 blockers: <what's stopping me, or `none`>
-orders: acked=<ids> done=<ids>
+orders: acked=<ids> done=<ids> [claimed-by: <ids> <lane-or-session> <ISO8601>]
 ⚑ needs-owner: <a decision/action only the owner can give, or `none`>
 notes: <anything the manager should know>
 ```
+
+The `kit:` line is the **substrate-coordinator visibility** channel (kit-lab reads it via the
+manager relay — zero write access to this repo): `v<X.Y.Z>` = the vendored kit version this
+repo actually runs (update it in the same session as every `bootstrap upgrade`); `check:` =
+the latest `check --strict` verdict on this tree; `engaged:` = the post-adopt engagement gate
+(`yes` once no UNRENDERED banner/slot remains, live CI runs the gate, and the session loop
+has engaged).
+
+## ⚑ needs-owner — the OWNER-ACTION item format (quality contract)
+
+The owner is the scarcest resource in the program: every ask routed to the owner costs
+attention, and an unclear or unnecessary ask stalls your own lane on top of burning his.
+**Before routing ANYTHING to the owner, try it yourself or cite the exact wall** — an
+assumption-based ask ("agents probably can't do X") is banned; the bar is the capability
+ledger (`docs/CAPABILITIES.md`) plus one real attempt with the captured error.
+
+Every ⚑ needs-owner item carries ALL of these REQUIRED fields — inline on the item, or as a
+structured block the item links to:
+
+```markdown
+⚑ OWNER-ACTION
+WHAT: <one plain sentence, zero jargon — the thing the owner does>
+WHERE: <exact click path or URL>
+HOW: <paste-ready text/values where applicable, or "click only">
+WHY-IT-MATTERS: <one sentence, in product terms>
+UNBLOCKS: <what starts moving the moment it's done>
+VERIFIED-NEEDED: <the attempt you made + the exact error/wall proving only the owner can do
+this — never an assumption>
+```
+
+Hygiene: **expire or withdraw stale asks every session** (an answered or obsolete ask left in
+the list is drift), and **fewer, clearer asks beat complete lists**. `check` warns — advisory,
+never exit-affecting — when a non-`none` ⚑ needs-owner list lacks these fields.
 
 ## `inbox.md` order format (manager-written, append-only)
 
```

### control/status.md

```diff
--- control/status.md (template@old, current slots)
+++ control/status.md (template@new, current slots)
@@ -2,6 +2,7 @@
 updated: (seeded at adopt — no real heartbeat yet: overwrite this whole file at your first session close)
 phase: adopted — first session not yet run
 health: green
+kit: v1.6.0 · check: red · engaged: no
 last-shipped: none
 blockers: none
 orders: acked= done=
@@ -9,3 +10,6 @@
 notes: seeded skeleton planted by substrate-kit adopt. This Project is the SOLE writer of this
 file — overwrite it (never append) as the deliberate LAST step of every session, per
 `control/README.md`. `check` holds strict RED until the first real heartbeat replaces this seed.
+The `kit:` line is your kit self-report (substrate-coordinator visibility): keep the version in
+sync with your vendored kit on every upgrade, `check:` = your last `check --strict` verdict,
+`engaged:` = the post-adopt engagement gate (yes once `check` reports ENGAGED/green live CI).
```

