# Archive-ready — project-chat close-out capture (2026-07-11)

> **Status:** `historical` — written at the archiving of the project chat
> that directed this repo's 2026-07-10→11 run. Everything load-bearing that
> existed ONLY in that chat is either cited to its durable home at HEAD or
> captured here. Companion edits landed in the same PR:
> `docs/owner/OWNER-ACTIONS.md` (four six-field asks added) and
> `docs/ideas/` (merge-hold-at-HEAD idea). A fresh session should read
> §6 (resume pointer) first.

## 1 · Current true state (verified 2026-07-11 ~19:45Z)

Four independent server-rendered FastAPI services share this repo —
**control-plane** (`app/`), **botsite** (`botsite/`), **dashboard**
(`dashboard/`), **review** (`review/`). The first three are deployed on
Railway (project `superbot-websites`; deploy = merge to `main`;
`scripts/healthcheck.py` verifies the three live URLs); **review/ is merged
but NOT deployed** — its Railway service is a queued ⚑ owner action
(`docs/owner/OWNER-ACTIONS.md`). Since 2026-07-10T20:17Z, **86 PRs had
merged on the green required `quality` check by 19:40Z** (84 verified via
GitHub search `is:pr is:merged merged:>=2026-07-10T20:17:00Z` at 19:35Z,
plus #150/#145 minutes later; #151/#153 and this capture's own PRs land
after that count — the chat's working figure of "~50" undercounted; the
total includes control fast-lane claim/heartbeat PRs), landed by the
continuous-mode send_later chain (#64→#142 work slices + rescues), the
4-hourly routine wakes, and owner-directed sessions.

- **PR #141** (review-site expansion: fleet coverage for the registry's 19
  seats, scheduled stats-bake Action, continuous review editions + Atom
  feed, evidence-backed questionnaire, interaction hooks; 28 files,
  +2785/−25) is **open, READY, kept green-clean by an agent
  drift-watchdog** (update-branch + re-green loop — sibling merges
  repeatedly knock it to `mergeable_state: behind`: #143/#146 did, then
  #147/#148/#150/#145). It **awaits the OWNER's squash-merge** — the
  platform denies agent merges of PRs that add workflow files (it adds
  `.github/workflows/review-bake.yml`).
- **PR #145** (dashboard `/admin` dry-run bot-management UX +
  `docs/specs/bot-control-api-v1.md` contract) **merged 2026-07-11T19:40Z**
  (`40ecd76`).
- **PRs #147** (open_work NO-DIFF classification) and **#148**
  (consumer-first `pickup:` history parser) merged 19:2x–19:32Z; **#150**
  was the chain's catch-up heartbeat (control-only).
- **PR #151** (chain close-out: `docs/retro/continuous-mode-lessons-2026-07-11.md`)
  and **#153** (final heartbeat — chain PARKED) landed 19:42–19:45Z: the
  continuous-mode chain is parked, its transferable lessons durable.
