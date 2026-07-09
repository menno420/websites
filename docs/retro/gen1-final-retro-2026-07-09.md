# websites — gen-1 final retrospective (2026-07-09)

> **Status:** `historical` — the closing retrospective of the gen-1 lane of
> `menno420/websites`, written at wind-down (2026-07-09 UTC) by the wind-down
> session. This document **aggregates** the retro record rather than
> re-deriving it — the primary payloads live in
> `docs/retro/self-review-2026-07-09.md` (the ORDER 003 question-by-question
> answers), `docs/retro/project-review-2026-07-09.md` (the full 29-subagent
> audit with stall classes and redesign rules F1–F4), and
> `docs/owner/project-retrospective-2026-07-09.md` (the mid-build
> retrospective, PR #17). Where those docs and this one disagree, they win;
> where source code and this doc disagree, source wins. Claims that exist only
> in cross-session briefings (never in this repo's committed record) are
> marked **[inherited]** and should be treated as record-only.

---

## 1. What this document is

The entire gen-1 lane ran on **one day — 2026-07-09 (UTC)**: 46 PRs (#1–#46),
of which #5, #9, and #22 closed unmerged (superseded/duplicate) and everything
else merged to `main`, shipping **three live public Railway services** —
control-plane, botsite, dashboard — in the fresh Railway project
`superbot-websites`, plus the `/fleet` heartbeat page over the whole
multi-repo fleet. This is the dated, final account of that day: what shipped
when, every recorded friction/failure class with exact error text where the
record has it, an honest account of how working in this Project felt, and a
pointer to what remains for the owner.

Reading route for a successor:

| Want | Read |
|---|---|
| Per-PR narrative of everything shipped | `docs/current-state.md` (Recently shipped) |
| Question-by-question honest self-review (A1–G3) | `docs/retro/self-review-2026-07-09.md` |
| Full agent audit + stall classes + redesign rules | `docs/retro/project-review-2026-07-09.md` |
| The mid-build story in the builder's own voice | `docs/owner/project-retrospective-2026-07-09.md` |
| Decision provenance (ledger entries 0001–0026) | `docs/decisions.md` |
| Verified capabilities & walls | `docs/CAPABILITIES.md` |
| What to do next (gen-2 queue) | `docs/planning/queue-state-2026-07-09-winddown.md` |
| Owner-gated forks (canonical) | `docs/owner/OWNER-ACTIONS.md` |

## 2. The life of the project — 46 PRs in one day

All timestamps 2026-07-09 UTC. Full per-PR detail is in
`docs/current-state.md`; the condensed milestones (matching
`docs/planning/queue-state-2026-07-09-winddown.md` § DONE) are:

**Seed + foundation (PRs #1–#6).** Intent commit `aec1cd5` → substrate-kit
adoption (#1, decisions 0001/0002) → the control-plane site built: readiness
board + journal browser over live GitHub data, TTL cache, HTTP Basic (#2,
decisions 0003/0004) → deployed to the fresh Railway project `superbot-websites`
(#3, decision 0005) → the dashboard/botsite rework plan (#4, decision 0007) → the
durable owner PAT wired as the control-plane service token, board fully live
(#6, decision 0006). PR #5 closed superseded — the first casualty of the
parallel-shared-checkout churn (§3.7).

**The two ported sites (PRs #7–#11).** Botsite rebuilt on this repo's
substrate and deployed as service `botsite` (#7, decision 0008) → dashboard rebuilt
and deployed as service `dashboard`, its live-bot-write `/admin` panel
deliberately stubbed (#8, decision 0009; #9 closed superseded) → stub hardening
(#10) → the `console.json` cross-repo shape contract (#11, decision 0010).

**Public pivot + owner overlay (PRs #12–#15).** Basic auth dropped from
control-plane + dashboard, the Actions-secrets cell masked to a count
(#12/#13, decision 0011; owner verbatim "Yes drop the auth") → the password-gated
`/owner` area: un-masked board, cache refresh, re-run failed CI (#14/#15,
decision 0012).

**Workflow hardening (PRs #16–#24).** Kit machinery actually engaged —
rendered docs, the `quality.yml` CI gate, bookkeeping backfill (#16,
decision 0013) → the mid-build retrospective (#17) → journal search + mobile (#18,
decision 0014) → the hardening batch: ambient-Railway-ID CI guard,
`scripts/healthcheck.py`, stub badges, `docs/owner/OWNER-ACTIONS.md` seeded
(#19/#20, decision 0015) — with **PR #19 itself auto-merging effectively EMPTY on
its born-red card**, the gate leak later root-caused → botsite content depth:
per-command detail pages + enriched changelog (#21, decision 0016) → the born-red
session-gate leak **fixed by adopting kit v1.0.0** with diff-aware
`--session-log` selection, proven both directions and regression-tested
(#24, decision 0017; `tests/test_born_red_session_gate.py`).

**Fleet-coordination era (PRs #23–#45).** The `control/` protocol adopted
(#23/#25; #22 closed duplicate) → ORDER 001: the deploy-state drift cell +
unauthenticated `/version` on all three services (#26–#28, decision 0018) — which
immediately caught the dashboard serving a stale sha; **root-caused: the
dashboard Railway service had no push→deploy trigger**, recreated (#29/#30) →
kit v1.2.0 via the §4.3 upgrade verb, `.claude/` wiring, the `control/**`
fast lane (#31, decision 0019) → `/activity` + `/ideas` cross-repo views (#33/#34,
decision 0020) → ORDER 002: the **`/fleet` heartbeat page** rendering all 10 fleet
lanes' `control/status*.md` on one screen (#35, decision 0021; the manager's
order-append was #32) → the `/fleet` lane set parsed **live** from superbot's
fleet-manifest, closing the hand-kept-list drift flag (#36, decision 0022) →
auto-refresh on `/` + `/fleet` + the quality.yml full-suite audit (#37,
decision 0023) → ORDERS 003+004: the gen-1 self-review retro + the 18-card
`📊 Model:` backfill + the full project review (#40, decision 0024; #38/#39 were
the *manager appending* those orders — a PR title is never evidence of
execution, see §3.14) → the `/activity.xml` Atom feed (#41, decision 0025) →
ORDER 006 latency ping-ack (#44; the ping was #43; #42 was the manager
appending ORDER 005) → kit v1.6.0 via the §4.3 release flow: capabilities
ledger, six-field owner-action format, claim ritual, `kit:` heartbeat line
(#45, decision 0026).

**Wind-down (PR #46).** Zero open PRs verified via the GitHub API; the
DONE / IN-FLIGHT / NEXT queue snapshot committed as
`docs/planning/queue-state-2026-07-09-winddown.md`; `control/status.md`
overwritten with the final gen-1 heartbeat (`orders: acked=…005,006
done=001,002,003,004,006` — **ORDER 005 is the one outstanding order**,
acked, unexecuted, unclaimed). PR #46 merged at 2026-07-09T20:03:22Z; zero
open PRs remained after the merge.

**End state.** Three public services, each repo-connected to
`menno420/websites@main` (merge IS the deploy), all exposing unauthenticated
`/healthz` + `/version`:

| Service | URL |
|---|---|
| control-plane (`app/`) | https://control-plane-production-abb0.up.railway.app |
| botsite (`botsite/`) | https://botsite-production-cfd7.up.railway.app |
| dashboard (`dashboard/`) | https://dashboard-production-a91b.up.railway.app |

Last live verification in the record: the project-review session saw all
three in sync at sha `6abe19f`; the kit-upgrade session re-verified
`/version` = `9ed43cf` = then-HEAD. **The wind-down session did not re-probe
the live URLs** (docs-only scope) — a successor should run
`python3 scripts/healthcheck.py` before trusting liveness. Ledgers at close:
26 decisions (ledger entries 0001–0026, append-only), 27 session cards in
`.sessions/`, `quality` a REQUIRED status check on `main` (owner-set — see
§3.1 for why the owner had to set it).

## 3. Every friction / failure class

Consolidated from `docs/retro/self-review-2026-07-09.md` § B1 (every error,
cost, preventability), `docs/retro/project-review-2026-07-09.md` § (b)
(per-agent stalls + the five cross-cutting classes), `docs/CAPABILITIES.md`
(verified walls), and this wind-down run's first-hand findings. Exact error
text is quoted where the record preserved it; **[inherited]** marks accounts
this wind-down session could not verify first-hand.

1. **Rulesets/branch-protection API blocked by the proxy** [inherited].
   Setting `quality` as a REQUIRED check via API returned 403 —
   `"Write access … not permitted through this proxy"` (the record itself
   preserves it partially elided; it matches the known fleet wall
   `Write access to this GitHub API path is not permitted through this
   proxy`). Could not self-complete; the owner set the ruleset by hand.
   Self-review B1; project-review row 14.

2. **Branch deletion → 403 on every path** [inherited, recorded wall].
   `docs/CAPABILITIES.md`: "403 on every path (git push `:branch` and API) →
   owner deletes by hand / enables 'Automatically delete head branches'."
   Related recorded wall: tag push / release create via git also 403s —
   workaround is the `workflow_dispatch` release path.

3. **Direct `api.github.com` HTTP blocked** [inherited, recorded wall].
   GitHub access is MCP-tools-only from sessions. Nuance discovered later
   (recorded in the CAPABILITIES append log): release-asset downloads over
   `github.com/<owner>/<repo>/releases/download/...` DO work through the
   proxy, and raw-content fetches don't need the API.

4. **GitHub MCP read tools served stale/cached PR + run state (~1 min lag)**
   [inherited]. Project-review stall (iii): "workers confirmed merges via
   `git ls-remote` instead." No verbatim error text exists — it is a silent
   staleness, not an error.

5. **No scheduler / timer primitive — the single clearest platform gap**
   [inherited]. "Hourly monitoring" could never be armed as a real timer:
   backgrounded sleeps exited early twice, Monitor capped at 30 min against a
   60-min need, foreground long sleeps were harness-blocked. Self-review F3
   calls it "the one capability I'd trade almost anything for."
   Project-review coordinator-worker rows; classed (b) platform.

6. **Auto-mode safety hold on the credential scan** [inherited]. A worker
   spawned to scan the environment for the deploy PAT was blocked by the
   auto-mode classifier as credential-exploration; resolved only when the
   owner named `GITHUB_PAT` directly. Cost: a full owner round-trip. The
   record classifies the block as correct by design, preventable by seeding
   an env-facts doc. Self-review B1/D1; project-review row 5.

7. **Parallel workers shared one git checkout/HEAD** [inherited]. Produced
   the superseded PRs **#5 and #9** — the clearest pure-waste of the run.
   Self-fixed by serializing ledger-touching workers + per-worker fresh
   clones. A related first attempt failed outright: git-worktree isolation
   was unavailable — "not in a git repository / no WorktreeCreate hooks" —
   forcing the fresh-clone fallback that then became the rule. Self-review
   A4/B1; project-review rows 6–8 and stall (ii).

8. **Dashboard Railway service had no push→deploy trigger** [inherited].
   The service silently served a stale sha with no error; the board's own
   deploy-state drift cell (ORDER 001, PR #26) surfaced it — the site caught
   its own drift — and PR #29 root-caused and recreated the trigger. Two
   sessions spent on a service-creation-time omission. Self-review B1/B3.

9. **Born-red session-gate leak (fixed)** [inherited]. PR #19 auto-merged
   effectively empty on its `in-progress` card alone — two engine holes
   (Status value never checked; card picked newest-by-mtime, which a fresh CI
   checkout flattens). Fixed by adopting kit v1.0.0 + the diff-aware
   `--session-log` step (PR #24, decision 0017), regression-tested in
   `tests/test_born_red_session_gate.py`.

10. **Mtime-fallback false-red (fixed)** [inherited]. A card-less PR fell
    back to an arbitrary old card missing the required `📊 Model:` line, so
    PR #38 went red on an *unrelated* card. Closed by the ORDER 004 18-card
    backfill (PR #40; decision 0024). Lesson recorded in self-review B2/F2: ship a
    gate-tightening change with its grandfather step.

11. **Kit one-doc-per-decision `stamp` check reddened CI silently**
    [inherited] when a [D-NNNN] was cited in two docs. Real but
    easily-tripped guard; project-review stall (iv).

12. **GitHub Actions runner-allocation stall, ~24 min once** (PR #20)
    [inherited]. Pure infra backlog; no agent action possible.

13. **Cross-session scratchpad unreachable** [inherited]. A worker verifying
    the dashboard was blocked because the credentials file lived in another
    session's per-session scratchpad — correct secret-handling, real
    friction. Project-review row "Verify dashboard deployment live".

14. **Orders stay `status: new` forever — a PR title is never evidence of
    execution** [inherited, then confirmed structurally first-hand]. The
    manager never flips an order's status; a waking session must diff
    `control/inbox.md` against its own `control/status.md` `done=` line.
    PRs #38/#39/#42/#43 were the manager *appending* orders; their merge
    titles read like executions (e.g. #42: "ORDER 005: owner-queue page
    (/queue) + environments page (/environments)") while `/queue` 404'd on
    the live deploy. Self-review E1/E4 names this the thing a fresh session
    would misunderstand first.

15. **Self-merge classifier & GraphQL quota** [inherited, recorded walls].
    `docs/CAPABILITIES.md`: sessions can be refused merging owner-gated PRs
    while other capabilities work — and the boundary differs by session kind
    (a child session was refused where a coordinator was not); GraphQL quota
    is tight — prefer REST-backed MCP tools.

16. **Degraded board cells from the unset/limited control-plane
    `GITHUB_TOKEN`** [inherited, recorded wall]. Live board renders
    `unknown (token lacks admin scope)` / `unknown (needs push-scope token)`
    — honest degradation, unfixable agent-side (owner-held Railway variable;
    the §5 PAT click resolves it).

17. **`send_message: tool is not enabled for this organization`**
    [inherited — from the wind-down coordinator briefing ONLY]. Cross-session
    messaging is disabled for this organization; per the briefing this is
    what killed the predecessor session's relay and why the wind-down runs in
    a successor session. **This string appears nowhere in the repo's own
    committed record** (a grep for `send_message` returns nothing) — it is
    recorded here so the wall survives, but it has no first-hand or in-repo
    confirmation.

18. **Pipe-swallows-exit-code trap** [inherited — fleet-wide, no incident
    recorded in THIS repo]. Piping a checker (`bootstrap check | tail`) masks
    a nonzero exit. The repo's convention already defends against it: run
    verification unpiped and check `$?` (the wind-down session did exactly
    that: pytest exit 0, `check --strict` exit 0).

19. **First-hand, this wind-down run** (2026-07-09, docs-only session):
    - Dependencies are not preinstalled on a fresh container:
      `python3 -m pytest` → `/usr/local/bin/python3: No module named pytest`.
      Fix: `pip install -r requirements.txt -r botsite/requirements.txt
      -r dashboard/requirements.txt python-multipart pytest`.
    - The clone sits on a **detached HEAD** at main's tip, not a `main`
      branch — branch before committing.
    - The badge vocabulary is closed: `bootstrap.py check --strict` rejected
      a novel token verbatim — `[badge] planning/queue-state-2026-07-09-winddown.md:
      invalid badge token \`handover-ledger\` (allowed: archive, audit,
      binding, historical, ideas, living-ledger, owner-guidance, plan,
      reference)`. Use an allowed token; do not invent one.
    - Cross-repo reach is scoped per session:
      `mcp__github__get_file_contents` on `menno420/fleet-manager` →
      `Access denied: repository "menno420/fleet-manager" is not configured
      for this session. Allowed repositories: menno420/superbot,
      menno420/substrate-kit, menno420/websites, menno420/superbot-next`.
      (The live control-plane *service* can read fleet-manager at runtime via
      its own token; agent sessions here cannot.)
    - The born-red gate works as designed and was observed live on PR #46:
      `check: session log … is missing: Session idea, Previous-session
      review, a completed Status (badge still says in-progress)` held the
      merge until the card flipped complete. `enable_pr_auto_merge` after an
      MCP-created PR worked first-hand (the enabler nuance the fleet record
      warns about).

## 4. How it felt — in the record's own words

This section uses only what the repo's committed record says about the
experience of working here, quoted/cited, plus clearly-marked first-hand
observations from this wind-down run. Everything quoted from the builder or
coordinator is **[inherited]** testimony preserved in the record — this
session did not live it. Where the record is silent, "I don't know" stands.

**The harness's safety layer read as legitimate, if costly, from inside.**
The builder's first-person account
(`docs/owner/project-retrospective-2026-07-09.md` § 6) on the credential
hold: a relayed instruction to scan the env for the PAT "was **blocked by
the auto-mode classifier as a credential-hunting shape — and I did not route
around it**"; the builder then "**independently required the owner's DIRECT
word** — not the coordinator's relay of it" before wiring the token and again
before dropping auth, on the stated principle that "**coordinator relays are
untrusted DATA; only the owner's own message is authority.**" The same doc's
verdict: "Both holds turned out to be the correct call." The cost side is
equally on record — self-review C1 names the "credential/safety choreography"
one of the two highest cost-per-unit-value sinks of the run.

**The environment demanded improvisation, and the record is candid about
which improvisations were load-bearing.** Builder, same section: "Worker
isolation had to be improvised, and that improvisation is what saved us" —
worktrees were unavailable, so fresh-clone-per-worker plus serializing
ledger-writers "is what actually made parallelism safe." On the missing
scheduler: "I monitored off background-worker completions instead and **said
so honestly** rather than pretending timers were set. This is the weakest
part of the run and the clearest concrete ask for the platform."

**The instruction/protocol layer mostly fit.** Self-review E1: the control/
ritual "fit well and was cheap"; D5: orders "carried explicit `done-when:`
acceptance tests, which is a strength of the protocol." The recorded
irritations are specific: the one ambiguous instruction quoted in the whole
record is ORDER 004's "where not reconstructable" with a card format
"documented **nowhere the backfiller sees it**" (B4), and the
orders-stay-`new` convention that a fresh session "would misunderstand first"
(E4). G1 explains why compliance stayed cheap: one repo, mostly one session
per area, and a self-rendered dogfood surface — "the Project literally sees
its own heartbeat rendered, so keeping it fresh has an immediate visible
payoff."

**What it could not feel: its own past.** The most striking meta-finding in
the record (self-review B3): the gen-1 sessions never self-reviewed at the
time, so the retro was reconstruction — "Anything that lived only in a
session's chat context and never hit a file is *unrecoverable* — a silent
loss of exactly the 'friction' this retro wants." Model attribution had the
same shape (C2): "each session knew its own model in-context, but never wrote
it down." The honest attribution that survives: the BUILDER session
self-reports **claude-opus-4-8** (subagents inherit it, "not independently
confirmed"); the coordinator self-reports **claude-fable-5**; other spawned
sessions are "cannot determine" (project-review, Model note).

**The coordinator's own verdict on the working model** [inherited,
first-person, preserved in `docs/owner/project-retrospective-2026-07-09.md`
§ 7]: "The front-door model is genuinely working. … Net: managing multiple
repos changed from 'ask an agent and wait' to 'dispatch, verify
independently, relay once'."

**The owner's presence in the record** is brief and decisive — the record
preserves his verbatims: the unattended-run test ("make sure the plans will
be properly executed so I can review the results when I wake up, this will be
a good test to see how an unattended run produces finished products"), "I
think those passwords are a bit unnecessary" → "Yes drop the auth", and the
dependabot policy. The mid-build retrospective's § 5 records "Owner decision
latency was tiny — single-shot decisions executed within minutes of the
owner's word."

**First-hand, from this wind-down run** (the only part of this section this
session lived): the orientation chain works as advertised — `.claude/CLAUDE.md`
→ `docs/current-state.md` → `docs/CAPABILITIES.md` → the retro docs was
sufficient to reconstruct the whole lane without chat history, which is
itself the strongest evidence the "everything durable lives in the repo"
discipline paid off. The environment friction that remains is boot-time
(deps not preinstalled; detached HEAD; closed badge vocabulary — §3.19), all
cheap once known and all now recorded. What this session **cannot** speak to:
what any gen-1 session felt in the moment, whether the inherited model
attributions are right, or whether the live services are still healthy (not
re-probed). I don't know those things, and the record doesn't fully settle
them either.

## 5. Remaining owner actions — pointer, not a copy

The **canonical list is `docs/owner/OWNER-ACTIONS.md`** (6 open decision
forks + the decided items); the two *actionable clicks* are carried as
six-field ⚑ OWNER-ACTION blocks in `control/status.md`, with exact click
paths in `docs/retro/project-review-2026-07-09.md` § (e). In one line each:

**Actionable clicks (2):**
1. **Provision the botsite submissions Postgres** — railway.app →
   `superbot-websites` → New → Database → PostgreSQL → set `DATABASE_URL` on
   the `botsite` service (unblocks the moderated `/submit` intake, rework Q5).
2. **Mint a durable fine-grained GitHub PAT** scoped to menno420 repos
   (contents/actions read + actions:write) and set it as `GITHUB_TOKEN` on
   the control-plane service (un-degrades board cells; enables `/owner`
   re-run-CI).

**Decision forks (6, canonical wording in OWNER-ACTIONS.md #1–#6):**
dashboard `/admin` live-bot control vs keep-stub (Q4) · botsite `/submit`
provision vs keep-stub (Q5, pairs with click 1) · redeploy-from-browser
scoped deploy hook yes/no · custom domains (owner-deferred to cutover) ·
preserve v1 visual design vs the shipped `ds/` restyle (Q2) · OLD-site
cutover/retirement of superbot's `dashboard/` + `botsite/` go/no-go.
(Optional extra, project-review § (e) item 7: a public production-bot health
URL for a bot-liveness cell.)

**Already done by the owner:** the `quality` REQUIRED ruleset on `main`.

## 6. The redesign payload — where gen-2 starts

Deliberately not restated here: the founding rules F1–F4 (every card carries
its model line from card #1; parallel workers never share a checkout;
contained-reversible follow-ups are build candidates, not owner questions;
the ideal ≤10-bullet seed state) live in
`docs/retro/self-review-2026-07-09.md` § F, and the redo-ordering + honest
efficiency verdict in `docs/retro/project-review-2026-07-09.md` § (d). The
gen-2 work queue — ORDER 005 (`/queue` + `/environments`, acked, unexecuted,
**claim it first**), the manifest-parse smoke check, the card template, the
heartbeat enrichment, the idea backlog — is
`docs/planning/queue-state-2026-07-09-winddown.md` § NEXT.

The one-sentence verdict the record itself reaches (project-review § (d)):
"the *output* is strong and fully verified-live; the *inefficiency* was
almost entirely one-time discovery cost in isolation, credentials, and deploy
plumbing — all seed-fixable, none in the product work itself."

---

*Written 2026-07-09 (UTC) by the gen-1 wind-down session (self-report:
claude-fable-5 worker; not independently confirmed — the same attribution
limit the project-review's Model note applies to every session). Sources:
the documents named in §1, `docs/decisions.md` (entries 0001–0026),
`control/inbox.md` + `control/status.md`, the 27 `.sessions/` cards, git
history, and the wind-down dossier's live-API verifications (zero open PRs;
PR #46 merged 2026-07-09T20:03:22Z).*
