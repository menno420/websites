# Fleet self-review — gen-1 retro answers (websites)

> **Status:** `complete` — answers to `docs/retro/QUESTIONS.md` by ID, per inbox
> ORDER 003. Honest over flattering; each claim tied to a PR/commit/file where
> possible; "I don't know / cannot determine" is used where it is the true answer.
> Authored by the 2026-07-09 project-self-review session (claude-opus-4-8) reviewing
> the whole gen-1 lane, not by each original session about itself — so answers about
> internal experience ("time spent", "what I figured out") are **reconstructed from
> the committed record** (session cards, decision ledger, PRs), not lived memory.
> That reconstruction limit is itself a finding — see B3 and E4.

## A. Work & correctness

**A1. Shipped to main vs. only on branches/drafts.**
Everything real shipped to `main`. 37 PRs merged (#1–#39, minus #5/#9/#22 which were
closed as superseded/duplicate — see B1). No abandoned drafts, no long-lived
branches: every session opened a PR and drove it to a terminal state (merge or
close), which is the Q-0103 rule. The only "gap" is by-design **stubs**, not
half-finished work: the dashboard `/admin` live-bot control panel
(`dashboard/templates/admin.html`) and the botsite `/submit` write path
(`botsite/templates/submit.html`) are deliberate, labeled, credential-free stubs
gated on owner decisions (OWNER-ACTIONS #1/#2). They are shipped *as stubs* on
purpose, not incomplete features.

**A2. Verified against an external oracle vs. only own tests.**
Strong on external verification for the deploy-bearing work. Live-run oracles used:
- Deploy of all three services confirmed by hitting the real Railway URLs
  (`/healthz` 200, `/version` sha) — `scripts/healthcheck.py`, re-run this session:
  all three services report sha `6abe19f` = current `main` HEAD, in sync.
- `/owner` auth behavior verified live post-deploy (401 without creds → 200 with,
  masking not regressed) — PR #15, recorded in `docs/deployment.md`.
- Public/no-secret-name posture verified against served HTML — PR #12/#14 tests
  assert a secret name is absent from the rendered board.
- The born-red gate leak was proven *empirically both directions*, not just
  asserted — `tests/test_born_red_session_gate.py` + the #19 incident (PR #24, [D-0017]).
- The `quality.yml` "is the suite actually running?" question was checked against
  **real GitHub Actions run logs** (run 29032059374 shows `117 passed`), not
  assumed — PR #37 / `.sessions/2026-07-09-monitoring-autorefresh.md`.
Only-own-tests (weaker oracle): the cross-repo `/activity` and `/ideas` views
(PR #33) and the `/fleet` manifest parse (PR #36) were verified by unit tests +
a local render, and `/fleet` was verified live, but the *content correctness*
(does every lane's status parse the way its author intended?) rests on the parser
tests, not a human reading every rendered lane.

**A3. Least confident piece + the check that would settle it.**
The `/fleet` manifest live-parse (PR #36, [D-0022]). It maps the manager's
`superbot/docs/eap/fleet-manifest.md` markdown table by header name and expands
rows into lanes. It was verified to yield "exactly the 10 lanes" *as the manifest
read on 2026-07-09* — but it is coupled to another Project's document format that
can change without notice. Concrete disproof check: a scheduled test (or the CI
gate) that fetches the live manifest and asserts the parsed lane set is non-empty
and every lane's `status_path` resolves — today a manifest reformat degrades to the
`config.FLEET_LANES` fallback (honest banner, [D-0022]), which is safe, but nothing
*alerts* that the live parse silently stopped working. That gap is real.

**A4. Built unnecessary / duplicated / already-existing-elsewhere.**
Two honest instances, both small:
- **Superseded work from parallel-checkout churn:** PRs #5 and #9 were closed as
  superseded because early parallel workers shared one git checkout/HEAD and
  collided (see B1/C1). That is duplicated effort that produced nothing — the
  clearest "unnecessary" cost of the gen-1 run.
- **Re-derivation over reuse:** the monitoring-autorefresh session (PR #37) *itself*
  noted in its `⟲` review that it re-derived "these pages should auto-refresh" from
  scratch rather than picking it off a backlog, because websites had no `docs/ideas/`
  shelf of its own — a near-miss duplication of thought, not code.
No case of rebuilding something that already existed in-repo unseen was found; the
repo was small enough (one session built each area) that blind duplication was rare.

## B. Errors & friction

**B1. Every error hit — cost, preventability.**
- **Auto-mode safety hold on credential scan** (wiring the GitHub PAT, PR #6 lead-up):
  a worker spawned to *scan the environment for the PAT* was blocked by the auto-mode
  classifier as credential-exploration. Resolved only when the owner named
  `GITHUB_PAT` directly. Cost: a full round-trip to the owner. Preventable by
  **setup** (a standing "the deploy token is named X" fact in the env/repo), not by
  the agent — and the block was correct by design. Classify: instructions/setup + by-design safety.
- **git-worktree isolation failed** (botsite build, PR #7 first attempt): "not in a
  git repository / no WorktreeCreate hooks" → relaunched with a per-worker fresh
  clone. Cost: one relaunch. Preventable by **setup** (don't assume worktree; default
  to fresh clone). Classify: platform limit + setup.
- **Parallel workers shared one checkout/HEAD** → superseded PRs #5, #9. Cost: two
  wasted PRs. Preventable by the agent/setup — self-corrected by serializing
  ledger-touching workers + giving each its own clone. Classify: setup, self-fixed.
- **Branch-protection / rulesets API blocked by the proxy** (kit-hygiene, PR #16):
  setting `quality` as a REQUIRED check via API returned 403 "Write access … not
  permitted through this proxy." Cost: could not self-complete; owner set the ruleset
  manually. Genuinely **external** (platform/proxy policy). Classify: platform.
- **Dashboard had no push→deploy trigger** (PR #29): the dashboard Railway service
  silently never auto-deployed while control-plane/botsite did. Cost: a
  deploy-lag hunt across two sessions (PR #26 surfaced the lag, #29 root-caused it).
  Preventable at **service-creation time** (create the trigger when you create the
  service). Classify: platform/config gap.
- **GitHub Actions runner-allocation stall ~24 min once** (PR #20): infra backlog.
  Cost: 24 min wall-clock, no agent action possible. Genuinely **external**. Classify: platform.
- **Kit one-doc-per-decision `stamp` check reddened CI silently** when a D-NNNN was
  cited in two docs. Cost: repeated small CI reds. Classify: a real but easily-tripped
  guard (kit-side/setup).

**B2. Figured out that was already documented elsewhere.**
The clearest case is the **Model-line requirement** itself: the kit v1.2.0 upgrade
(PR #31, [D-0019]) tightened the session gate to require a `📊 Model:` line, but
the 18 pre-upgrade cards were never backfilled — so PR #38 went born-red on an
*unrelated* old card via the mtime fallback, and the fix (ORDER 004, executed this
session) had to be re-discovered from a red CI run. It *should* have been shipped as
a grandfather step **inside the v1.2.0 upgrade PR** — where the person tightening the
gate is looking. (Relayed as kit-side worthiness per ORDER 004.)

**B3. Broke silently (no error, wrong result) — how discovered.**
- **Dashboard deploy silently stale:** it served an old sha with no error; the board's
  own **deploy-state drift cell** (ORDER 001, PR #26) is what surfaced it — the site
  caught its own drift, which is the intended payoff. Root cause (missing deploy
  trigger) then found in PR #29.
- **This retro's meta-silent-failure:** the gen-1 sessions did **not** self-review at
  the time; this document reconstructs their internal experience from the committed
  record. Anything that lived only in a session's chat context and never hit a file is
  *unrecoverable* — a silent loss of exactly the "friction" this retro wants. Discovered
  by trying to answer C1/C2 and finding no durable time-spent record exists (see E4).

**B4. Ambiguous/contradictory/missing instruction line, quoted.**
From `control/inbox.md` ORDER 004: *"18 pre-kit-v1.2.0 session cards … Backfill the
Model line on all 18 (value `unknown (pre-v1.2.0)` where not reconstructable)."* The
ambiguity: "where not reconstructable" leaves the model value to judgment, and the
`Model:` line's own sub-format (`<model> · <effort> · <task>`, per the six v1.2.0
cards) is documented **nowhere the backfiller sees it** — you learn it only by
grepping an existing card. Minor, but it is exactly the kind of format that should be
in a template, not reverse-engineered. (Resolved this session by reading an existing
card and using `claude-opus-4-8 (pre-v1.2.0 backfill; … not independently confirmed)`.)

## C. Efficiency

**C1. Rough % time split + biggest sink.**
Cannot determine precisely — no per-session time record was kept (see B3/E4). From
the committed evidence, the reconstructable shape is: building dominated (the three
sites + control-plane feature set are the bulk of 37 PRs), but the **highest
cost-per-unit-value** went to two things that produced little: (1) the
**credential/safety choreography** (the PAT scan hold + the dashboard-credential
relay refusal), and (2) the **parallel-checkout churn** that cost PRs #5/#9 and the
serialize-and-fresh-clone recovery. The single biggest *waste* sink was the parallel
git entanglement; the single biggest *blocked-waiting* sink was the improvised
monitoring (no scheduler primitive — see D3/F3).

**C2. Context rebuilt from scratch that should have been durable.**
The **session model attribution** — each session knew its own model in-context, but
never wrote it down (pre-v1.2.0), so this retro had to *reconstruct* it from the
spawn-config chain. And a **websites-local idea backlog**: the autorefresh idea was
re-derived (A4) because there was no `docs/ideas/` shelf for this repo — a durable
one-line idea file would have made it a pick-off-the-shelf.

**C3. Most / least value per minute.**
Most: the **deploy-state drift cell** (ORDER 001) and `scripts/healthcheck.py` — a
few lines that turn "is the live site actually the merged code?" from a manual guess
into a glanceable/scriptable fact, and they caught the real dashboard drift. Also the
**born-red gate fix** (PR #24) — high leverage, closed a whole class of empty merges.
Least: chasing the ~17s `quality` run as a *suspected* short-circuit (PR #37) — it
turned out to be genuinely fast, so the audit correctly changed nothing, but it was a
low-yield investigation relative to the reading it took.

**C4. Redo speed + biggest ordering change.**
Materially faster — most of the lost time was one-time discovery. Biggest **ordering**
changes, in order: (1) **per-worker fresh clones + serialized ledger writes from the
very first parallel spawn**, not after #5/#9 collided; (2) **create the Railway
push→deploy trigger at service-creation time** for every service, so the dashboard
lag never happens; (3) **name the deploy token in the repo/env at seed** so the PAT
scan is never attempted; (4) open **tiny status/doc PRs born-complete** (they carry no
runtime risk) instead of paying the born-red round-trip.

## D. Autonomy & owner input

**D1. Every owner-input stop — truly owner-only or unblockable?**
- **Name the deploy PAT** (PR #6 lead-up): *unblockable* by a pre-granted rule —
  "the service token is named `GITHUB_PAT`" is a fact, not a decision. Grant: a
  seed env-facts doc.
- **Relay the dashboard password** (worker declined on coordinator authority):
  *truly owner-only* — correct by-design refusal; the credential stayed in Railway.
- **Set `quality` as a REQUIRED check** (PR #16): *forced* owner-only only because the
  **proxy blocked the rulesets API** — otherwise the agent could have done it. Grant:
  a proxy-allowed branch-protection path, or the owner pre-setting the ruleset at seed.
- **The six OWNER-ACTIONS items** (Q4 /admin, Q5 /submit Postgres, custom domains,
  visual restyle vs preserve-v1, old-site cutover, redeploy hook): *truly owner-only* —
  taste, money, irreversible, or prod-write. Correctly parked, not blocked.

**D2. Routed up that should have been decide-and-flag.**
None of the six OWNER-ACTIONS items — those are genuinely owner-only. The one
borderline call was the *lane-set sync* (D-0021): it was flagged ⚑ to the owner as
"keep in sync by hand or parse live," then the **next self-directed session just built
the live parse** (PR #36, [D-0022]) under decide-and-flag. That is the correct
pattern; the mild miss is that it was flagged up first instead of being routed
straight to a `docs/ideas/` build candidate — a contained, reversible, test-coverable
follow-up should be a *build candidate*, not an owner question (this repo's own #37
`⟲` review named exactly this).

**D3. Took while unsure it was allowed.**
The **redeploy of the lagging dashboard** (pinned-SHA, non-destructive) and the
**recreation of the dashboard deploy trigger** (PR #29) were Railway operations on a
live service — taken because they were non-destructive and scoped to
`superbot-websites` (never the ambient production IDs, `docs/RAILWAY-SAFETY.md`). The
rule that makes this unambiguous already half-exists (the RAILWAY-SAFETY denylist);
what would have removed all doubt is an explicit written grant: *"non-destructive
redeploy/trigger ops on the `superbot-websites` project are pre-authorized; the
ambient production `RAILWAY_*_ID` vars are the only hard line."*

**D4. Smallest standing grant set for zero-human end-to-end.**
1. A seed **env-facts doc** naming the deploy token(s) and each service's Railway
   IDs (so no credential scan is ever attempted).
2. **Non-destructive Railway ops on `superbot-websites`** pre-authorized (redeploy,
   create/repair deploy trigger), ambient prod IDs the only hard line.
3. A **proxy-allowed branch-protection path** (or ruleset pre-set at seed) so CI
   gates are agent-configurable.
4. The six product/taste/money decisions in OWNER-ACTIONS stay owner-only — that
   set is correctly *not* grantable.

**D5. Always knew what "done" meant?**
Mostly yes — the orders carried explicit `done-when:` acceptance tests, which is a
strength of the protocol. Undefined edge: ORDER 004's "a card-less docs PR passes
quality" is a *future* condition the backfilling session can't fully prove in its own
PR (its PR adds a card), so "done" there means "the mtime-fallback check is green,"
which is a proxy — good enough, but not literally the stated test.

## E. Protocol & environment

**E1. Did the control/ ritual fit? Where did it cost / get skipped?**
It fit well and was cheap (see G1). One real friction: the ritual says "read inbox
FIRST" but the manager keeps executed orders at `status: new` (the Project reports
`done` only in its own `status.md`) — so a waking session must **diff the inbox
against its own last status** to know what's actually outstanding. This session hit
exactly that: ORDERS 003/004 read as `new` but had to be checked against
`status.md` (`done=001,002`) *and* against the git history (PRs #38/#39 were the
manager *appending* the orders, not executing them) to confirm they were genuinely
undone. Not a skip, but a non-obvious step that a first-time session could get wrong.

**E2. Environment missing at first boot.**
- **A scheduler / timer primitive** — the single clearest gap (see F3): "hourly
  monitoring" could not be armed as a real timer; it was improvised via
  background-worker completions and on-demand probes.
- **Named deploy credentials / Railway IDs** as env facts (drove the PAT-scan hold).
- **Cross-session shared scratch** for non-secret handoff — a worker verifying the
  dashboard was blocked because the credentials file lived in another session's
  per-session scratchpad, unreachable cross-session.

**E3. Repo missing at seed.**
- A **`.sessions/` card template** carrying the `📊 Model: <model> · <effort> · <task>`
  line from day one (its absence caused the ORDER 004 backfill and the B4 format
  reverse-engineering).
- A **`docs/ideas/` shelf for this repo** (drove the C2/A4 re-derivation).
- A **seed env-facts / RAILWAY-IDs doc** (drove the PAT-scan hold and the "unsure I'm
  allowed" Railway ops).
- The **`quality` ruleset pre-configured** (or a proxy-allowed path to set it).

**E4. What a fresh no-history session would misunderstand first + the one doc that prevents it.**
It would misunderstand the **inbox order status** — that `status: new` on an order
does NOT mean "not started" (the manager never flips it; the Project reports done in
its own `status.md`). A fresh session could re-execute a done order or, worse, treat
PRs #38/#39 (manager *appending* orders 003/004) as evidence those orders were
*executed*. The single doc that prevents it already exists and is good —
`control/README.md` — but it should state **explicitly**: *"an order stays `new`
forever; to find outstanding work, diff `inbox.md` against your own `status.md`
`done=` line, and never infer execution from a PR title."*

## F. Redesign (the payload)

**F1. Three founding rules that weren't in ours.**
1. **Every session writes its model + effort + task in its card, from card #1** — no
   grandfather backfills later (the ORDER 004 class of landmine).
2. **Parallel workers never share a checkout; ledger-touching writes serialize** —
   stated as a founding rule, not learned from PRs #5/#9 colliding.
3. **A contained, reversible, test-coverable follow-up is a build candidate, not an
   owner question** — route it to `docs/ideas/` and build it self-directed; only
   taste/money/irreversible forks go to the owner. (This repo re-derived this rule
   twice; it should be seeded.)

**F2. What the manager should have done differently.**
Little — the orders were well-scoped with explicit `done-when:` tests, right priority
(P1), and pointed at committed docs. Two refinements: (a) **ship gate-tightening
changes with their grandfather step** (the v1.2.0 Model-line requirement should have
carried the 18-card backfill, so ORDER 004 never needed to exist); (b) the retro
protocol would be higher-fidelity if sessions self-reviewed **at close**, not weeks
later in one reconstructing pass — the manager could require a one-line "friction
noted" ender per session so the retro is aggregation, not archaeology (see B3).

**F3. One capability I'd trade almost anything for.**
A **scheduler / `send_later` timer primitive.** Its absence is the single clearest
platform limitation of the whole run: "check the sites hourly" could never be armed
as a real recurring timer — it was improvised (backgrounded sleeps that exited early,
a 30-min Monitor cap against a 60-min need, on-demand probes). Event-driven monitoring
partly filled the gap, but a first-class timer would have made liveness monitoring
trivial and reliable.

**F4. Ideal seed state (≤10 bullets), if relaunched "built right."**
1. `.sessions/` **card template** with the `📊 Model:` line + ender checklist.
2. **Env-facts doc**: named deploy token(s), each Railway service ID, the ambient
   prod-ID hard line — at seed.
3. **`quality` ruleset pre-set** as a required check (or a proxy-allowed path to set it).
4. **Per-worker fresh-clone + serialized-ledger** discipline as a founding rule.
5. **Railway deploy trigger created with each service** (no post-hoc lag hunt).
6. A **scheduler primitive** for liveness monitoring.
7. A **`docs/ideas/` shelf** for self-directed backlog.
8. **Cross-session shared scratch** for non-secret handoff.
9. `control/README.md` stating the **"orders stay `new`; diff against your status"**
   rule (E4).
10. The three F1 rules in the founding instructions.

## G. Addendum — WEBSITES

**G1. What made compliance CHEAP — and which conditions are missing elsewhere.**
Compliance was cheap because: (a) **one repo, mostly one session per area** — low
parallel-collision surface after the #5/#9 fix, so the "one writer per file" rule was
nearly free; (b) the control/ files are **plain committed markdown** the Project both
writes and *dogfoods* on its own `/fleet` board — the Project literally sees its own
heartbeat rendered, so keeping it fresh has an immediate visible payoff; (c) the work
is **public read-only web surfaces** — few irreversible/prod-write forks, so
decide-and-flag covered almost everything. Conditions likely missing in other repos:
Projects that touch the **live production bot** (superbot) have real irreversible
forks and can't decide-and-flag as freely; repos with **many parallel sessions** pay
the collision cost this repo mostly escaped; and repos without a **self-rendered
dogfood surface** get no immediate feedback for keeping their heartbeat honest.

**G2. Is the born-red machinery sufficient, or is a class of empty/premature merges still open?**
The #19 empty-merge is closed for its exact shape — kit v1.0.0's checker fails a
born-red card under `--strict` and the diff-aware `--session-log` derivation stops a
stale `complete` card masking an `in-progress` one (PR #24, [D-0017], regression-tested).
But **one class was still open until this session**: the **mtime-fallback landmine** —
a PR that adds *no* card falls back to picking an arbitrary old card by mtime, and if
that card lacked the required `Model:` line the gate went red on an *unrelated* card
(this is what reddened PR #38). That is not an empty-*merge* leak (it fails *closed*,
which is safe) but it is a **false-red** class that the ORDER 004 backfill (this PR)
closes. Remaining theoretical gap: the control-fast-lane (`control/**`-only diffs
short-circuit green with no card) means a `control/`-only change is never card-gated —
intended (heartbeats), but worth stating as the one path that bypasses the card gate
by design.

**G3. What I wish heartbeats carried that they don't.**
- A **machine-readable outstanding-orders field** (`orders: acked=… done=… open=…`)
  so `/fleet` and a waking session can compute "what's left" without diffing inbox vs
  status vs git (the E1/E4 friction).
- A **model + session-count** per lane (which model is driving this lane right now),
  so the fleet page shows not just *how far* but *who/what* is running each lane.
- A **last-verified-live timestamp + deployed-sha** per lane (websites has this via its
  drift cell; other lanes' heartbeats don't carry it), so "green" means "verified live",
  not just "the session said so".
- A **structured `⚑ needs-owner` list** (id + one-line + where-it-lives) rather than
  free prose, so the owner-actions aggregate across the whole fleet automatically.
