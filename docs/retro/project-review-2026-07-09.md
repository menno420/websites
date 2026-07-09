# websites — full project review (2026-07-09)

> **Status:** `complete` — owner-directed full project self-review + wake-up pass.
> Verified against the repo (merged PRs, decision ledger, live services) rather than
> memory; every "cannot determine" below is an honest limit, not a guess. Companion
> files: the gen-1 retro answers (`docs/retro/self-review-2026-07-09.md`, ORDER 003)
> and the question set (`docs/retro/QUESTIONS.md`).

---

## (a) What this Project is + its TRUE current state

**What it is.** The `websites` repo for the menno420 estate — **one repo, three
public Railway services** (share code, not a process), all in the fresh Railway
project **`superbot-websites`** (never the production-bot project):

| Service | Live URL | Deployed sha (verified this session) | Role |
|---|---|---|---|
| control-plane (`app/`) | https://control-plane-production-abb0.up.railway.app | `6abe19f` = `main` HEAD ✅ in sync | Readiness board + journal + fleet page |
| botsite (`botsite/`) | https://botsite-production-cfd7.up.railway.app | `6abe19f` ✅ in sync | Public marketing/reference site |
| dashboard (`dashboard/`) | https://dashboard-production-a91b.up.railway.app | `6abe19f` ✅ in sync | Read-only developer/bot-inventory dashboard |

All three `/healthz` 200 and all three `/version` report `6abe19f` (current `main`
HEAD) — **verified live this session** via `scripts/healthcheck.py` + direct
`/version` probes. No drift. All three are **public, no auth**; the one gated corner
is control-plane `/owner` (HTTP Basic on `SITE_PASSWORD`, [D-0012]).

**Control-plane feature set (verified in `app/` + `docs/site.md`):**
- **Readiness board `/`** — live GitHub-API status over superbot / superbot-next /
  substrate-kit / websites; Actions-secret **names masked to a count** on the public
  board.
