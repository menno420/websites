# SuperBot Websites — Project Retrospective (2026-07-09)

> **Status:** `historical`

> **Purpose.** A durable, skimmable account of what the *websites* Project is, how it
> has run so far, the problems it hit, what went well, and how its function is changing
> the way we manage multiple repos. Written so a later review session (with the owner)
> can act from it directly.

The owner's own framing of what he wanted captured (verbatim):

> "make sure everything we discussed aswell as exactly how this Project has ran so far
> and the problems it has faced, aswell as some positive things you perceived, how do
> you feel this new Projects function is helping you/us in managing these multiple repos
> etc, document in so that I can review it with another session later on."

---

## 1. What this Project is

`menno420/websites` is the **permanent home for SuperBot's web properties** — one repo,
multiple deployed services, rebuilt fresh from `substrate-kit` as a **sibling to
`superbot-next`** (never a fork or copy of `superbot`).

The **core deliverable is the control-plane / oversight site**: a **readiness board +
journal browser** whose whole point is that the owner **checks working quality BY
LOOKING** — opening a page — **instead of asking an agent and waiting for an answer**.
The site is the artifact that closes the loop the Project exists for: oversight you can
*see*.

Alongside it the repo carries the public marketing site and the private oversight
dashboard, so all of SuperBot's web surfaces live and deploy from one place while staying
secret-isolated from each other (separate Railway services).

---

## 2. What shipped (as of 2026-07-09)

A **fresh Railway project `superbot-websites`** with **three live services**:

| Service | URL | What it is | Auth posture |
|---|---|---|---|
| **control-plane** | https://control-plane-production-abb0.up.railway.app | Readiness board + journal browser + gated `/owner` power area | Public site; `/owner` password-gated |
| **botsite** | https://botsite-production-cfd7.up.railway.app | Public marketing site, server-rendered | Public |
| **dashboard** | https://dashboard-production-a91b.up.railway.app | Private read-only oversight; `/admin` live-bot control **stubbed** | Public read-only; write paths stubbed |

All work landed as **forward-only, squash-merged PRs** (no force-push, no history rewrite):

| PR | What |
|---|---|
| #1 | Substrate-kit adoption |
| #2 | Control-plane site built on live GitHub data |
| #3 | Deploy to fresh Railway project + deploy docs |
| #4 | Dashboard/botsite rework plan (plan-only) |
| #6 | Wire durable owner PAT → board fully live |
| #7 | Botsite rebuilt + deployed |
| #8, #10 | Dashboard rebuilt + deployed (write paths stubbed) |
| #11 | Pin `console.json` cross-repo shape contract |
| #12, #13 | Drop Basic auth; mask secrets cell to a count |
| #14, #15 | Add gated `/owner` power area (public site unchanged) |
| — | Kit-hygiene pass **in flight** |