- Corrections made against reality while writing this: PR count 86+ not
  ~50 (above; #151/#153 and this capture's own PRs land after the count);
  everything else in the chat's closing summary checked out.

## 2 · Owner rulings that existed only in chat (verbatim intent)

Recorded here so no future session has to guess:

- **(a) Review site = a standing channel, not a one-shot report.** The
  owner's expansion directive: the review site is for **continuous**
  reviews by Anthropic — including reviews outside the EAP and future
  EAPs — and must stay **appealing and easy to use so Anthropic keeps
  using it**; it should leave **room for interaction**, and carry an
  **agent-authored, evidence-backed questionnaire that agents keep
  updating from findings**. (The original one-shot directive is durable
  verbatim in `docs/current-state.md` § Recently shipped; the expansion
  intent shipped as PR #141's content but was stated only in chat — this
  paragraph is its durable record. Future sessions: keep publishing
  review editions per `review/README.md` once #141 lands.)
- **(b) Dashboard bot management: build to the credential wall, arm
  later.** The owner directed building the complete `/admin` management
  experience as an honest dry-run with **zero credentials present**;
  **arming it is deferred until the owner answers Q-0004** (where live
  bot control lives). Durable since #145: `docs/owner/OWNER-ACTIONS.md`
  Open row 1 + the three six-field asks,
  `docs/planning/dashboard-bot-management-readiness.md`,
  `docs/specs/bot-control-api-v1.md`.
- **(c) The owner personally merges workflow-file PRs.** Agents are
  platform-denied from merging any PR whose diff adds/edits
  `.github/workflows/**`; the owner ruled he performs those merge clicks
  himself (PR #141 is the standing instance). Previously recorded only on
  the volatile heartbeat (`control/status.md` is overwritten every wake) —
  this line is the durable record.

## 3 · Coordination lessons (what failed, what works)

- **Session-message merge holds FAIL against 4-hourly wakes.** The
  repo-wide hold protecting PR #141's green state was coordinated via
  messages between live sessions — but routine-fired wakes boot with no
  chat context: **#143 and #146 were merged mid-hold** by sessions that
  never saw the hold (evidence: PR #148's body records "#141 is now
  `mergeable_state: behind` — the #143/#146 merges by other sessions
  knocked it back"). The hold's WORKING side (build-and-hold ceremony)
  is durable in `docs/retro/continuous-mode-lessons-2026-07-11.md` §3/§5;
  this failure mode was chat-only. **Durable fix proposed:** announce
  holds in a file at HEAD that every wake's mandatory pull sees — a
  `control/claims/HOLD-<scope>.md` claim file (or a `hold:` line in
  `control/status.md`, whose phase line carried it late in the day).
  Captured as a routable idea: `docs/ideas/merge-hold-at-head-2026-07-11.md`.
- **The drift-watchdog pattern is the standing remedy for owner-click
  PRs.** A PR only the owner may merge goes `behind` every time a sibling
  merges; an agent session watching it (merge `origin/main` into the
  branch → re-green `quality` → repeat) keeps it one click away at all
  times. Proven on #141 all afternoon. Any session finding an owner-click
  PR behind/red should take the watchdog over (see §6).

## 4 · Consolidated ⚑ owner actions (all open, one list)

Canonical home: `docs/owner/OWNER-ACTIONS.md` (six-field asks). Status at
capture:

| # | Action | Six-field ask durable? |
|---|---|---|
| i | **Squash-merge PR #141** (update branch first if offered) | added by this capture |
| ii | **Railway New Service** — repo `menno420/websites`, Root Directory=`review`, branch `main` | already present (active ask) |
| iii | **One manual `review-bake` workflow run post-merge** (seeds `stats.json`) | added by this capture |
| iv | **Answer Q-0004** — where armed bot control lives | present since #145 |
| v | **Discord OAuth app + redirect URI** (after Q-0004) | present since #145 |
| vi | **Scoped control-API token + Railway env on the SEPARATE armed service** | present since #145 |
| vii | **Botsite submissions Postgres → `DATABASE_URL`** | added by this capture (click steps were in `docs/retro/self-review-2026-07-11.md` §2) |
| viii | **Durable `GITHUB_TOKEN` PAT on control-plane** — also unlocks live + private-repo stats for the review site's bake | added by this capture (steps in `docs/deployment.md` § owner TODO; wall in `docs/CAPABILITIES.md`) |

Also standing (click-level, from `docs/retro/self-review-2026-07-11.md`):
deleting stale remote branches (agents get 403 on branch deletion).

## 5 · Blocked on other projects (named debts)

(One-line roll-up also in `docs/retro/continuous-mode-lessons-2026-07-11.md`
§6; citations per debt below.)

- **superbot** must implement `docs/specs/bot-control-api-v1.md` (extend
  `disbot/control_api.py` to serve the v1 envelope) before any armed
  control panel can exist — see
  `docs/planning/dashboard-bot-management-readiness.md` § superbot-side.
- **fleet-manager** owes this lane:
  - a generated **`lanes.json`** data contract (today `/fleet` parses the
    `LANES` literal inside `scripts/gen_roster.py` — `docs/ideas/backlog.md`
    "Ask the manager for a generated lanes.json");
  - **review-queue rows** for websites **#67/#72/#75/#77/#81** (the >50
    runtime-line law — `.sessions/2026-07-10-orders-visibility.md`,
    `.sessions/2026-07-10-activity-repo-filter.md`);
  - the **`meta.md` deployed-line convention** in the `projects/` registry
    (`docs/ideas/backlog.md`);
  - adoption of the **pickup-latency persistence convention** (`pickup:
    <id> <mins>m` heartbeat-notes tokens — the consumer already shipped
    here as PR #148) and the **provenance-token conventions** (shared
    token list with the kit lane — `docs/ideas/backlog.md`).

## 6 · Resume pointer (fresh session, no chat context)

1. Read `control/status.md` (heartbeat + orders), then THIS note, then
   `docs/owner/OWNER-ACTIONS.md`.
2. **If PR #141 is still open:** take over the drift-watchdog — keep the
   branch updated onto main and `quality` green so the owner's click
   always lands; never merge it yourself (workflow files).
3. **After the owner merges #141:** verify the review Railway deploy once
   the service exists (ask ii) and that the first `review-bake` run
   landed (ask iii); then resume the normal ritual
   (`control/README.md`) — inbox orders, then backlog.

## 7 · Wake-reliability ledger (now durable — pointer + one addendum)

While this capture was in flight, PR #151 landed the full fired-session
ledger durably: **`docs/retro/continuous-mode-lessons-2026-07-11.md` §1**
(04:03Z stranded→rescued #98 · 08:00Z silent · 12:05Z stranded→relayed
#124 · 16:00Z silent; verdict: honest workers, unreliable landers).
Chat-only addendum that table omits: the **00:02Z fire was OK** — it
worked and landed normally, so the day's full record is five fires, 1
ok / 2 stranded-rescued / 2 silent. The **rescue/relay doctrine** (any
session may land another's green control-only work verbatim) is durable
in `control/README.md` § "Landing other sessions' control-only work",
written by **PR #99** (`d6b91c9`); earlier durable pieces:
`docs/retro/self-review-2026-07-11.md` §1,
`.sessions/2026-07-11-fastlane-control-gates.md`.

## 8 · Closing confirmation

**Nothing load-bearing remains chat-only.** Every ruling, ledger,
lesson, ask, and debt above is now either cited to a durable file at
HEAD or recorded in this note.
