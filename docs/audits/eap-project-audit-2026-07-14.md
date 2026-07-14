# websites — EAP project close-out audit (2026-07-14)

> **Status:** `audit`
>
> The seat's definitive EAP close-out audit (owner directive 2026-07-14,
> coordinator-relayed). Written 2026-07-14T08:52Z from branch
> `claude/eap-audit-0714` (origin/main @ `eee8c7a`; the branch differs from
> main only by this audit's own card + claim, so `path@eee8c7a` citations hold
> for every cited tracked file). Every number below is measured or explicitly
> marked LEAD / not measured; quotes are verbatim. This doc stands alone.

**Relation to the previous audit** (`docs/audits/2026-07-13-fleet-cleanup-audit.md`
— an outside observer's read-only snapshot; not restated here, only delta'd):
all four of its suggestions moved within a day. Its finding 1 (orphaned claim
file) was swept and its suggestion 2 became the #318 claims-drift CI gate
(`ba1aa86`); its suggestion 3 (`project.index.json` placeholder) was populated
by PR #319 (`3076e9d`); its risk flag 4 (the self-documented automerge-race
overlap) fired for real on PR #321 within 24 hours and got its reconciliation
in PR #324 (open, parked by its own rail); its suggestion 1 (fleet-wide
lifeboat convention) is upstream as a `control/outbox.md` proposal. Open PRs
moved 9 → 11 (the same 7 draft lifeboats persist).

## 1. Identity & scale

Measured 2026-07-14T08:35Z on `menno420/websites`, origin/main @
`eee8c7a189ec6227ed5dcea4199e183e15a730c9`.