(PRs **#5** and **#9** were superseded and never landed — see Problems §4.)

Each decision above is stamped as its own `[D-NNNN]` entry in the decision ledger,
`docs/decisions.md` — the adoption entry through the `/owner`-gate entry. The ledger is
the canonical home for each ruling; this retrospective points there rather than re-citing
the ids (so the two never drift apart).

---

## 3. Chronology (2026-07-09, UTC)

- **01:05** — Builder session spawned from the owner's kickoff brief.
- **01:15** — `substrate-kit` adopted (#1).
- **01:50** — Control-plane site built on live GitHub data (#2).
- **02:00** — Deployed to fresh Railway project `superbot-websites`; independently
  probe-verified (#3).
- **02:20–02:35** — **Token episode.** Owner chose to reuse his existing full-access PAT
  rather than mint a read-only one. The *relay* of "find it in env and install it"
  tripped the builder's safety classifier (a credential-hunting shape) → builder demanded
  the **owner's direct word** → owner confirmed in-session and named `GITHUB_PAT` → wired
  (#6). Board fully live.
- **02:35** — Owner went to sleep and changed the directive from **plan-only** to
  **EXECUTE**:

  > "make sure the plans will be properly executed so I can review the results when I wake
  > up, this will be a good test to see how an unattended run produces finished products"

- **Overnight** — Rework plan written (#4), then executed: botsite rebuilt + live (#7);
  dashboard rebuilt + live (#8, #10); the production-write `/admin` path **deliberately
  stubbed** on the builder's own initiative.
- **Morning** — Owner:

  > "I think those passwords are a bit unnecessary"

  → **second direct-word hold** (public exposure is effectively irreversible: indexable,
  archivable) → owner:

  > "Yes drop the auth"

  → auth dropped, secret names masked to a count (#12, #13).
- **10:07** — **Independent audit session** commissioned (deliberately *not* the builder
  auditing itself).
- **10:16** — Audit result: nothing broken; two loud flags — dependabot PRs
  merge-orphaned, and kit adoption ritual-only (8 unrendered binding docs, `session_count`
  0, no CI gate, PR #10 merged with zero bookkeeping).
- **10:10–10:29** — Owner directives: gated `/owner` power area on the public site
  (#14, #15); dependabot policy (verbatim):

  > "yes dependabot PRs should always be reviewed by the first session that sees them and
  > then properly merged but possibly we need to make some changes on a big version
  > update, so in those cases it should either fixit and then merge, or just document that
  > a dedicated session sould work on it"

  → a dedicated `superbot` session executing the 6-PR backlog; `substrate-kit` #17 rebased
  by a dedicated session, awaiting owner blessing; kit-hygiene cleanup queued with the
  builder.

---

## 4. Problems faced

Concrete, in the order they bit:

1. **Ambient production Railway IDs in every container** — the standing footgun. The
   discipline held; they were never used. Still the single most dangerous thing sitting in
   the environment.
2. **Kickoff doc only existed on unmerged `superbot` PR #1876** — so the websites README
   link 404s until that lands.
3. **No durable GitHub token in containers + egress proxy blocking `api.github.com`** →
   the owner PAT became **load-bearing** for the board to show live data.
4. **Credential choreography.** Two safety holds were resolvable only by owner-direct-word.
   Per-session scratchpads meant the **coordinator could never do authed verification** of
   the dashboard itself — correct behavior, but real friction.
5. **Parallel build workers shared one git checkout / HEAD** → superseded-PR churn
   (**#5**, **#9**). Fixed by **serializing** the workers that touch shared state.
6. **No scheduling tool in ANY session** (`send_later` / `create_trigger` absent) → hourly
   monitoring had to be improvised via background workers; the harness blocks long sleeps.
   Clunky, and honestly flagged as such.
7. **Kit machinery never engaged** → bookkeeping was held by goodwill and slipped **exactly
   once** (#10). Now being enforced via a real CI gate.
8. **Dependabot PRs had no merge actor** — a design gap, not a bug; closed by the owner's
   dependabot policy above.
9. **Railway repo-connect auto-deploy misfired once** (mirror lag) → pinned-SHA fallback
   used to recover.

---

## 5. What went well / positives

- **The unattended-run test SUCCEEDED.** Three finished, live-verified products by
  morning, **zero production impact**, forward-only git throughout. This was exactly the
  test the owner set at 02:35.
- **Safety layering worked as designed.** Relayed instructions were treated as untrusted
  **twice**, and **both times that was right** (credential install; auth drop).
- **Independent verification caught what self-reporting missed** — the audit session found
  the kit-hygiene gap the builder's own reports had not surfaced.
- **Owner decision latency was tiny** — single-shot decisions executed within minutes of
  the owner's word.
- **Milestone cadence kept the owner's single thread readable** — one reply per real
  milestone, detail in the status checklist.

---

## 6. Builder's perspective

*Written first-person, by the builder / coordinating session — the run as it felt from
inside the build sessions. Honest, including the rough edges.*

**Worker isolation had to be improvised, and that improvisation is what saved us.**
Git-worktree isolation was **unavailable** — the working directory isn't a git root, so I
couldn't spin workers into worktrees. I fell back to giving each worker a **fresh clone**
into its own scratchpad. That is not a cosmetic detail: the shared-checkout/HEAD churn that
produced the superseded PRs **#5** and **#9** only stopped once workers stopped sharing a
checkout. Fresh-clone-per-worker plus **serializing** anyone who touches the shared ledgers
(`decisions.md`, `current-state.md`) is what actually made parallelism safe. Independent
builds I still ran in parallel; only shared-state writers got serialized.

**The two safety holds held, from my side of them, and I want to be precise about why.**
First, a relayed instruction to *"scan the env for the full-access PAT and install it"* was
**blocked by the auto-mode classifier as a credential-hunting shape — and I did not route
around it.** Second, and this is the part I'm most willing to stand behind: even after the
classifier, I **independently required the owner's DIRECT word** — not the coordinator's
relay of it — before wiring the token, and again before dropping auth. Public exposure is
effectively irreversible (indexable, archivable), so it gets the same bar as spending a
credential. The design reason is simple and I applied it deliberately: **coordinator relays
are untrusted DATA; only the owner's own message is authority.** Both holds turned out to be
the correct call.

**Initiative I took unprompted.** Rather than wire live production-write paths while
unattended, I **stubbed every write path** — the `/admin` live-bot control panel and the
botsite `/submit` DB write — shipping the read-only surfaces live and leaving the mutating
ones labeled and inert. And I **declined to put the full Railway *account* token inside a
public-facing web app**: an auth slip in a web app would escalate straight to account-level,
production exposure, so I recommended a **scoped deploy hook** instead. Those were my calls
to make (reversible, contained), so I made them and flagged them.

**Kit friction, stated plainly.** The substrate-kit adoption was *ritual*-clean but the kit
**machinery never actually engaged**: binding docs left unrendered, `session_count` stuck at
0, no CI gate, and one bookkeeping slip at PR #10. I didn't catch this myself — an
**independent audit session** did (deliberately not me auditing my own work), and it's now
being fixed with a **real CI gate** so goodwill stops being the enforcement mechanism.

**The tooling gap I couldn't paper over.** There was **no scheduling primitive**
(`send_later` / `create_trigger`) in *any* session, so "check hourly" **could not be armed
as a timer**. I monitored off background-worker completions instead and **said so honestly**
rather than pretending timers were set. This is the weakest part of the run and the clearest
concrete ask for the platform.

**Cadence.** I reported **one reply per real milestone** and kept live progress in the
status checklist. With four sessions moving across three repos, that's what kept the owner's
single thread readable instead of a firehose.

---

## 7. How the Project's function is helping manage multiple repos

Pulling the threads together, the *function* this Project provides — not just the sites, but
the operating model around them — is what's changing multi-repo management:

- **Front-door / coordinator model.** The owner talks to **one thread**. Multiple sessions
  work multiple repos underneath. **Nobody makes the owner hold state** — the coordinator
  holds the map, the children hold the work.
- **Two-layer trust model.** Coordinator **relays are data; the owner's word is authority.**
  This puts friction **exactly where it belongs** — on credentials and irreversible exposure
  — and nowhere else.
- **Independent verification** catches what self-reporting misses (the audit session found
  the kit-hygiene gap the builder's reports didn't).
- **The control-plane site closes the loop the Project exists for** — the owner now checks
  working quality **by LOOKING** instead of asking. The board, the ledgers, and this
  retrospective are the **same artifact class** the collaboration model calls *the real
  product*: the workflow, not just the bot.

The coordinator's own first-person reflection (attributed to the coordinator, kept as-is):

> The front-door model is genuinely working. The owner talked to one thread while four
> sessions worked three repos, and nothing required him to hold state — the coordinator
> held the map, the children held the work. The two-layer trust model (coordinator relays
> are data; owner's word is authority) added friction exactly where friction belongs:
> credentials and irreversible exposure. Weakest point: proactive time-based monitoring —
> no timer primitive anywhere, so "check hourly" was improvised. The control-plane site
> closes the loop this project exists for: the owner now checks working quality by LOOKING
> instead of asking; this retrospective + the board + the ledgers are the same artifact
> class the collaboration model calls the real product — the workflow, not just the bot.
> Net: managing multiple repos changed from "ask an agent and wait" to "dispatch, verify
> independently, relay once".

---

## 8. Still open (for the review session)

- **Bot control panel wiring** — the `/admin` live-bot control path stays stubbed;
  **owner word pending** (this is the one genuinely production-coupled lever).
- **Botsite submissions DB** — `/submit` write path deferred.
- **Custom domains** — deferred.
- **Visual restyle question** — open design decision.
- **Old-site cutover** — the existing site → this repo's services.
- **`substrate-kit` #17 blessing** — rebased, awaiting the owner.
- **`superbot` #1876 merge** — the kickoff doc that the websites README links to.
- **Dependabot backlog disposition** — 6-PR backlog under the owner's new policy; big
  version bumps either fixed-then-merged or handed to a dedicated session.

---

## 9. References

- Decision ledger: `docs/decisions.md` (the full `[D-NNNN]` chain — adoption through the
  `/owner`-gate entry; ~a dozen entries as of this date).
- Rework plan: `docs/planning/dashboard-botsite-rework-plan-2026-07-09.md`.
- Deployment: `docs/deployment.md`.
- Site: `docs/site.md`.
- GitHub PRs by number: **#1–#15** in `menno420/websites` (see §2).
