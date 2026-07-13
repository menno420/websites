# websites — fleet cleanup audit (2026-07-13, EAP final night)

> **Status:** `historical`
>
> Read-only cross-repo cleanup pass, run as a complementary check alongside a
> live owner-driven fleet dispatch ("ORDER 045", 2026-07-13 ~22:00–22:30Z).
> This is an outside observer's snapshot, not a coordinator session — it does
> not carry authority over `control/status.md` or `control/inbox.md`, and it
> touched no open PR. Source code and the repo's own `docs/current-state.md`
> win over anything below if they disagree.

## Scope and method

- Repo: `menno420/websites`, cloned at local commit `95a9ef5` (main), then
  `git fetch origin main` re-synced to `8e9d4f3` mid-audit — main moved
  **twice** while this audit was in progress (see "Activity tonight" below).
- Read `.claude`-equivalent docs (`CONSTITUTION.md`, `docs/current-state.md`,
  `docs/AGENT_ORIENTATION.md`, `control/status.md`, `control/inbox.md`,
  `control/outbox.md`), the CI workflow files, and a sample of `docs/*.md`.
- Checked all open PRs live via the GitHub API (`pull_request_read`,
  `list_pull_requests`), and the last 30 completed `quality` workflow runs on
  `main` via the Actions API.
- **No PR was merged, closed, commented on, or edited.** Per this audit's
  explicit brief, every open PR in this repo was left untouched regardless of
  its individual mergeability, because the repo is under live, active
  coordinator work tonight (evidence below).

## What this repo is

`websites` is the menno420 estate's consolidated web-properties repo: one
repo, four independent server-rendered FastAPI services that share code but
never a running process, each with its own `Dockerfile` + `requirements.txt`
+ Railway service:

- **control-plane** (`app/`) — a public fleet readiness board + journal
  browser over `superbot`, `superbot-next`, `substrate-kit`, and `websites`
  itself, built live from the GitHub API; a password-gated `/owner` area
  exposes the un-masked secret list and privileged actions (cache refresh,
  CI re-run).
- **botsite** (`botsite/`) — the public marketing/reference site for the bot.
- **dashboard** (`dashboard/`) — public read-only oversight of the bot's own
  inventory (commands/settings/access/env/ideas/bugs); the live-bot control
  panel is a deliberate dry-run stub.
- **review** (`review/`) — a program-review site built for Anthropic EAP
  reviewers: process/growth/successes/problems pages, a per-repo fleet index,
  continuous-review editions + an Atom feed, and an evidence-backed
  questionnaire/questions ledger. Rendered server-side from committed JSON
  mirrors (`review/data/*.json`) baked by a scheduled `review-bake` GitHub
  Actions workflow; read-only and network-free at runtime.