| Metric | Value | Source / command |
|---|---|---|
| Repo / seat | menno420/websites — four independent FastAPI services: `app/` (control-plane), `botsite/`, `dashboard/`, `review/`; shared code, never a shared process | `.claude/CLAUDE.md` architecture section @ eee8c7a |
| Active window | 2026-07-09 02:59:30 +0200 (first commit `aec1cd5`) → 2026-07-14 08:35Z = **6 calendar days** | `git log --reverse --format='%ci %h' origin/main \| head -1` |
| Session cards | **201** (202 `.md` files in `.sessions/` minus `README.md`) | `ls .sessions/*.md \| grep -v README \| wc -l` |
| Commits on main | **353** | `git rev-list --count origin/main` |
| PRs opened | **332** — **316 merged, 5 closed-unmerged, 11 open** (numbers contiguous 1–332, no gaps; full 4-page `list_pull_requests state=all` sweep, deduped) | GitHub MCP, 2026-07-14; closed-unmerged: #5, #9, #22, #268, #283 |
| Open-PR composition | 7 draft rescue/lifeboat parks (#245 #249 #257 #278 #279 #280 #300) + 1 non-draft rescue (#281) + 3 live (#324, #330 bake bot, #332 this audit) | same sweep |
| Backlog bullets | **117** total: **78 built/shipped, 33 captured, 6 retired**, 0 planned | `docs/ideas/backlog.md` @ eee8c7a; bullets = `^- \*\*` lines; state = first backticked marker per bullet (83 bullets) or the plain words for the 34 older ones |
| docs/*.md files | **21** (top level of `docs/`) | `ls docs/*.md \| wc -l` |
| GitHub workflows | **6**: auto-merge-enabler, healthcheck, host-automerge-extras, quality, review-bake, smoke-crawl | `ls .github/workflows/` |
| Test count | **1414 collected** across all four suites | `python3 -m pytest tests/ botsite/tests dashboard/tests review/tests -q --collect-only` → "1414 tests collected in 4.06s" |

Not measured: per-service test split (collect-only ran as one four-suite
invocation only).

## 2. Tooling used

Verdict scale: reliable / flaky / painful. One citation each; dispositions on
every row.

| Tool / surface | How it was used | Verdict + evidence | Disposition |
|---|---|---|---|
| GitHub MCP tools | All PR create/read/merge-state, workflow-run reads, full 332-PR + 733-run sweeps for this audit | **Reliable**, but PR-state reads served up to **~25 min stale** with no staleness signal — "acting on a stale \"open\" or \"merged\" is how agents double-land work" (`botsite/data/agent_pr_tree.json:210@eee8c7a`) | ANTHROPIC — staleness-signal ask, §6 row 4. Doctrine until then: `git ls-remote` / Actions runs are truth, never an MCP read alone |
| git through the egress proxy | Clone, fetch, branch, push on every session; this audit's own unshallowed clone | **Reliable** — pushes verifiable via `ls-remote`; noise: shallow-clone fetches report false "forced update" alarms, disproven by deep merge-base (`control/status.md@837cfab`) | FLEET-FIX — boot-time `git fetch --unshallow` (§6 row 2) |
| pytest + kit gate (`quality.yml`) | Required check on all 332 PRs + 152 main pushes; 1414-test baseline | **Reliable** post-#314 — 152/152 main runs green; the control fast lane was a measured **false-green** pre-#314 (#307 merged green while breaking heartbeat grammar; PR #310 body: "#307 merged red") | FLEET-FIX (shipped) — #314 fast-lane grammar pins (`cd4aa9d`); residual pin-map hollowing risk flagged in §7 |
| Auto-merge enabler | Landed 300+ of the 316 merges (merged_by github-actions[bot] on every merged PR sampled) | **Reliable**, one raced incident: workflow-touching #321 auto-merged past the host rail ("host `arm-on-open` disarmed by 01:41:09Z, kit `enable-auto-merge` re-armed at 01:41:25Z" — PR #324 body) | FLEET-FIX — #324 label-first carve-out (open, owner-merge-only by design) |
| Railway deploy-on-merge | Every merge to main deploys the four services; zero deploy-specific incidents recorded | **Reliable** for deploys; variable **writes** are classifier-walled ("[Secret Store Writes] … authorized only by an untrusted coordinator-context", `docs/CAPABILITIES.md@eee8c7a`, 2026-07-13) | ACCEPTED — the wall coincides with the repo's own `docs/RAILWAY-SAFETY.md` policy (§3 row 1) |
| Playwright / Chromium | Smoke-crawl workflow (#321) + live route verification | **Painful** to first light: "the agent egress proxy resets a TLS 1.3 ClientHello" (`docs/CAPABILITIES.md`, 2026-07-13); works capped at TLS 1.2, cert verification ON, proven on all 15 review-site routes | ANTHROPIC — TLS 1.3 ask, §3 row 7 |
| Trigger / send_later MCP | Pacemaker chains + failsafe crons kept sessions waking overnight | **Flaky at platform level**: "84/85 send_later one-shots fired" 07-10/11, then the 07-12 scheduler incident silently dropped 9 due one-shots + wedged 2 crons (`review/data/evidence/02-incident-2026-07-12.md`) | ACCEPTED with defense-in-depth — layered failsafe cron + pacemaker chain self-revived every time since; fire-ledger want in §10 |
| Worker subagents | Coordinator-dispatched builders/verifiers all week | **Flaky on timers**: "3 workers this sitting parked on sleep/monitor waits and died silently … recovered only by a coordinator re-message" (`control/outbox.md:60`) | ACCEPTED — harness design ("Foreground `sleep` is blocked"); fleet memory: never park a worker on a timer (§3 row 8) |

## 3. Tooling walled or missing

13 distinct walls in the verified-walls ledger (`docs/CAPABILITIES.md@eee8c7a`)
and cited cards; 8 remain live, 5 fully neutralized by proven workarounds.
All quotes verbatim.

| # | Capability wanted | Verbatim denial / error + date | Workaround | Disposition |
|---|---|---|---|---|
| 1 | **Write Railway variables** (envhub set-live) | Classifier denial, 2026-07-13 (ledger): "[Secret Store Writes] The sub-agent prompt instructs a live Railway variableUpsert/variableDelete creating an env-var entry on the production dashboard service, authorized only by an untrusted coordinator-context (not user intent)". Ledger adds: "Railway itself was never reached, so API-level write capability stays **UNTESTED**" and the write "would be DISHONEST even if [it] worked" (empty values crash int-parsed TTL vars, `app/config.py:83`). | Owner pastes real values; "`/owner/environments` already lists exactly which names are missing per service" (ledger) | **ACCEPTED** — the harness wall coincides with the repo's own `docs/RAILWAY-SAFETY.md` policy; ORDER 026 resolved create-nothing (`.sessions/2026-07-13-coordinator-sitting.md@eee8c7a`). |
| 2 | **RAILWAY_TOKEN provisioned** (live GraphQL reads for /owner/environments) | Ledger 2026-07-12: "**`RAILWAY_TOKEN` is NOT provisioned** — neither in this agent session's environment (`printenv \| grep -i railway` shows only the ambient production trio + `RAILWAY_API_KEY`, none of which `/owner/environments` may use per `docs/RAILWAY-SAFETY.md`…) nor on the deployed control-plane service" | "none agent-side — the token is an owner-click Railway errand; the page degrades honestly" (ledger) | **FLEET-FIX** — owner mints the project-scoped `superbot-websites` token (decided 2026-07-11 per ledger, not yet landed); already an OWNER-ACTIONS row. |
| 3 | **`gh` CLI in the container** | `docs/succession/next-boot-2026-07-09.md:125@eee8c7a`: "GitHub is **MCP-tools-only**; no `gh` CLI." `botsite/data/agent_pr_tree.json:119@eee8c7a`: "Inside the sandbox, `gh: command not found` is normal: use the platform's API/MCP tooling instead of shelling out to gh." (2026-07-09 seed) | GitHub MCP tools + git proxy cover PR create/merge/read (ledger 2026-07-09 capability: "PRs #44/#45 this session") | **ACCEPTED** — MCP coverage is complete for this repo's flows; no session has been blocked by the absence itself since 07-09. |
| 4 | **Direct `api.github.com` HTTP** (curl, unauthenticated reads) | Ledger seed: "**`api.github.com` direct HTTP**: blocked → GitHub access is MCP-tools-only." Verbatim error, 2026-07-10 entry: `403 {"message":"GitHub access to this repository is not enabled for this session. Use add_repo to request access."}` ("the CCR proxy's own gate, not a GitHub-side error") | MCP tools; `add_repo`; raw.githubusercontent.com and `github.com/<o>/<r>/releases/download/...` DO pass (ledger 2026-07-09/10 capabilities) | **ANTHROPIC** — paste-ready ask: "In Claude Code cloud sessions, please let the egress proxy pass anonymous read-only GETs to api.github.com / github.com content for PUBLIC repos (or return a clearly distinguishable proxy status) instead of a blanket per-session 403 — the substituted 403 masks GitHub's real HTTP semantics and broke our link-rot gate (websites PR #328)." |
| 5 | **Merge Actions-created bake PRs** (required `quality` check) | Ledger 2026-07-13: merge attempts "return verbatim `405 Repository rule violations found` / `Required status check \"quality\" is expected.`, `mergeable_state` stays `blocked`" — even with a green dispatch-chained `quality` run on the head ("the ruleset wants the required context from a `pull_request`-event run, not a same-named dispatch run") | Interim: "a session — i.e. any non-GITHUB_TOKEN actor — closes and reopens the bake PR" (precedent PR #259; used again on #270) | **FLEET-FIX** — durable fix per ledger: "the bake PR must be CREATED by a non-GITHUB_TOKEN credential (fine-grained PAT as an Actions secret, review-bake's `GH_TOKEN` switched to it)" — filed in `docs/owner/OWNER-ACTIONS.md` (BAKE_PAT ask). GitHub-side behavior, not Anthropic's. |
| 6 | **Delete branches** (prune 22+ rescue/bake orphans) | Ledger seed (2026-07 fleet findings): "**Branch deletion**: 403 on every path (git push `:branch` and API)" | "owner deletes by hand / enables 'Automatically delete head branches'" (ledger) | **ANTHROPIC** — paste-ready ask: "Please allow Claude Code cloud sessions to delete non-default branches they themselves pushed (git push :branch or the API currently 403s on every path) — without it, every rescue/bake branch becomes permanent clutter only the owner can prune." Parallel FLEET-FIX: owner flips the repo's auto-delete-head-branches toggle. |
| 7 | **Default Chromium through the egress proxy** (TLS 1.3) | Ledger 2026-07-13: "the agent egress proxy resets a TLS 1.3 ClientHello, so a default Chromium launch fails the handshake" | "capping the browser at TLS 1.2 (certificate verification stays ON, proxy CA bundle `/root/.ccr/ca-bundle.crt`) connects cleanly" — proven on all 15 review-site routes (ledger) | **ANTHROPIC** — paste-ready ask: "The Claude Code cloud egress proxy resets Chromium's TLS 1.3 ClientHello, forcing headless browsers to run with --ssl-version-max=tls1.2; please support TLS 1.3 in the proxy's MITM path so browser automation works with default TLS settings." |
| 8 | **Foreground sleep / timer-parked workers** | `.sessions/2026-07-13-coordinator-sitting.md:68-70@eee8c7a`: "**Background workers parked on timers/monitors 3×** (dead per fleet memory — workers are not resumed by sleep); fixed each time by re-messaging the worker." (2026-07-13; the harness itself documents "Foreground `sleep` is blocked" in the Bash tool contract) | Re-message the worker; `send_later` / Monitor-until-loop for scheduled waits | **ACCEPTED** — harness design; the fleet workaround (never park a worker on a timer) is now fleet memory. |
| 9 | **Tag push / release create via git** | Ledger seed: "**Tag push / release create via git**: HTTP 403 from the environment's git proxy" | "use the workflow_dispatch release path" — "proven repeatedly fleet-wide" (ledger Capabilities) | **ACCEPTED** — workaround is reliable and already doctrine. |
| 10 | **Actions runner creates PRs** (review-bake) | Ledger 2026-07-12: both bake runs "died at `gh pr create` with the exact error: \"GraphQL: GitHub Actions is not permitted to create or approve pull requests (createPullRequest)\"" (runs 29167034060, 29184552812) | "none in-repo — the fix is the owner console toggle (Settings → Actions → General → 'Allow GitHub Actions to create and approve pull requests')" (ledger) | **FLEET-FIX (resolved 2026-07-12)** — owner flipped the toggle same day (OWNER-ACTIONS Decided row M); a PAT secret also bypasses (same PAT as row 5). |
| 11 | **Routine-fired sessions: push + PR tooling** | Ledger 2026-07-10: the 16:01Z fired session's "`git push` never landed, despite its session card recording the branch as pushed"; same session's API error verbatim: `403 {"message":"GitHub access to this repository is not enabled for this session. Use add_repo to request access."}`; separately its "toolset does NOT include GitHub PR-creation tooling" | "NEVER record 'pushed' without proof (`git push` exit 0 AND `git ls-remote origin <branch>` shows the commit)"; leave PR-open/merge to an interactive session (ledger) | **ANTHROPIC** — paste-ready ask: "Routine-fired (scheduled) Claude Code sessions sometimes start without GitHub access to their own repo (add_repo-gated 403) and without PR-creation tools — please make a trigger's fresh sessions inherit the creating session's repo grants and toolset so scheduled automation can land its own work." |
| 12 | **Self-merge owner-gated PRs / cleanup `rm`** | Ledger seed: "**Self-merge classifier**: sessions can be refused merging owner-gated PRs while their other capabilities work — and the boundary differs by session kind". Coordinator card @eee8c7a: "plus `rm` classifier denials on cleanup" (2026-07-13) | Record which session kind hit which boundary; route owner-gated merges to the owner | **ACCEPTED** — the classifier guarding owner-gated merges and destructive cleanup is working as intended; cost is small once known (but see §9 pain 1 for the consent-shape ask on green, reviewed PRs). |
| 13 | **GraphQL API quota** | Ledger seed: "**GraphQL API quota**: tight — batch queries and prefer the REST-backed MCP tools for bulk reads." | Batch + REST-backed MCP tools (ledger) | **ACCEPTED** — no session since has hit it as a hard stop (no append-log entry). |

Biggest wall: the CCR egress proxy's per-session GitHub gate (rows 4 + 11) —
it blocks direct API reads, silently substitutes 403 for real GitHub
semantics (fed the PR #328 masking finding, §6), and stranded a routine-fired
session's push. Costliest GitHub-side wall: the required-check 405 on
GITHUB_TOKEN bake PRs (row 5) — every bake needs a manual close/reopen until
the BAKE_PAT owner action lands.

## 4. Merge & landing friction

Sources: full PR dataset (332/332), full `quality.yml` run history (733/733
runs), PR bodies #307/#310/#314/#321/#324/#281, local `git branch -r`,
`.sessions/`, `docs/CAPABILITIES.md`. MCP PR-state reads can be ~25 min stale.

### 4.1 Time-to-land (createdAt → mergedAt, all 316 merged PRs)

| Stat | Value |
|---|---|
| Median | **3.1 min** |
| Mean | 14.3 min |
| Worst | **#163 — 493 min (8.2 h)**, "chore(session): reviewer session card 2026-07-12" |
| Fastest | #3, #13, #15 — 0.1 min (docs-only records) |

| Bucket | PRs | Share |
|---|---|---|
| < 5 min | 213 | 67% |
| 5–15 min | 60 | 19% |
| 15–60 min | 27 | 9% |
| 1–6 h | 15 | 5% |
| > 6 h | 1 | 0.3% |

The entire >1 h tail is human-click waits, not CI — dominated by the
2026-07-12 classifier-parked cluster: #159 (259 min), #160 (264 min),
#161 (248 min), #141 (249 min), #163 (493 min).

### 4.2 Quality-round churn — with the born-red caveat

All 733 `quality.yml` runs grouped by head_branch; ">1 round" = a `failure`
later followed by a `success` on the same branch.

| Metric | Value |
|---|---|
| PR branches with quality runs | 314 |
| Single clean pass | 132 (42%) |
| Failure later followed by success | **147 (47%)** |
| Failed and never passed | 7 |
| main-branch runs | 152/152 green |

**Honesty caveat: 47% overstates true rework.** The kit's session gate holds
runs "born-red BY DESIGN" until the session card flips `complete`
(self-described in PR #314/#321/#324/#308 bodies), so many first-run failures
are the designed HOLD, not broken code. Genuine-rework share was not
separable without reading job logs for ~197 failed runs (not spent). Worst
churners: `claude/review-site-expansion` and `claude/order-012-records-reconcile`
(7 runs each).

### 4.3 The #321 automerge race → #324

- **#321** (smoke-crawl workflow, merged 2026-07-14T01:42:00Z by
  github-actions[bot]) was a **workflow-touching PR that auto-merged anyway**:
  the kit enabler and the host rail raced on every `pull_request` event, and
  per #324's body, "host `arm-on-open` disarmed by 01:41:09Z, kit
  `enable-auto-merge` re-armed at 01:41:25Z — the rail was defeated and the
  workflow-touching PR auto-merged anyway" (the kit's 15 s label-grace sleep
  made its arm reliably land after the host's disarm).
- **#324** (open) fixes it by speaking the kit's own carve-out protocol:
  label `do-not-automerge` FIRST (the enabler's documented off-switch), then
  disarm, then a 75 s settle re-check; label-API failure exits loudly red.
  All changes confined to `host-automerge-extras.yml` (the kit enabler is
  regenerated byte-identical on upgrades). Proven with an offline two-job
  concurrency harness replaying the exact #321 interleaving.
- #324 is itself workflow-touching, so it parked itself: labeled
  `do-not-automerge`, `mergeable_state: dirty` — **owner-merge-only by design**.

### 4.4 Owner-click dependencies

**5 past human-click landings measured, 9 pending.** The other 300+ merges
landed via the enabler.

| PR(s) | Click |
|---|---|
| #324 | **pending** — owner removes label + merges by hand (by design) |
| #281 | **pending** — coordinator card-flip or owner attention (kit-held red: "do not close; do not bypass") |
| #245 #249 #257 #278 #279 #280 #300 | **pending** — 7 owner close/keep decisions on the draft lifeboats (enumerated as exactly these 7 in merged PR #308's body) |
| #283 | past — lifeboat closed unread 2026-07-13T13:20:48Z |
| #159 #160 #161 | past — agent merge refused by the permission classifier; parked "for the owner to squash-merge in order #159 → #161 → #160" (`.sessions/2026-07-12-reviewer-session.md`); merge timestamps match that order |
| #270 | past — session-family merge "permission-denied"; PR "stays PARKED... waiting for a sibling session... or the owner" (`.sessions/2026-07-13-bake-check-wall.md`) |

### 4.5 Branch litter

182 remote branches excl. main: 11 open-PR heads, **151 leftovers of merged
PRs** (deletion is a 403 wall, §3 row 6), 4 closed-unmerged leftovers, and
16 never-PR'd (13 rescue-family + 1 known-empty probe per PR #147 + 2 stale
`bake/review-data-*`).

### 4.6 The #307 fast-lane false-green incident

1. **What went wrong:** #307 (control-only heartbeat overwrite, merged
   22:34Z) rode the fast lane that "skips pytest by design", so it merged
   green while breaking `control/status.md`'s field grammar — "every
   subsequent full quality run on main fails 3 tests" (#310 body): false-green
   on its own PR, red exported to the next unrelated PRs.
2. **What fixed it:** #310 (merged 22:49Z, 15 min later) restored the
   grammar; #314 (merged 23:20Z) closed the class — the fast lane now runs
   exactly the relevant grammar pin on the PR introducing the drift
   (`control/status.md` → `test_own_heartbeat.py`, `control/outbox.md` →
   `test_outbox_grammar_pin.py`).
3. **Citations:** PR #307 body ("control-only fast-lane diff... enabler arms,
   lands on green"), PR #310 body ("#307 merged red"), PR #314 body ("Path
   (b) is the gate that would have caught #307 pre-merge").

### 4.7 Classifier denials on merge-path actions — 4 documented

1. `.sessions/2026-07-12-reviewer-session.md` — "Approve + squash-merge was
   attempted and **refused by the platform permission classifier** (quote:
   \"[Merge Without Review] ... no [named+specifics] consent exists\")...
   Deny-wins: no merge was forced or retried around the classifier."
2. `.sessions/2026-07-13-bake-check-wall.md` — "**Landing #270 from this
   session-family: permission-denied**".
3. `docs/CAPABILITIES.md` — "**Self-merge classifier**: sessions can be
   refused merging owner-gated PRs while their other capabilities work — and
   the boundary differs by session kind (a child session was refused where a
   coordinator was not)."
4. `.sessions/2026-07-13-agent-pr-diagnostic.md` — "the live self-merge
   classifier refusal" stored verbatim in `botsite/data/agent_pr_tree.json`.

### 4.8 Dispositions

| Recurring cause | Disposition |
|---|---|
| Kit-enabler vs host-rail automerge race (defeated the rail on #321) | **FLEET-FIX** — #324's label-first carve-out + settle re-check; survives kit regeneration. Remaining click: owner merges #324. |
| Fast-lane false-green (control-only diffs skipped pytest → #307) | **FLEET-FIX (shipped)** — #314's targeted fast-lane grammar pins. |
| Self-merge classifier refusing agent merges of green, reviewed PRs (the entire >1 h time-to-land tail) | **ANTHROPIC** — paste-ready ask in §9 pain 1. |
| 151 undeleted merged branches + deletion 403 | **FLEET-FIX** — owner enables "Automatically delete head branches"; ANTHROPIC deletion ask in §3 row 6; until then ACCEPTED. |
| 7 draft lifeboats + 16 never-PR'd rescue branches | **ACCEPTED** (convention working as designed) with a follow-up: periodic coordinator disposal sweep (close-unread list enumerated in #308). |
| Born-red HOLD inflating failed-run stats (47% fail→pass) | **ACCEPTED** — designed gate; follow-up idea: a distinct check name for the HOLD so retry metrics separate designed red from real red. |

## 5. Scheduling & wake friction

### 5.1 review-bake schedule

**Cron `23 5 * * *`, unchanged since the workflow was born** (created in
PR #141 commit `0545906`, merged 2026-07-11T20:24:48Z; `git log -p --follow`
shows one cron line ever added, zero edits since — later PRs #175/#269/#274/#297
never touched the schedule).

| run ID | event | created (UTC) | conclusion | vs 05:23Z slot |
|---|---|---|---|---|
| 29167034060 | workflow_dispatch | 2026-07-11T20:26:33Z | **failure** | n/a (manual) |
| 29184552812 | **schedule** | 2026-07-12T07:38:28Z | **failure** | +2h15m late |
| 29202721928 | workflow_dispatch | 2026-07-12T17:49:33Z | success | n/a (manual) |
| 29235587736 | **schedule** | 2026-07-13T08:28:54Z | success | +3h05m late |
| 29242851190 | workflow_dispatch | 2026-07-13T10:28:08Z | success | n/a (manual) |
| 29314319655 | **schedule** | 2026-07-14T07:22:06Z | success | +1h59m late |

- **3 schedule fires ever, zero missed days** (07-12/13/14, exactly one
  each), **all +2–3 h late** — matching the standing doctrine "cron timing is
  ±hours, never gate anything on a slot" (`docs/CAPABILITIES.md` 2026-07-11).
- The 2 failures were the since-resolved Actions PR-creation wall (§3 row
  10), not the schedule. Disposition: **ACCEPTED** (GitHub-side lag, doctrine
  in place); residual bake landing friction is §3 row 5's BAKE_PAT FLEET-FIX.

### 5.2 smoke-crawl first slot — CURRENT TRUTH: fired late, not wedged

Workflow added by PR #321 (`7b08200`); cron `47 2-23/6 * * *` (02:47 / 08:47 /
14:47 / 20:47Z). The 05:22Z heartbeat (`e37ddbb`, PR #325, written from a
03:15Z check) recorded "WATCH: 02:47Z first slot did not fire — zero runs at
03:15Z check". **Re-checked 2026-07-14T08:37Z: exactly one run —
run 29308117901, event=`schedule`, created 05:16:54Z, conclusion=`success`**
(4m40s, head `2b5947d`). The 02:47Z slot was delivered ~2h30m late — **the
schedule is proven, not wedged**; the 03:15Z "zero runs" observation was a
too-early check. The 08:47Z slot showed nothing at the 08:48Z final check —
**not diagnostic** given the observed lag; next meaningful re-check ~11:30Z
(§11). Disposition: **ACCEPTED** — same ±hours doctrine; the workflow's
failure path (failed-workflow email + red Actions tab) covers a genuinely
failed run.

### 5.3 send_later reliability

| Window | Record | Source |
|---|---|---|
| 07-10→07-11 | "84/85 send_later one-shots fired" — clean batch (cites a live registry export, not re-verifiable from git) | `review/data/evidence/02-incident-2026-07-12.md` §1 |
| 07-12 ~02:30–08:00Z | Platform scheduler incident: **9 due one-shots silently dropped** across 5 seats, **2 crons wedged** (`enabled=true`, `next_run_at` frozen); seats with healthy `*/2` failsafe crons self-revived ~08:0xZ | same evidence file (verbatim from superbot night-review @ `8558179`) |
| 07-12/13 night | Late-delivery anomaly 00:45–02:10Z (late, **not lost**); failsafe + pacemaker recovered unaided, "subsequent fires on schedule (04:45/06:45/08:45Z verified)" | `control/outbox.md:43`; `.sessions/2026-07-13-coordinator-sitting.md` |
| 07-13/14 night | **"~40+ pacemaker timers armed, fired reliably" is coordinator-reported LEAD, not measured** — no per-tick ledger exists in the repo. Indirect corroboration: 27 merges landed on main 23:12Z→09:52Z (#303→#331) and the 05:22Z heartbeat records the armed failsafe cron + ~15 min pacemaker chain — the seat demonstrably kept waking all night | git log origin/main; `control/status.md@e37ddbb` |

Also recorded: one duplicate pacemaker tick forked and hand-deduped; 6
concurrent pending one-shots at the 09:30Z report — hygiene noise, not
failures (`control/outbox.md:48`). Disposition: **ACCEPTED with
defense-in-depth** — the layered failsafe design is the mitigation; a
platform fire-ledger is a §10 wishlist want.

### 5.4 Dead workers — honest count

**Repo-measured total: 3.** "3 workers this sitting parked on sleep/monitor
waits and died silently (dead per fleet memory); each was recovered only by a
coordinator re-message" (`control/outbox.md:60`, corroborated by the
coordinator card). Strictly these parked on sleep/monitor waits; whether each
had also armed a send_later is not recorded. The night 07-13/14's "at least 1"
worker-timer death is **not measured** — no card, heartbeat, or outbox entry
records it (the coordinator session was still live at audit time, so its
sitting-ender card does not exist yet). Disposition: **ACCEPTED** (§3 row 8
doctrine: never park a worker on a timer) + §10 want (death notification).

## 6. Environment & platform

| # | Issue | Evidence (verbatim + date) | Count / freshest | Disposition |
|---|---|---|---|---|
| 1 | Container deaths | **Not measured** — 0 mentions of "ENV-DEAD" / "container death" in `.sessions/*.md`, `docs/CAPABILITIES.md`, or `control/` git history (case-insensitive rg + `git log --all -S 'ENV-DEAD'`, both empty). Nearest neighbors are worker-level, not container-level (§5.4). | 0 tracked | **ACCEPTED / instrument** — adopt an `ENV-DEAD` tag in the CAPABILITIES append log so the next occurrence is countable instead of folklore. |
| 2 | Shallow-clone "forced update" false alarms | `control/status.md@837cfab` (2026-07-13T20:53:35Z): "\"forced update\" reports = shallow-clone artifact (deep merge-base verified, history intact)." Only this ONE tracked citation exists (`git log --all -S 'forced update'` → 837cfab only), so the "recurring all night" frequency is **not measured** in tracked history. Re-confirmed by this audit's own unshallowed clone (full history, no forced updates, clean merge-bases). | 1 tracked citation | **FLEET-FIX** — boot-time `git fetch --unshallow` (or a CAPABILITIES one-liner: "forced update on a shallow fetch = artifact, verify merge-base before alarming"); zero real history loss ever found. |
| 3 | `.substrate/state.json` churn + kit-stub noise | Coordinator card @eee8c7a: "**Kit auto-draft session stubs repeatedly dirtied the shared checkout** — the real time sink of the sitting: 3 lifeboat draft PRs (#245/#249/#257) plus `rm` classifier denials on cleanup." `git branch -r` today: **22 rescue/lifeboat branches** (12 `rescue/*`, 8 `claude/rescue-*`, 2 `claude/lifeboat-*`). **Freshest instance: THIS session** — pre-sync found dirty `M .substrate/state.json` again; rescued to `rescue/eap-audit-pre-sync` @ `555208d` (2026-07-14T08:32:52Z, diff = `.substrate/state.json | 6 ±3`, verified pushed via ls-remote). | ≥7 lifeboat draft PRs + 22 rescue/lifeboat branches; freshest 555208d, 2026-07-14 | **FLEET-FIX** — coordinator already routed it upstream ("worker briefs gain a standing 'kit stubs → scratchpad, never commit' line"); complete it kit-side: auto-draft stubs + `state.json` session-counter writes go to scratchpad or get gitignored. Highest-frequency env annoyance in the record. |
| 4 | MCP PR-state staleness (~25 min) | `botsite/data/agent_pr_tree.json:210@eee8c7a`: "MCP PR-state reads can run ~25 minutes stale — acting on a stale \"open\" or \"merged\" is how agents double-land work or abandon a PR that already merged." Same figure in `.substrate/skills/upgrade-distribution/SKILL.md:59` and `.substrate/upgrade-report.md:88-89`. Earlier, smaller: `docs/succession/next-boot-2026-07-09.md:126`: "PR/run state served stale ~1 min (silent — no error text)". | Observed ~1 min (07-09) → ~25 min (v1.15 kit-report era) | **ANTHROPIC** — paste-ready ask: "The GitHub MCP server in Claude Code cloud has served PR merge/CI state up to ~25 minutes stale with no staleness signal — please shorten the cache TTL or expose a fetched-at timestamp so agents can tell a fresh read from a stale one." Doctrine until then: `git ls-remote` / Actions runs are truth. |
| 5 | Egress-proxy 403-vs-404 masking (PR #328) | PR #328 body (merged 2026-07-14T04:25:32Z) verbatim: "**those container 403s are the CCR egress proxy's per-session GitHub gate, not GitHub itself — in proxy-less CI, GitHub answers anonymous requests to genuinely private repos with 404, so a scheduled-run 404 can mean repo privacy as well as a rewrite defect.**" Locally: `.sessions/2026-07-14-md-link-sample.md:53-59@eee8c7a` ("that 403 is the agent container's per-session proxy gate (verified this session: the response body is the CCR 'access not enabled for this session' JSON)"); live sample: "sampled 10, 9× 403 … + 1× 200". | Found 2026-07-14; 9/10 sampled responses proxy-substituted | **FLEET-FIX (near)** — build the captured backlog disambiguator (`docs/ideas/backlog.md:1828-1844@eee8c7a`: visibility probe or committed known-private-repo list). Root cause is §3 row 4's proxy gate — covered by that ANTHROPIC ask. |

## 7. Process & ceremony cost

Rule applied: a gate "paid for itself" only if it caught something real, with
a citation. Each verdict doubles as the disposition.

| Gate / practice | Caught (citation) | Cost (rough) | Verdict / disposition |
|---|---|---|---|
| Born-red card gate | The gate exists BECAUSE PR #19 auto-merged EMPTY (`docs/current-state.md:554`; the empty-merge decision entry in `docs/decisions.md`); kit fix regression-tested (`tests/test_born_red_session_gate.py`), "verified holding first-hand on PR #46"; then "the born-red → flip pipeline landed 63 PRs with zero bad merges" (`.sessions/2026-07-13-coordinator-sitting.md`) | Card+flip commits on every PR; 1 documented substring false positive — `IN_PROGRESS_TOKENS` includes bare `"hold"`, so branch name "place**hold**ers" tripped it (`control/outbox.md:64-67`, cites `bootstrap.py:1957/:2035`); kit auto-draft stub churn is adjacent friction (§6 row 3) | **Paid for itself** — ACCEPTED; word-boundary fix proposed upstream (§8) |
| Claims convention (alone) | Its failure mode was caught by hand: the orphaned railway-placeholders claim outlived merged PR #275 (`docs/audits/2026-07-13-fleet-cleanup-audit.md`, finding 1) | Claim create+release per session; drifts when the release step is skipped | **Mixed** — convention alone drifted within hours; ACCEPTED now that the #318 gate backstops it |
| #318 claims-drift gate | Live-validated day one: "the new gate flagged exactly this file before deletion" — the known-stale claim (`.sessions/2026-07-14-claims-drift-gate.md`) | ~0 CI cost; 1 reported zero-commit false positive — **LEAD, not found in the repo record** (§11) | **Paid for itself** — FLEET-FIX shipped (`ba1aa86`); pin the FP lead with a synthetic zero-commit test |
| Heartbeat contract tests | Caught the #307 grammar break; PR #310 restored it 15 min later (`0ea4b6c`, subject verbatim: "restore heartbeat field grammar (fixes test_own_heartbeat reds from #307)") | Tiny (one pytest file); the fast-lane hole delayed the red to the next PR | **Paid for itself** — ACCEPTED |
| Docs word-budget gate | Tripped twice 2026-07-13 (7120 and 7135 vs 7000), forcing compression of superseded detail only — no bug caught, but boot-read bloat is exactly its job (`CLAUDE.md`: front-loading "buys ceremony, not context — measured") | Two trim passes, ~minutes each; headroom invisible until breached (captured, `docs/ideas/backlog.md:1585`) | **Mixed, leaning paid** — ACCEPTED |
| Six-field asks (`docs/owner/OWNER-ACTIONS.md`) | Paste-shaped asks resolved same-day (Actions toggle row M; RAILWAY_TOKEN + GITHUB_TOKEN, 07-12) — but **no evidence the FORMAT caused the speed**, and decision-shaped asks (Q-0004, open since ≤07-11) sat through the whole EAP | 9 open + ≥5 decided blocks maintained; two dated re-verification sweeps embedded | **Mixed** — ACCEPTED; no causation claim |
| Kit gate + control fast lane | The fast lane was a measured **checker false-green pre-#314**: a typo'd REPORT heading and #307's heartbeat break both merged green because control-only diffs skipped pytest (`.sessions/2026-07-13-fastlane-outbox-gate.md`) | quality-run time on every PR; the false-green cost two fix PRs | **Mixed** — kit gate pays; the fast lane was FLEET-FIXED by #314 (`cd4aa9d`, proven on 5 synthetic diff shapes); residual: the pin map is unexecuted shell that can hollow out silently (flagged as the #314 session's own 💡) |

Measured checker failures to carry forward: the pre-#314 fast-lane
false-green, the born-red "hold" substring false positive, and the
unconfirmed claims-gate zero-commit false positive (LEAD — §11).

## 8. What we fixed ourselves

All SHAs on origin/main @ `eee8c7a` unless noted; one line + citation each.

| Fix | What it fixed | Citation |
|---|---|---|
| #310 heartbeat grammar restore | Restored the control heartbeat field grammar #307 broke, un-redding `test_own_heartbeat` | PR #310, `0ea4b6c` (2026-07-13 22:49Z) |
| #314 fast-lane grammar pins | Fast lane no longer false-greens grammar-breaking control edits (outbox REPORT + status heartbeat pins) | PR #314, `cd4aa9d` (2026-07-13 23:20Z) |
| #318 claims-drift gate | A claim outliving its merged branch now reds `quality` (+ sweep of the real stale claim) | PR #318, `ba1aa86` (2026-07-14 00:30Z) |
| #324 automerge race park rail | Workflow-touching PRs park deterministically via the kit's own `do-not-automerge` carve-out (label-first + settle re-check), reconciling the race that let #321 auto-merge | PR #324 — **OPEN, not on main**: head `70ec3d2`, parked by its own rail, owner-merge-only by design |
| #285 env crash-class gate | CI gate failing module-level bare `int()`/`float()` over env vars (static AST scan) | PR #285, `7582185` (2026-07-13 13:45Z) |
| #287 hostile-env import smoke | Dynamic complement: imports every service module under a poisoned environment | PR #287, `6a0e59d` (2026-07-13 14:07Z) |
| #290 poison-list pin | Self-deriving poison list so #287's smoke can't silently miss newly documented env vars | PR #290, `6360263` (2026-07-13 15:18Z) |
| #321 smoke-crawl | Scheduled Playwright smoke-crawl — browser-level complement to `healthcheck.yml` | PR #321, `7b08200` (2026-07-14 01:42Z) |
| #322 relative-link rewrite | Rewrites relative links in remotely-rendered markdown + serves `/favicon.ico` fleet-wide | PR #322, `22dcfec` (2026-07-14 02:14Z) |
| Kit "hold"-substring workaround | Born-red gate substring-matches `"hold"` (`bootstrap.py:1957/:2035`); workaround = keep branch names off Status lines; word-boundary fix proposed upstream | KIT-GRADUATION PROPOSAL, `control/outbox.md:64-67@eee8c7a` (landed via PR #276, `5381fdb`) |

Extras found in the same sweep (cap 5):

| Fix | What it fixed | Citation |
|---|---|---|
| #282 env-parse hardening | The original crash-class fix that #285/#287 then gated; documented SITE_PASSWORD | PR #282, `096202c` (2026-07-13 13:33Z) |
| #309 suite-level token pin | Killed the ambient-token flake class via an autouse `tests/conftest.py` fixture | PR #309, `26b4d6e` (2026-07-13 22:52Z) |
| #320 botsite import valve | Self-recovery from a live data loss: owner-auth import restores `export.json` after a redeploy wipe | PR #320, `49db5e4` (2026-07-14 01:16Z) |
| #328 link-check followup | Hardened its own #322 fix: smoke-crawl sample-checks the rewritten links exist | PR #328, `2b5947d` (2026-07-14 04:25Z) |
| #212 heartbeat grammar fix | Same self-inflicted-grammar class as #310, two days earlier | PR #212, `472a1f5` (2026-07-12 21:32Z) |

Score: 9 of 10 headline items verified merged on origin/main; #324 exists and
is verified but is deliberately parked by the rail it introduces. Disposition
for the section: **FLEET-FIX (shipped)** across the board — this is the
evidence the seat closes its own incident classes same-day.

## 9. Top 5 remaining pains (ranked by measured cost)

| Rank | Pain | Measured cost | Disposition |
|---|---|---|---|
| 1 | **Owner-click dependency cluster / self-merge classifier wall** | The entire >1 h time-to-land tail (16 PRs, worst 8.2 h); 5 past clicks + 9 pending (#324, #281, 7 lifeboats); 4 documented classifier denials (§4.7) | **ANTHROPIC** — paste-ready ask: "On repo menno420/websites, agent sessions are refused squash-merging PRs they (or sibling reviewer sessions) verified green ('[Merge Without Review]... no [named+specifics] consent exists'), and the boundary differs by session kind (child refused where coordinator was not). Please document the intended consent shape for agent-initiated merges — what standing owner authorization (e.g. a CLAUDE.md grant, a repo setting, or per-PR label) the classifier will honor — so green PRs don't park 4–8 h for a human click." Parallel owner errands: merge #324, sweep the lifeboats. |
| 2 | **GitHub egress-proxy gate** (api.github.com + `gh` walled → MCP-only) | Blocks direct API reads; substituted 403s masked real GitHub semantics and broke the link-rot gate (PR #328, 9/10 sampled responses proxy-substituted); stranded a routine-fired session's push (§3 row 11) | **ANTHROPIC** — paste-ready ask (§3 row 4): "In Claude Code cloud sessions, please let the egress proxy pass anonymous read-only GETs to api.github.com / github.com content for PUBLIC repos (or return a clearly distinguishable proxy status) instead of a blanket per-session 403 — the substituted 403 masks GitHub's real HTTP semantics and broke our link-rot gate (websites PR #328)." Plus the routine-fired-session grants ask (§3 row 11). |
| 3 | **`.substrate/state.json` churn spawning rescue branches** | 22 rescue/lifeboat branches, ≥7 lifeboat draft PRs, called "the real time sink of the sitting"; recurred THIS session (`555208d`) | **FLEET-FIX** — kit-side: auto-draft stubs + state.json counter writes to scratchpad or gitignored (§6 row 3); brief-side line already proposed upstream. |
| 4 | **Scheduled-workflow fire lag** (+2–3 h on every cron) | All 4 schedule-event fires ever (3 bake + 1 smoke-crawl) delivered +1h59m…+3h05m late; manufactured one false "wedged" alarm (§5.2) | **ACCEPTED** — GitHub-side; doctrine holds ("cron timing is ±hours, never gate anything on a slot"); no missed days ever. |
| 5 | **Branch-deletion 403 litter** | 151 undeleted merged-PR branches + 16 never-PR'd; only the owner can prune | **ANTHROPIC** — paste-ready ask (§3 row 6): "Please allow Claude Code cloud sessions to delete non-default branches they themselves pushed (git push :branch or the API currently 403s on every path) — without it, every rescue/bake branch becomes permanent clutter only the owner can prune." Parallel FLEET-FIX: owner enables auto-delete-head-branches. |

Ranked out (6th): the Chromium TLS 1.3 wall — real, but the TLS 1.2 workaround
is proven on all 15 routes and the smoke-crawl ships with it; its ANTHROPIC
ask stands in §3 row 7.

## 10. Wishlist (ranked, net-new only — deduped vs §3/§9)

1. **A queryable trigger/send_later fire ledger** (past fires + delivery
   timestamps, agent-readable) — three of this audit's LEADs (§11: the "~40+
   overnight timers", the 84/85 figure, timer-death attribution) would have
   been measurements instead of leads; today the only evidence is what a
   session happens to write down.
2. **Harness notification when a background worker dies** (event or poll
   surface) — the 3 measured silent worker deaths (§5.4) were each found by a
   coordinator noticing silence, not by any signal.
3. **Boot-time unshallowed clones** (or a `fetch --unshallow` knob in the
   session environment) — kills the "forced update" false-alarm class at the
   source (§6 row 2's repo-side workaround stands until then).

Already dispositioned above, referenced not repeated: auto-delete-merged-
branches (§3 row 6 / §9 pain 5), MCP staleness signal (§6 row 4), public-repo
proxy pass-through (§3 row 4 / §9 pain 2), proxy TLS 1.3 (§3 row 7),
faster cron delivery (§5.1/§9 pain 4 — ACCEPTED), Actions PR-creation toggle
(§3 row 10 — resolved 2026-07-12).

## 11. Honest gaps — what this audit could not measure, and why

| Gap | Why |
|---|---|
| Container deaths | 0 tracked mentions anywhere in the repo (rg + `git log --all -S 'ENV-DEAD'` both empty) — no lifecycle ledger exists; §6 row 1 proposes instrumenting. |
| "~40+ overnight send_later timers fired reliably" (07-13/14) | Coordinator-reported **LEAD** — no per-tick ledger in the repo; corroborated only indirectly by 27 overnight merges (#303→#331) and the armed failsafe/pacemaker lines in `control/status.md@e37ddbb`. |
| The "#319 zero-commit claims-gate false positive" | **LEAD** — NOT FOUND in the repo record (PR #319 body/comments/commits/check-runs all clean; quality run 29297236583 SUCCESS). Mechanism is plausible from the code: Lane 1 (`git merge-base --is-ancestor`, `tests/test_claims_drift_gate.py:99`) is trivially TRUE for a branch with zero unique commits, so the gate would call a brand-new claim "merged". Note #319 opened 00:52Z, BEFORE #318 merged (02:30Z), so any FP happened session-side or on a later run. A synthetic zero-commit test would settle it. |
| True >1-round rework rate | The born-red HOLD inflates the 47% fail→pass figure (§4.2); separating designed red from real red needs job-log reads for ~197 failed runs — not spent this audit. |
| 08:47Z smoke-crawl slot | Not yet diagnostic at the 08:48Z final check — the previous slot itself arrived ~2h30m late; next meaningful re-check ~11:30Z. |
| Night 07-13/14 worker-timer deaths | Not measured — the coordinator session was still live at audit close, so the sitting-ender card that would record them does not exist yet. |
| Per-service test split | Collect-only ran as one four-suite invocation (§1). |
| PR #281 open | **BY DESIGN, not a gap in follow-through** — the coordinator's own session PR flips at the coordinator's session ender, after this audit lands. |
