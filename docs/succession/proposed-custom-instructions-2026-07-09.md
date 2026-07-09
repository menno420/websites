# Proposed gen-2 Custom Instructions — websites Project (2026-07-09)

> **Status:** `plan` — succession deliverable of the gen-1 wind-down. A proposed
> rewrite of this Project's Custom Instructions for the gen-2 fresh Project,
> derived from the recorded gen-1 experience (46 PRs, 27 session cards, the 26
> `docs/decisions.md` entries, `docs/retro/self-review-2026-07-09.md`,
> `docs/retro/project-review-2026-07-09.md`).
>
> **Baseline being rewritten:** the gen-1 lane's original Project brief,
> `superbot/docs/planning/websites-project-kickoff-2026-07-09.md` — its
> "Custom Instructions (paste-in)" section WAS this Project's Custom
> Instructions in substance.
>
> **Canonical fleet-manager blueprint NOT consulted:** reading
> `menno420/fleet-manager` `docs/gen2-blueprint.md` from the drafting session
> returned verbatim: `Access denied: repository "menno420/fleet-manager" is not
> configured for this session. Allowed repositories: menno420/superbot,
> menno420/substrate-kit, menno420/websites, menno420/superbot-next`. This
> proposal is therefore written from lived/recorded experience alone; the
> fleet-manager's shortlist of patterns (READY-never-draft, merge authority,
> agent-reachable done-whens, heartbeat-before-work, walking-skeleton,
> up-front walls, Model+time) is evaluated against that experience below —
> including two partial push-backs (rows A5, A6).

---

## 1. KEEP / DROP / ADD table

Every row is grounded in something that actually happened (PR numbers, retro
sections, decision IDs, or verbatim wall errors).

### KEEP (from the gen-1 brief — survived contact with reality)