It is the sibling rebuild track to `menno420/superbot-next`, built on the
same `substrate-kit` foundation (vendored `bootstrap.py`, currently kit
`v1.15.0` per `substrate.config.json`). It uses a git-file-based
fleet-coordination protocol: `control/status.md` (own heartbeat, one
writer), `control/inbox.md` (append-only orders from the fleet manager /
owner), `control/outbox.md` (append-only reports back to the manager), and
`control/claims/*.md` (per-branch work claims, deleted at session close —
same pattern documented in `superbot`'s `docs/owner/claims/README.md`).

## Structure

```
app/            control-plane FastAPI service (routes, readiness.py, journal.py, github.py client, templates)
botsite/        public marketing/reference site (+ tests/, data/)
dashboard/      public dev dashboard (+ tests/, data)
review/         Anthropic EAP review site (+ tests/, data/*.json baked mirrors)
bootstrap.py    vendored substrate-kit CLI (828 KB — kit-owned, not hand-edited)
control/        fleet-coordination git-file bus (status/inbox/outbox/claims)
docs/           ~21 top-level docs + owner/, ideas/, planning/, plans/, project/, retro/, specs/, succession/
.sessions/      184 per-session close-out cards (newest 2026-07-13)
tests/          top-level test suite; each service also has its own tests/
```

98 `test_*.py` files exist under `tests/` + the three per-service `tests/`
dirs combined; the `quality` workflow runs all four suites in one pytest
invocation (`tests/ botsite/tests dashboard/tests review/tests`).

## CI setup and health

Five workflows in `.github/workflows/`:

- **`quality.yml`** — the required status check (`quality`) on every PR and
  push to `main`. Runs on Python 3.12. Has a **control-only fast lane**: a
  diff touching only `control/**` short-circuits to green after two
  narrow gates (a `--status-only` heartbeat-grammar check, and an
  append-only + ORDER-grammar check on `control/inbox.md`) instead of the
  full suite — this is why heartbeat-only commits can land in seconds.
  Otherwise it installs all four services' `requirements.txt`, runs the
  kit's session-card gate (diff-aware, "born-red until flipped complete"),
  a Railway-ID ambient-secret guard, then the full pytest suite.
- **`auto-merge-enabler.yml`** (kit-owned) + **`host-automerge-extras.yml`**
  (host-owned companion, carrying a sweep job + a workflow-touching-PR
  disarm rail) — together arm GitHub-native squash auto-merge on non-draft
  `claude/*` PRs. The host file's own header documents a **known,
  unreconciled overlap**: the kit file arms on `pull_request` events without
  the workflow-touching-PR rail, so on a PR that touches
  `.github/workflows/**` the two files' arm/disarm can race. This is
  self-disclosed in-repo (`host-automerge-extras.yml` lines ~10–20), not a
  new finding, but worth flagging as still-open.
- **`healthcheck.yml`** — read-only liveness probe of the four live Railway
  URLs + a fleet-manifest parse smoke check, every 6 hours; not a required
  check, notifies via failed-workflow email only.
- **`review-bake.yml`** — scheduled data refresh for the review site; not
  inspected in depth this pass.

**Health, from the live API (last 30 completed `quality` runs on `main`,
sampled via `actions_list`):** 30/30 `conclusion: success`, 0 failures in
the sample — spanning `2026-07-11T19:30Z` → `2026-07-13T11:09Z`. The repo's
own heartbeat (`control/status.md`, live at `updated: 2026-07-13T22:46:00Z`
at write time) separately self-reports one brief red window **tonight**,
between commit `f47f7ce` (`#307`) and its own commit (`#310`): `#307`
apparently broke the heartbeat field grammar that `tests/test_own_heartbeat.py`
asserts, and `#310` restored it. This was **found and fixed by the repo's
own active session in real time during this audit**, not something this
audit needed to act on — cited here only as evidence of live self-correction
and as a CI-health data point (a required-check regression did briefly
land, however briefly, which the healthcheck/quality design is meant to
catch and did catch).

## Doc quality

Generally strong and unusually self-aware for an autonomous-agent repo:
`docs/current-state.md` (6,071 words — near-hugging its own declared 7,000-word
orientation budget in `substrate.config.json`) is kept as a dated, explicitly
"verify against live source" ledger rather than a claimed-authoritative one;
`docs/AGENT_ORIENTATION.md` is a tight task router; `docs/CAPABILITIES.md`
exists specifically to record verified walls instead of re-discovering them
every session; `docs/owner/OWNER-ACTIONS.md` uses a consistent six-field
ask format. The `control/status.md` heartbeat is dense but genuinely live —
it was rewritten twice during the ~40 minutes of this audit.

One structural gap: `project.index.json` (the `AgentContextPack` manifest
index referenced by `bootstrap.py`) still contains only the generator's
placeholder entry —

```json
"areas": [{"name": "example-area", "folio": "", "binding_docs": [], "source_roots": [], "do_not_create": [], "gates": [], "verification": []}]
```

— i.e. it has never been filled in with this project's real areas (control-plane / botsite / dashboard / review), despite the repo having four
well-documented service areas that would be natural entries. Not causing any
visible failure (nothing in the sampled CI or docs currently depends on it
being populated), but it is dead scaffolding that will mislead a future
session into thinking the AgentContextPack generator is either unused or
broken. `docs/AGENT_ORIENTATION.md` fills the same "which docs for which
task" role by hand instead, so this looks like an adopted-but-never-finished
kit feature rather than a broken one.

## Open PRs found — all left open, none touched

**9 open PRs at first check, 8 by the time of the final check** (PR #308
merged as `8e9d4f3` — timestamp `2026-07-13T22:55:45Z`, essentially the same
minute this audit's live-state check ran). This alone is conclusive evidence
of active, live coordinator work in this repo tonight; combined with the
explicit repo-specific brief ("DO NOT TOUCH ANY OPEN PR IN THIS REPO"), no
merge/close/comment action was taken on any PR, independent of individual
mergeability.

| PR | Draft | State | Why left untouched |
|---|---|---|---|
| #308 | no | **merged during this audit** (`8e9d4f3`, 22:55:45Z) | Was open at audit start; merged itself via the repo's own auto-merge before any audit action was needed — direct, timestamped proof of live work. |
| #281 | no | open, `combined status: pending / total_count 0` | Coordinator's own session PR, explicitly held red by kit design ("Do not close; do not bypass the hold" in its own body); last updated `20:53:45Z`, ~2h before this audit's checks — inside the "likely live" window per the audit brief. Base SHA is far behind current `main`, consistent with an in-progress multi-hour session PR, not an abandoned one. |
| #300 | yes | open | Explicitly self-labeled "Owner-parked — do not merge... owner may close unread." |
| #280 | yes | open | Explicitly self-labeled "Safe to close" (owner-click). |
| #279 | yes | open | Explicitly self-labeled "Do-not-merge; owner may close unread." |
| #278 | yes | open | Explicitly self-labeled "Do-not-merge; owner may close unread." |
| #257 | yes | open | Explicitly frames a "keep or close" decision for a coordinator/owner — not a mechanical close candidate. |
| #249 | yes | open | Explicitly self-labeled "do not merge." |
| #245 | yes | open | Explicitly self-labeled "ratification park — do not merge." |

All seven drafts are the repo's own documented "lifeboat" convention: kit
auto-generated `.substrate/state.json` churn or auto-drafted session-card
stubs, rescued onto disposable branches before a hard-sync so nothing is
silently lost, deliberately never intended to merge. This matches what the
repo's own `control/outbox.md` (PROPOSAL entry, `2026-07-13T11:29Z`)
already flags as "the sitting's biggest time sink" and recommends a
standing worker-brief line to prevent at the source, rather than a repeated
per-PR cleanup. **Merged: 0. Closed-superseded: 0. Left open: 8/8 (with
reason above).** Nothing was flagged as newly "needs attention" beyond what
the repo already tracks in its own `control/status.md` open-PR line and
ORDER 027 blocked-list.

## Concrete inconsistencies / errors noticed

1. **Orphaned claim file.** `control/claims/2026-07-13-railway-placeholders.md`
   (added in commit `cedca1e`, PR #275) documents a claim for "ORDER 026
   Railway placeholders," but ORDER 026 is recorded as `done` in
   `control/status.md` (`orders: ... done=001-019,023-026`) and PR #275 is
   itself listed as merged/shipped in `docs/current-state.md`. Per this
   repo's own claim convention (one file per in-flight branch, deleted at
   session close — mirrored from `superbot`'s Q-0195 pattern), a claim for
   completed, merged work should have been deleted and was not. Low-risk
   (claims are advisory, not load-bearing for CI), but it is exactly the
   kind of "docs drift you can see" the fleet's own working agreement asks
   to fix on sight — noted here rather than fixed, per this audit's
   read-only brief.
2. **`project.index.json` unpopulated** — see Doc quality above; a real but
   low-severity inconsistency between an adopted kit feature and its actual
   configuration state.
3. **`docs/current-state.md` "In flight" section was stale relative to live
   PR/commit state at the start of this audit**, but the repo's own PR #308
   (merged mid-audit, `8e9d4f3`) was specifically a truing pass that fixed
   exactly this — by the time this audit's second live check ran, the
   ledger already matched reality (7 draft lifeboats, evening-wave PR range,
   current suite count). No independent action needed; noted only to record
   that the audit observed the self-correction happen in real time rather
   than having caused or missed it.
4. **`host-automerge-extras.yml` documents its own unreconciled overlap**
   with `auto-merge-enabler.yml` on workflow-touching PRs (see CI section) —
   self-disclosed as a known gap in the file's own header comment, not
   discovered by this audit, but still open as of the audit's read.

## Suggestions

1. **Centralize the "lifeboat/rescue PR" convention across the fleet.** This
   repo has independently invented (and documented, and is now proposing
   upstream) the same pattern — auto-drafted kit-state churn parked on a
   disposable draft PR rather than risking a denied `rm`. The repo's own
   `control/outbox.md` PROPOSAL (`2026-07-13T11:29Z`) already asks for this
   as a standing dispatch-brief line ("kit auto-draft session stubs go to
   your scratchpad — never commit or lifeboat them"). Worth promoting to a
   fleet-wide kit/dispatch-brief standard rather than each repo rediscovering
   it — it is the direct cause of 7 of this repo's 8 currently-open PRs.
2. **A one-line "claims are deleted on merge" CI check would catch the
   orphaned-claim class of drift for free.** `superbot` already runs
   `scripts/check_lane_overlap.py`; a cheap equivalent here (a `quality`
   step that fails if a `control/claims/*.md` file's referenced branch has
   already merged into `main`) would have caught finding #1 above
   automatically, at effectively zero runtime cost given the existing
   control-fast-lane infrastructure.
3. **Either populate `project.index.json` or remove/park it with a note.**
   As-is it is dead weight that looks unfinished to the next reader; a
   5-minute fill-in (four areas: control-plane/botsite/dashboard/review,
   pointing at their existing `docs/site.md` / `docs/botsite.md` /
   `docs/dashboard.md` / `review/README.md` folios) would make it either
   useful or honestly retired.
4. **Risk flag, not a defect:** the `host-automerge-extras.yml` /
   `auto-merge-enabler.yml` overlap on workflow-touching PRs is the one spot
   in this repo's CI setup where a race is self-documented and still open.
   It is low-probability (requires a PR that both touches
   `.github/workflows/**` and lands in the exact window both jobs run), but
   worth a real reconciliation pass rather than living as a permanent
   "known overlap" comment, especially since this repo already has three
   overlapping automerge files as its footprint keeps growing.

## Activity tonight

**ACTIVE — live, hands-off.** Directly observed: PR #308 merged to `main` at
`2026-07-13T22:55:45Z`, in the same minute this audit's live-state re-check
ran (`date -u` read `22:55:44Z` one command earlier); `control/status.md`
carries `updated: 2026-07-13T22:46:00Z` (9 minutes before this audit's read)
and describes "ORDER 027 in progress (coordinator session 12)"; `main`
advanced from `95a9ef5` → `8e9d4f3` (and further, to at least `0ea4b6c` /
`#310`) while this audit was running. This repo needed zero redispatch — it
is already mid-execution on an owner-relayed EAP final-night worklist
(`control/inbox.md` ORDER 027, itself a relay of fleet-manager "ORDER 045").
This audit is therefore purely observational for this repo tonight.

## Notes

- No repository control-bus files were modified by this audit
  (`control/status.md`, `control/inbox.md`, `control/outbox.md`,
  `control/claims/*` were read-only for this session).
- This audit's own report and its PR are the only write this session made
  to `menno420/websites`.
- The audit's own report PR is intentionally **not self-merged** — left
  open for the repo's existing auto-merge convention (`quality` green on a
  `claude/*` branch) or a human to land, per this task's explicit
  instruction.