- **Journal browser `/journal/…`** — sanitized markdown render + cross-repo search (PR #18).
- **Deploy-state drift cell** — DEPLOYED sha vs `main` HEAD per service, `/version`
  JSON on all three (ORDER 001, PR #26).
- **`/activity`** — merged cross-repo PR timeline; **`/ideas`** — cross-repo idea
  backlog (PR #33, [D-0020]).
- **`/fleet`** — every fleet lane's `control/status*.md` as one glanceable screen
  (ORDER 002, PR #35), with the lane set derived **live from the fleet-manifest**
  (PR #36, [D-0022]).
- **Auto-refresh** on the two live-monitoring surfaces (`/` + `/fleet`), 45s soft
  `#live-content` swap, pause/resume (PR #37, [D-0023]); content pages stay static.
- **Gated `/owner` area** — un-masked board + privileged actions (cache refresh,
  re-run failed CI) (PR #14, [D-0012]).
- Stack: FastAPI + Jinja2 + httpx, server-rendered, no build step, TTL cache.

**Kit + CI.** substrate-kit engaged (adopted PR #1; upgraded v1.0.0 → v1.2.0, PR #31,
[D-0019]). The **`quality`** workflow is a **REQUIRED** status check on `main` (owner
set the ruleset; verified live on PR #18) — runs `bootstrap.py check --strict
--require-session-log`, the ambient-Railway-ID guard, and every service's pytest
suite (121 tests as of PR #37). Deploy = merge (Railway auto-deploys `main`).

**Merged work.** 37 PRs merged: **#1–#39** minus **#5, #9, #22** (closed as
superseded/duplicate — the parallel-checkout churn). #1–#37 are the build; #38/#39
were the *manager* appending ORDERS 003/004 to `inbox.md`. **Decision ledger:
`[D-0001]`…`[D-0023]`** (this review adds `[D-0024]`). **Session cards: 25** in
`.sessions/` (26 with this session's).

**Outstanding orders at this session's start:** ORDERS 001/002 done; **003 (retro)
and 004 (Model backfill) were genuinely unexecuted** — both executed this session
(retro answers + 18-card backfill; `bootstrap.py check --strict` now green).

---

## (b) The agent audit

Every session/agent/subagent that worked this Project. Deliverables verified against
the repo where possible; models stated honestly (see the model note below the table).

### Builder-session subagents (spawned via Agent tool, `worker` type, model = **claude-opus-4-8 inherited**, not independently confirmed)

| # | Task | Delivered (verified) | Stall / friction | Class |
|---|---|---|---|---|
| 1 | Adopt substrate-kit | PR #1 (kit adoption) ✅ | none | — |
| 2 | Build control-plane site | PR #2 (FastAPI+Jinja board+journal) ✅ | none | — |
| 3 | Deploy to fresh Railway | PR #3; created project `superbot-websites` ✅ | none | — |
| 4 | Write deployment memory | memory file | none | — |
| 5 | Set GITHUB_PAT on Railway | PR #6 (board fully live) ✅; PR #5 closed (superseded) | prior worker to *scan env* for the PAT blocked by auto-mode as credential-exploration → owner named `GITHUB_PAT` | (a) instructions + by-design safety |
| 6 | Draft dashboard/botsite rework plan | PR #4 ✅ | navigated parallel shared-checkout entanglement forward-only | (a) setup |
| 7 | Build+deploy botsite | PR #7 ✅ | 1st attempt git-worktree isolation FAILED ("not in a git repo / no WorktreeCreate hooks") → relaunched fresh clone | (b) platform + (a) setup |
| 8 | Build+deploy dashboard | PR #8 + polish #10 ✅; PR #9 closed (superseded) | concurrent-merge conflict | (a) setup |
| 9 | Final health check all services | verified + memory ✅ | none | — |
| 10 | Read dashboard credential | DECLINED to relay password on coordinator authority (correct refusal); left in Railway | by-design safety refusal | by-design safety |
| 11 | Drop auth (control-plane+dashboard) | PR #12 + docs #13 ✅ | none | — |
| 12 | Update deployment memory (auth) | memory | none | — |
| 13 | Build gated `/owner` area | PR #14 + #15 ✅ | none | — |
| 14 | Kit-hygiene cleanup | PR #16 (8 docs rendered, quality.yml gate, ledger backfill, 7 Qs routed, D-0013) ✅ | could NOT set `quality` REQUIRED — proxy blocked rulesets API (403 "Write access … not permitted through this proxy"); owner set it manually | (b) platform |
| 15 | Write project retrospective | PR #17 ✅ | none | — |
| 16 | Persist standing mandates | memory | none | — |
| 17 | Adopt fleet control protocol | PR #23 ✅ | `control/README.md`+`inbox.md` didn't exist yet (manager hadn't committed) → wrote status.md in default format | (a) cross-lane timing |
| 18 | Fix born-red gate | PR #24 (adopted kit v1.0.0 bootstrap; closed 2 holes; proven both directions) ✅ | root: PR #19 had auto-merged EMPTY on its born-red card — a real gate leak | (a)+(c) |
| 19 | Status drift resolved | PR #28 ✅ | none | — |
| 20 | Execute ORDER 001 (drift cell) | PR #26 + status #27 ✅; surfaced dashboard deploy lag | none in build; surfaced a platform lag | — |
| 21 | Re-check dashboard version | read-only; found dashboard still 404 (lag not self-resolved) | platform lag, not agent | (b) |
| 22 | Redeploy lagging dashboard | non-destructive pinned-SHA redeploy, SUCCESS ✅ | — | — |
| 23 | Investigate dashboard auto-deploy | PR #29 — ROOT CAUSE: dashboard Railway service had **no push→deploy trigger**; recreated it (non-destructive), proven by #29 auto-deploying | Railway service-creation gap | (b) platform/config |
| 24 | Status deploy-fix resolved | PR #30 ✅ | none | — |
| 25 | Cross-repo activity+ideas views | PR #33 + status #34 (/activity, /ideas) ✅ | none | — |
| 26 | Execute ORDER 002 (/fleet) | PR #35 (all 10 lanes render) ✅ | none | — |
| 27 | Fleet manifest live-parse | PR #36 (drift-proof lane source) ✅ | none | — |
| 28 | Auto-refresh + CI audit | PR #37 (45s auto-refresh; CONFIRMED quality runs full 121-test suite; ~17s was fast, not a skip; no fix) ✅ | none | — |
| 29 | Diagnose PR#37 "failure" | read-only; confirmed failures were the benign born-red gate holding | — | — |

### Other sessions (coordinator-supplied; models "cannot determine" unless self-reported)

| Session | Delivered | Stall / friction | Model |
|---|---|---|---|
| **BUILDER session** ("control-plane build & deploy") — spawned all 29 subagents above | the whole gen-1 build | recurring cross-cutting stalls (see below) | **claude-opus-4-8** (self-reported) |
| **Coordinator** (front-door) | orchestration | never stalled; standing limit: no scheduler | **claude-fable-5** (self-reported; config `claude-fable-5[1m]`, fallback `claude-opus-4-8[1m]`) |
| "Audit: PR blockers + kit compliance" (10:07Z) | 3-part audit (stuck PRs ×4 repos, kit-usage, live-site probe); drove kit-hygiene batch | none observed | cannot determine |
| "substrate-kit #17 rebase" (10:17Z) | rebased sk#17 green/mergeable; confirmed born-red gate fixed at kit v1.0.0 + an unreleased mtime hole | none | cannot determine |
| "Dependabot policy + clear 6 PRs" (10:24Z) | owner policy Q-0256, Q-0257 DISCUSS filed, merged 5 dependabot PRs, closed #1761 dup, session PR #1886 merged | born-red CI reds mid-session were the gate *working*, not stalls | cannot determine |
| Coordinator worker "Verify deployed site live" | delivered clean | none | claude-fable-5 (inherited, per spawn config) |
| Coordinator worker "Read deployment doc token section" | delivered | none | claude-fable-5 (inherited) |
| Coordinator worker "Hourly site health check #1" | eventually ran probes on demand ~03:55Z, delivered green | REPEATEDLY STALLED: backgrounded its sleep + exited early twice; Monitor capped 30min vs 60 requested; foreground long sleep harness-blocked | (b) platform — clearest case |
| Coordinator worker "Hourly site health check #2" | nothing before superseded by event-driven monitoring; idle | armed 29-min Monitor waits; superseded | (b) platform |
| Coordinator worker "Verify dashboard deployment live" | delivered healthz/401 | BLOCKED on the authed check — credentials file lived in the builder session's per-session scratchpad, unreachable cross-session | (b) platform design + (a) cross-session secret handling |

**Model note (honest).** The BUILDER session self-reports **claude-opus-4-8**. Its
subagents were spawned as `worker` with **no model override**, so they **inherit
claude-opus-4-8** — but a child worker's exact model is not independently
introspectable from the parent, so this is "opus-4-8 by inheritance, not
independently confirmed." The coordinator self-reports **claude-fable-5**; its own
direct workers inherit claude-fable-5 per spawn config. Other spawned *sessions*
(audit, sk#17, dependabot) are **cannot determine** — the coordinator has no
model-introspection for child sessions, and these did not self-report a model.

### Recurring cross-cutting stalls (named once)

- **(i) No scheduler/`send_later` primitive** in any session → "hourly monitoring"
  could not be armed as a timer; improvised via background-worker completions.
  **The single clearest platform limitation. Class (b).**
- **(ii) Early parallel workers shared ONE git checkout/HEAD** → superseded PRs #5,
  #9; self-fixed by serializing ledger-touching workers + per-worker fresh clones.
  **Class (a), self-corrected.**
- **(iii) GitHub MCP read tools served STALE/cached PR+run state (~1 min lag)** →
  workers confirmed merges via `git ls-remote` instead. **Class (b).**
- **(iv) Kit one-doc-per-decision `stamp` check reddened CI silently** when a D-NNNN
  was cited in two docs. **Class (a)/(c) — real but easily-tripped guard.**
- **(v) GitHub Actions runner-allocation stalled ~24 min once** (PR #20, infra
  backlog). **Class (b).**

---

## (c) The answered retro questions

Answered in full, by ID, in **`docs/retro/self-review-2026-07-09.md`** (ORDER 003) —
every question A1–G3, honest over flattering, each claim tied to a PR/commit/file,
with "cannot determine" used where it is the true answer. Headline findings that
matter for gen-2 setup: the **model line should be born with every card** (no
grandfather backfills — B2/G2); **per-worker clones + serialized ledger writes** as a
founding rule (A4/C4/F1); a **scheduler primitive** is the one capability worth almost
anything (F3); and **`status: new` on an order never flips** — a waking session must
diff inbox against its own `status.md`, which a fresh session would misread (E4).

---

## (d) Honest efficiency verdict

**Where the time actually went** (reconstructed from the record — no per-session
timing was kept, itself a finding):
- **Building dominated** (the three sites + control-plane feature set = the bulk of
  37 PRs) and was efficient — most sessions shipped a PR with no stall.
- **The real waste was concentrated, not diffuse:**
  1. **Parallel-checkout churn** — PRs #5/#9 produced nothing; recovering meant
     serializing and re-cloning. Highest pure-waste sink.
  2. **Credential/safety choreography** — the PAT-scan auto-mode hold (owner
     round-trip) and the dashboard-password relay refusal. Correct by design, but
     costly; a seed env-facts doc removes the first entirely.
  3. **Dashboard deploy-trigger hunt** — a lag surfaced in #26, chased to root in
     #29 (no push→deploy trigger). Two sessions for a service-creation-time omission.
  4. **Improvised monitoring** — no scheduler, so "hourly" health checks stalled
     repeatedly (#1 exited early twice, Monitor 30-min cap vs 60-min need) before
     event-driven monitoring replaced them.

**What I'd redo, in order:**
1. **Per-worker fresh clones + serialized ledger writes from the first spawn** (kills
   #5/#9 and the entanglement).
2. **Create the Railway push→deploy trigger with every service** (kills the #26→#29 hunt).
3. **Seed an env-facts doc naming the deploy token + Railway IDs** (kills the PAT-scan hold).
4. **Open tiny status/doc PRs born-complete** (no runtime risk → skip the born-red round-trip).
5. **Ship gate-tightening with its grandfather step** (the v1.2.0 Model-line
   requirement should have carried the 18-card backfill — then ORDER 004 never exists).
6. **A scheduler primitive** for liveness (retires the improvised monitoring entirely).

Candid bottom line: the *output* is strong and fully verified-live; the *inefficiency*
was almost entirely one-time discovery cost in isolation, credentials, and deploy
plumbing — all seed-fixable, none in the product work itself.

---

## (e) ⚑ OWNER ACTIONS — only the owner can do these

Verified against `docs/owner/OWNER-ACTIONS.md` and the repo. Each with exact steps.

1. **Custom domains** for the three sites (unblocks friendly URLs, deferred to cutover).
   Railway → project **`superbot-websites`** → each service (control-plane / botsite /
   dashboard) → **Settings → Networking → Custom Domain → Add** → enter your domain →
   Railway shows a target host → at your DNS provider add a **CNAME** for that
   subdomain pointing at the shown target → wait for the green check.
2. **Provision the `/submit` submissions Postgres** (unblocks the botsite public
   feature/bug intake pipeline; today a labeled stub `botsite/templates/submit.html`).
   Railway → project **`superbot-websites`** → **New → Database → Add PostgreSQL** →
   once created, copy its `DATABASE_URL` → on the **botsite** service → **Variables →
   New Variable** → `DATABASE_URL` = (paste) → redeploy. Then tell an agent to wire the
   moderation ring (needs a mirror PAT too). OWNER-ACTIONS #2 / rework-plan Q5.
3. **Wire `/admin` to a live-bot control API** (unblocks the Discord-OAuth panel that
   *writes* the live bot — settings/help/cog-routing/moderation; today a
   credential-free stub `dashboard/templates/admin.html`). **Owner go required — prod
   writes.** Decide *where bot control lives* (websites / superbot / superbot-next),
   then it's a **separate** service: provision the Discord OAuth app + a scoped
   control-API token; do NOT reuse the ambient production `RAILWAY_*_ID` vars
   (`docs/RAILWAY-SAFETY.md`). OWNER-ACTIONS #1 / rework-plan Q4.
4. **Visual restyle vs. preserve-v1** (taste). Decide whether the shipped `ds/`-based
   restyle stands or the original superbot visual design is carried over. One word back
   ("keep restyle" / "preserve v1") unblocks any visual follow-up. OWNER-ACTIONS #5 /
   rework-plan Q2.
5. **OLD-site cutover / retirement in superbot** — go/no-go (decision). Retire the
   `dashboard/` + `botsite/` still living in `menno420/superbot` once these replace
   them. Verify the live websites URLs first (they're green, this session). OWNER-ACTIONS #6.
6. **Redeploy-from-browser scoped deploy hook** — yes/no. A gated `/owner` button that
   triggers a Railway redeploy of a websites service from the site. Needs a Railway
   deploy hook scoped to `superbot-websites` only. Currently deploy = merge (auto). OWNER-ACTIONS #3.
7. **(Optional, low effort) A public production-bot health/liveness URL.** If the live
   production bot exposes a public health endpoint, paste the URL here and an agent will
   add a bot-liveness signal to the board/fleet page. If none exists, nothing to do.

**Already DONE by the owner (no action):** `quality` is set as a REQUIRED status check
on `main` (owner configured the ruleset 2026-07-09; verified live on PR #18).

---

## (f) CONTINUATION — what I'll do next WITHOUT the owner

All contained, reversible, test-covered, self-directed (decide-and-flag) — picked up
in the next self-directed pass / cadence, no owner input needed:
- **`/activity.xml` Atom feed** — already in the backlog; a machine-readable feed of the
  cross-repo activity timeline (the `/activity` view already exists, PR #33).
- **A `/fleet` live-parse smoke check** (A3): assert the manifest parse still yields a
  non-empty lane set so a manifest reformat surfaces as an alert, not a silent
  fallback.
- **A `docs/ideas/` shelf for this repo** so self-directed follow-ups (like this one)
  are picked off a backlog instead of re-derived (the #37 `⟲` review's own point).
- **A `.sessions/` card template** carrying the `📊 Model:` line + ender checklist, so
  no future grandfather backfill (ORDER 004's whole class) is ever needed.
- **Heartbeat enrichment** (G3): add a machine-readable outstanding-orders field +
  deployed-sha/last-verified-live to `control/status.md` so `/fleet` shows "what's
  left" without diffing inbox vs status vs git.

These will be flagged `⚑ Self-initiated:` on their session run reports when built.