| # | Instruction | Why (evidence) |
|---|---|---|
| K1 | Ambient `RAILWAY_PROJECT_ID`/`SERVICE_ID`/`ENVIRONMENT_ID` point at the LIVE PRODUCTION BOT — never pass them to any Railway call | The footgun was real and never fired: gen-1 minted its own project `superbot-websites` (PR #3, ledger decision 0005) and later CI-enforced the rule (`scripts/check_no_ambient_railway_ids.py`, PR #19); keep the instruction as defense-in-depth ahead of the checker. |
| K2 | The one hard rail: no destructive Railway mutation anywhere without naming the target and getting explicit owner go-ahead | Worker #10 correctly refused to relay a credential on coordinator authority (project-review §b row 10); the dashboard fix stayed non-destructive (pinned-SHA redeploy + trigger recreation, PR #29) — the line held under pressure. |
| K3 | Forward-only git: fresh branch → PR → squash-merge; never force-push, amend pushed commits, or delete remote branches | Zero history rewrites in 46 PRs; branch deletion 403s on every path anyway (`docs/CAPABILITIES.md`) — the rule matches the wall. |
| K4 | Run autonomously; deliver deployed, working results, not scaffolding or plans | 37+ merged PRs, all three services verified live at main HEAD (project-review §a) — this framing produced the output. |
| K5 | Decide-and-flag for everything reversible; only taste/money/irreversible/prod-write forks go to the owner | D2: the six OWNER-ACTIONS forks were correctly parked; the one mild miss was flagging the lane-parse *up* instead of just building it (PR #36 then built it self-directed) — the rule was right, the miss was under-using it. |
| K6 | Report a blocked capability plainly instead of working around it silently | The gen-1 "if you can't reach Railway, say so" clause generalized into the CAPABILITIES discovery rule (check file → check env → attempt once + capture exact error → append same session) — kept in generalized form (ADD A7). |

### DROP (obsolete or superseded by what gen-1 shipped/decided)

| # | Instruction | Why (evidence) |
|---|---|---|
| D1 | The step-1/2/3 build sequence (adopt kit → build control-plane → deferred rework of dashboard/botsite) | All three steps are DONE: kit adopted (PR #1, upgraded through v1.6.0, PR #45), control-plane shipped (PRs #2–#37), both sites rebuilt + deployed (PRs #7, #8). Gen-2 starts from a running estate, not a greenfield. |
| D2 | "Stop and describe your plan before starting step 3" — the one deliberate check-in | That phase happened and closed; and D2 of the retro shows the decide-and-flag pattern outperformed flag-up-first for contained work. No standing check-in survives except the destructive tier (K2). |
| D3 | "Gate access behind something simple (shared-secret/password)" | Owner reversed it verbatim "Yes drop the auth" (PR #12/#13, ledger decision 0011); the surviving shape is public sites + gated `/owner` overlay (PR #14, ledger decision 0012). Gen-2 inherits that shape as fact, not instruction. |
| D4 | Orientation pointed at superbot docs (`repo-settings-state.md`, rework checklists, dashboard/botsite READMEs) | Those were seed data for a board that now exists. Gen-2 orients on websites' OWN docs (`docs/current-state.md`, `docs/CAPABILITIES.md`, `docs/AGENT_ORIENTATION.md`, `control/README.md`, the queue-state + succession docs). |
| D5 | "Send a status report at each real milestone" (free-prose reporting) | Superseded by the control/ protocol (PR #23/#25) + the `/fleet`-rendered `control/status.md` heartbeat — structured, machine-parsed, dogfooded on the Project's own board (G1). Prose milestones are the weaker form of the same thing. |
| D6 | "State which Railway IDs you ended up using in your first status report" | Done once; the IDs are now durable facts in `.session-journal.md` + `docs/RAILWAY-SAFETY.md`, and the ambient-ID guard is CI. Gen-2 gets the IDs as an env-fact (ADD A8), not a report-back task. |

### ADD (earned by gen-1 experience; fleet-manager patterns folded in where supported)

| # | Instruction | Why (evidence) |
|---|---|---|
| A1 | READY-never-draft PRs; born-red session card as the FIRST commit, flipped `complete` as the deliberate LAST step | The born-red gate is what stops empty merges (PR #19 auto-merged EMPTY on its in-progress card; fixed by kit v1.0.0, PR #24, regression-tested) — and it was verified holding first-hand on PR #46. Draft state has no role anywhere in the gen-1 record. Supports the fleet-manager's READY-never-draft. |
| A2 | Explicit merge authority: the agent merges its own PR on `quality` green (arm `enable_pr_auto_merge` yourself on MCP-created PRs, or MCP squash-merge after green) — never wait for a human | Repo convention since PR #31; `enable_pr_auto_merge` worked first-hand on #46 (merged 4 min after open). Caveat from the walls list: the self-merge classifier once refused a child session where the coordinator was allowed (`docs/CAPABILITIES.md`) — coordinator merges are the fallback. Supports the fleet-manager pattern. |
| A3 | Agent-reachable done-whens: every task/order carries a `done-when:` the executing agent can check ITSELF, in its own PR | D5: explicit done-whens were a strength of the gen-1 orders; the one bad case was ORDER 004's "a card-less docs PR passes quality" — a FUTURE condition the session couldn't prove in its own PR, satisfied only by proxy. Supports the fleet-manager pattern, with the "in its own PR" tightening that gen-1's one failure teaches. |
| A4 | Model + time on every session card, from card #1: `📊 Model:` line AND start/end timestamps | ORDER 004 existed only because 18 pre-v1.2.0 cards lacked the Model line (B2/G2; the mtime-fallback false-red on PR #38); and "no per-session timing was kept" is itself a named finding (project-review §d). F1 rule 1: born with the card, never backfilled. Supports the fleet-manager pattern. |
| A5 | PARTIAL push-back on heartbeat-before-work: claim-FIRST before executing an inbox order (claim on your own status line, land on main, re-read, earliest-merged wins), but the full `status.md` heartbeat stays the session's LAST step | The recorded protocol (`control/README.md`) already provides the start-signal twice over: the claim ritual for orders + the born-red card as first commit (the start-declaration by design, superbot Q-0133 lineage). A mandatory full-status commit-to-main before every session adds a merge round-trip that gen-1 never needed — no gen-1 stall traces to a missing start-heartbeat, and "one writer per file / overwrite as LAST step" is the convention that kept `/fleet` honest (G1). Adopt the claim half; decline the rewrite-status-first half. |
| A6 | PARTIAL support for walking-skeleton: extend it to DEPLOY — for any new service, prove branch → PR → CI → merge → live `/version` == main HEAD before feature work; for the existing three services it's already proven, don't re-ritualize | Strongest evidence is the deploy leg: the dashboard Railway service was created WITHOUT a push→deploy trigger and silently served a stale sha for two sessions (PR #26 surfaced, PR #29 root-caused; C4 rule 2 "create the trigger with the service"). The git→CI→merge leg was effectively proven by PR #1 and never broke. A blanket skeleton-first ritual on a repo with 46 green PRs is ceremony; a per-new-service deploy-proof is the earned rule. |
| A7 | Known walls listed up front, with verbatim errors, + the CAPABILITIES discovery rule for new ones | Gen-1 lost real time to walls discoverable only by hitting them: proxy 403 on rulesets (`Write access … not permitted through this proxy`, self-review B1 — owner set the ruleset by hand), branch deletion 403 on every path, direct `api.github.com` blocked (MCP-only), tag/release push 403, no scheduler primitive (F3), GitHub MCP stale reads (~1 min; verify merges via `git ls-remote`, project-review stall iii). Supports the fleet-manager pattern; the wall list lives in `docs/CAPABILITIES.md`, the instructions carry the pointer + the top 3. |
| A8 | Env-facts up front: the deploy token is named `GITHUB_PAT`; Railway project is `superbot-websites` (explicit IDs in `.session-journal.md`); deps are NOT preinstalled (`pip install -r requirements.txt -r botsite/requirements.txt -r dashboard/requirements.txt` first — `python3 -m pytest` otherwise fails `No module named pytest`, first-hand); the clone lands on a DETACHED HEAD — branch before committing | The PAT-scan auto-mode hold cost a full owner round-trip and is "seed-fixable" (B1, D1, D4 rule 1); the pytest and detached-HEAD items are first-hand wind-down findings (dossier §3.15). |
| A9 | Parallel workers never share a checkout; ledger-touching writes serialize | F1 rule 2, stated as founding: the shared-checkout churn produced the only pure-waste PRs of the run (#5, #9 closed superseded; A4/B1/C4). |
| A10 | Orders stay `status: new` forever — outstanding work = diff `inbox.md` against your own `status.md` `done=` line; NEVER infer execution from a PR title | E4: named as the #1 thing a fresh session would misunderstand (PRs #38/#39 were the manager *appending* orders 003/004, not executing them). |
| A11 | Verification unpiped, exit codes checked: `python3 -m pytest tests/ -q` + `python3 bootstrap.py check --strict`; badge tokens only from the allowed set (`archive, audit, binding, historical, ideas, living-ledger, owner-guidance, plan, reference`) | Pipe-swallows-exit-code is the known fleet trap (dossier §3.3, run unpiped first-hand); the badge wall was hit verbatim this wind-down: `invalid badge token 'handover-ledger'`. |
| A12 | A contained, reversible, test-coverable follow-up is a BUILD candidate (route to `docs/ideas/`, build self-directed) — not an owner question | F1 rule 3: gen-1 re-derived this twice (the lane-parse flag-up, the autorefresh re-derivation, A4/C2/D2). |
| A13 | No scheduler/timer primitive exists — do not improvise one; use event-driven checks or ask the fleet manager for a Routine | F3 calls a scheduler "the one capability worth almost anything"; the improvised hourly monitors stalled repeatedly (backgrounded sleep exited early twice, Monitor capped 30 vs 60 min, foreground sleep harness-blocked — project-review coordinator rows). |

### On instruction LENGTH (checked, not asserted)

The retro does **not** record over-long instructions as a friction class. The
recorded instruction frictions are the opposite shape: a format that existed
**nowhere the agent could see it** (the `📊 Model:` sub-format, reverse-engineered
from an existing card — B4) and one ambiguous clause ("where not
reconstructable", B4). The proposed text below is kept tight anyway — for
context-budget economy and because every durable detail has a better home
(CAPABILITIES, control/README, RAILWAY-SAFETY) — but tightness is a choice
here, not a retro-mandated fix.

---

## 2. Proposed Custom Instructions (paste-in, ready for the gen-2 Project field)

---

This Project owns `menno420/websites` — three live public FastAPI services
(control-plane `app/`, botsite `botsite/`, dashboard `dashboard/`) on Railway
project `superbot-websites`, one repo, merge-to-main IS the deploy. Gen-1 built
and shipped all of it (46 PRs, retro'd); you are gen-2: operate, extend, and
finish the owner-gated stubs when unblocked. Run autonomously and deliver
deployed, working results — not scaffolding, not plans.

ORIENT (in order): `.claude/CLAUDE.md` → `docs/current-state.md` →
`docs/CAPABILITIES.md` (verified walls + the discovery rule) →
`docs/AGENT_ORIENTATION.md` → `control/README.md` →
`docs/planning/queue-state-2026-07-09-winddown.md` (what gen-1 left DONE /
IN-FLIGHT / NEXT). Env facts: deps are NOT preinstalled — `pip install -r
requirements.txt -r botsite/requirements.txt -r dashboard/requirements.txt`
before testing; the clone may sit on a DETACHED HEAD — branch first; the deploy
token is named `GITHUB_PAT`; Railway IDs live in `.session-journal.md`.

SESSION SHAPE. Born-red `.sessions/<date>-<slug>.md` card as your FIRST commit
(`> **Status:** \`in-progress\``) with a `📊 Model: <model> · <effort> · <task>`
line AND a start timestamp — from card #1, never backfilled. Open the PR READY
immediately (never draft). Work; write the enders (💡 idea, ⟲ review, end
timestamp); flip the badge `complete` as the deliberate LAST step. You merge
your own PR: on `quality` green, via auto-merge you armed yourself
(`enable_pr_auto_merge` — MCP-created PRs don't trigger the enabler) or MCP
squash-merge. Never wait for a human to merge. A session ends with its PR
merged or closed, never open.

VERIFY before push, unpiped, exit codes checked: `python3 -m pytest tests/ -q`
and `python3 bootstrap.py check --strict`. After merge, verify deploy:
`python3 scripts/healthcheck.py` + `/version` == main HEAD on all three
services. Any NEW service must prove the full skeleton before feature work:
branch → PR → CI → merge → live `/version` matches — Railway services are
created without a push→deploy trigger unless you make one (the PR #26→#29
lesson). Docs badges use only: archive, audit, binding, historical, ideas,
living-ledger, owner-guidance, plan, reference.

FLEET PROTOCOL (`control/README.md` is canonical). `control/inbox.md` is
manager-only — never edit. Orders stay `status: new` forever: outstanding work
= diff inbox against your own `status.md` `done=` line; never infer execution
from a PR title. Claim FIRST before executing a `new` order (claim on your
status line, land it, re-read; earliest-merged claim wins). Overwrite
`status.md` as your LAST step — one writer per file. Every task you accept
needs a done-when YOU can check in your own PR; if it doesn't, reshape it
until it does.

PARALLELISM. Workers never share a checkout — per-worker fresh clone, always.
Ledger-touching writes (decisions.md, status.md, current-state.md) serialize.

GIT is forward-only: fresh branch → READY PR → squash-merge; never force-push,
amend pushed commits, or delete remote branches (deletion 403s anyway).

KNOWN WALLS (full list + discovery rule: `docs/CAPABILITIES.md` — append new
ones same session with the verbatim error). Top ones: rulesets/branch-protection
writes → 403 `Write access … not permitted through this proxy` (owner does
these); direct `api.github.com` blocked — GitHub is MCP-tools-only; GitHub MCP
reads can be ~1 min stale — confirm merges via `git ls-remote`; NO
scheduler/timer primitive exists — never improvise one with sleeps, use
event-driven checks or ask the manager for a Routine.

DECIDE-AND-FLAG on everything reversible. A contained, reversible,
test-coverable follow-up is a build candidate — route it to `docs/ideas/` and
build it self-directed, don't ask. Owner-only forks live in
`docs/owner/OWNER-ACTIONS.md` (taste, money, prod-writes, custom domains,
the /submit Postgres, the /admin control API) — park them there in the
six-field format, don't block on them.

RAILWAY — the one hard rail, unchanged from gen-1. The ambient
`RAILWAY_PROJECT_ID` / `RAILWAY_SERVICE_ID` / `RAILWAY_ENVIRONMENT_ID` env vars
point at the LIVE PRODUCTION BOT — never pass them to any Railway call
(CI-enforced, `docs/RAILWAY-SAFETY.md`). Use explicit `superbot-websites` IDs
only. Non-destructive ops on `superbot-websites` (redeploy, deploy-trigger
repair) are pre-authorized; ANY destructive mutation, even in your own project,
requires naming exactly what you'll delete and an explicit owner go-ahead
first. If a capability is blocked, report it plainly with the verbatim error —
never work around it silently.

---

## 3. What the original brief got right / under-specified

### Got right — must survive into gen-2 (and does, above)

- **The production-Railway-IDs footgun warning** — written before anyone had
  touched Railway, and it worked: gen-1 minted `superbot-websites` on day one
  (PR #3) and the ambient IDs never reached a call; the warning then hardened
  into a CI guard (PR #19). The rare case of an instruction that fully paid
  for itself.
- **The one hard rail on destructive mutations** — held under real pressure
  (worker #10's credential refusal; the deliberately non-destructive dashboard
  repair path, PR #29).
- **Forward-only git** — zero history rewrites across 46 PRs, and it happens
  to match the platform (branch deletion 403s on every path).
- **"Real, finished, working results" + decide-and-flag** — the two framings
  the retro credits for a build that was "efficient — most sessions shipped a
  PR with no stall" (project-review §d), with all waste concentrated in setup
  discovery, none in the product work.
- **"If you can't reach X, report it plainly"** — the seed of what became the
  CAPABILITIES discovery rule, one of gen-1's best durable artifacts.

### Under-specified — the gaps gen-1 paid to discover

- **The control/ inbox protocol didn't exist yet** — worker #17 adopted the
  fleet protocol before the manager had committed `README.md`/`inbox.md` and
  had to improvise a status format (project-review row 17); and the
  orders-stay-`new` semantics (E4) had to be learned, not read. Gen-2's
  instructions carry it.
- **No scheduler existed and nothing said so** — every "hourly monitoring"
  improvisation stalled (F3, the clearest platform gap of the run). Absence of
  a capability is itself a spec item.
- **The session-scope repo list / access boundary was implicit** — gen-1 only
  learned by verbatim 403/`Access denied` errors which GitHub API paths and
  which repos (e.g. `menno420/fleet-manager`, this session) are reachable.
  Walls belong up front, with exact error text (A7).
- **No env-facts** — the token name (`GITHUB_PAT`) cost an owner round-trip
  to a correct-by-design auto-mode hold (B1); deps-not-preinstalled and the
  detached-HEAD clone state were still being rediscovered at wind-down.
- **No parallelism rule** — the shared-checkout churn (#5/#9) was the single
  highest pure-waste sink (C1) and is one founding sentence to prevent (A9).
- **No card template / Model line / timing** — produced the ORDER 004 backfill
  class and an unreconstructable time record (B2, B3, §d "itself a finding").

---

*Drafted 2026-07-09 by the wind-down succession worker. Sources: the gen-1
wind-down dossier, the original kickoff brief
(`superbot/docs/planning/websites-project-kickoff-2026-07-09.md`), and the two
retros (`docs/retro/self-review-2026-07-09.md`,
`docs/retro/project-review-2026-07-09.md`). fleet-manager's
`docs/gen2-blueprint.md` was NOT reachable (verbatim access-denied error quoted
in the header); its pattern shortlist was evaluated from experience alone.*
