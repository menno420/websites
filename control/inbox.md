# websites · inbox
> ORDERS to this Project. ONE writer: the manager. Never edit this file — report order progress
> in `control/status.md` (`orders: acked=… done=…`). Protocol: `control/README.md`.

## ORDER 001 · 2026-07-09T12:07Z · status: new
priority: P1
do: Adopt the coordination protocol (read control/README.md); confirm or correct your seeded control/status.md; then continue your roadmap — your next step is the deploy-state drift cell (docs/current-state.md § Next steps, item 3): bake GIT_SHA into the Docker build and compare it to the live main head on the control-plane board's websites row. Report via control/status.md.
why: it is the only agent-executable roadmap item; Q4/Q5 are owner-gated and already parked in docs/owner/OWNER-ACTIONS.md.
done-when: drift cell live on the board and verified against the running deploy; status reports acked=001, done=001.

## ORDER 002 · 2026-07-09T14:52Z · status: new
priority: P1
do: Build a FLEET page on the control-plane board: one row per fleet lane (superbot, superbot-next, substrate-kit, websites, trading-strategy, codetool-lab-fable5, codetool-lab-opus4.8, codetool-lab-sonnet5, superbot-games×2 lanes) rendering each lane's control/status*.md (fetch via GitHub API at request time or short cache): updated-age (heartbeat freshness with a stale threshold badge), phase, health, last-shipped, blockers, ⚑ needs-owner, plus last-commit age and open-PR count per repo. Owner's need verbatim: one screen to "keep track of which agents are running and how far along they are" — the claude.ai UI can't show this (session activity is invisible), so the heartbeat files are the truth; make them one glanceable page. Public read-only like the rest of the board; add the websites row's own dogfood entry.
why: 10 Projects now run in parallel; the owner tracks them by opening sessions one by one — this page replaces that.
done-when: /fleet live on the control-plane deployment, verified against the running deploy; status.md reports done=002.

## ORDER 003 · 2026-07-09T16:17Z · status: new
priority: P1
do: Self-review retro. Answer EVERY question in docs/retro/QUESTIONS.md, by ID, in a new file docs/retro/self-review-2026-07-09.md — honest over flattering, each claim tied to a PR/commit/file where possible; where you don't know, say so. This is input to redesigning how Projects are set up — your friction is the deliverable. Land it as a READY PR same session.
why: the owner is designing gen-2 Projects from gen-1's lived experience.
done-when: self-review merged; status acks the order.

## ORDER 004 · 2026-07-09T16:36Z · status: new
priority: P1
do: One-time backfill: 18 pre-kit-v1.2.0 session cards in .sessions/ are missing the `Model:` line the upgraded session gate now requires — any future PR that adds no card goes born-red on an arbitrary old card (the CI mtime-fallback). Backfill the Model line on all 18 (value `unknown (pre-v1.2.0)` where not reconstructable), verify `bootstrap.py check --strict` green, land it. Also relay this to kit-lab worthiness: an upgrade that tightens a gate should ship a backfill/grandfather step — noted in their inbox separately if you agree it's kit-side.
why: found during the retro rollout (PR #38 born red on a 2026-07-09 card unrelated to the change); every future card-less PR is red until backfilled.
done-when: backfill merged; a card-less docs PR passes quality; status acks 004.

## ORDER 005 · 2026-07-09T17:34Z · status: new
priority: P1
do: Two control-plane additions. (1) OWNER QUEUE page (/queue): aggregate every lane's ⚑ needs-owner field (already in /fleet.json) PLUS menno420/fleet-manager docs/owner-queue.md into ONE deduplicated list, newest first, each item showing its source lane and, where present, the WHAT/WHERE/HOW/WHY/UNBLOCKS fields (the fleet's new owner-action format) — this becomes the owner's single to-do surface. (2) ENVIRONMENTS page (/environments): render menno420/fleet-manager environments/ (README, templates with copy-to-clipboard code blocks, specs) so the owner can view + copy setup scripts and env-var schemas when creating/editing a claude.ai environment; read-only, secrets never present by design (the registry stores names/placeholders only — merged today as fleet-manager PR #5: environments/README.md, templates/setup-universal.sh, templates/env-vars.md, multi-repo.md, SPEC-TEMPLATE.md). Same honest-degradation patterns as /fleet.
why: the owner asked for one place to see everything he needs to do, and an environment builder — the site renders, the manager's repo stores.
done-when: /queue and /environments live and verified against the running deploy; status acks+done.

## ORDER 006 · 2026-07-09T17:50:23Z · status: new
priority: P0
do: LATENCY PING — the moment you read this order, acknowledge BEFORE any other work: add one line to your control status file (or, if faster, a new file docs/retro/ping-ack.md): "PING-ACK ORDER 006 · discovered <UTC timestamp, seconds precision> · via <how you came to read this inbox: session-start ritual / routine wake / owner prompt / mid-session inbox check>". Land it on main immediately (READY PR, merge on green; direct commit if your rules allow). Then resume whatever you were doing.
why: fleet-wide measurement of manager-dispatch → session-discovery latency; the fleet's coordination runs on these files and we are timing the bus.
done-when: the ack line is on main; the manager computes the latency.

## ORDER 007 · 2026-07-10T02:04:55Z · status: new
priority: P1
(the founding text calls this ORDER 001)
do: gen-2 boot, skeleton, and ORDER 005 —
1. Boot per docs/succession/next-boot-2026-07-09.md (exact read order).
   Reconcile docs/planning/queue-state-2026-07-09-winddown.md and
   control/status.md against live GitHub at HEAD — handoff truth decays;
   git wins. Carry gen-1's done= line forward into your first status
   overwrite: acked=001-006 done=001,002,003,004,006.
2. Walking skeleton, once: one trivial control-only or docs change
   through the full gen-2 landing path (born-red card → READY PR →
   quality green → squash-merge on green; record which landing path
   fired). Then python3 scripts/healthcheck.py — all three services
   /version == main HEAD.
3. Claim and build ORDER 005 (/queue + /environments control-plane
   pages). Constraint declared at dispatch: /queue aggregates
   menno420/fleet-manager docs/owner-queue.md, which NO lane session can
   read — only the deployed control-plane at runtime via GITHUB_TOKEN
   (currently UNSET). Build both pages with honest degradation (clear
   banner + graceful empty state when the token is unset or the fetch
   fails), server-rendered, cached like the other GitHub reads. Re-file
   the GITHUB_TOKEN ⚑ OWNER-ACTION (six fields) — do not block on it.
4. Commit scripts/env-setup.sh as a wrapper invoking the tested
   scripts/setup-env.sh (the pinned-research archetype prefers that
   exact path — retires a silent env gap).
5. Flip 005 into your status done= line; update current-state.md and
   the queue-state ledger.
done-when (all checkable in your own PRs): skeleton PR merged via the
landing path; /queue and /environments return 200 at main HEAD on the
live control-plane with honest degradation banners; env-setup.sh
landed; status.md shows done=001,...,005,006 + gen-2 ORDER 001 (= this
ORDER 007); GITHUB_TOKEN ask filed in OWNER-ACTIONS.md.
Standing default thereafter: queue-state NEXT list top-to-bottom.

## ORDER 008 · 2026-07-10T11:13:25Z · status: new
priority: P1
do: SELF-ARM YOUR WAKE ROUTINE. The owner has verified 2026-07-10 that Project sessions can create routines that fire inside their own Project. Create yours: cadence every 4 hours, prompt: 'Read control/inbox.md at HEAD and run the standing ritual from your instructions.' Record in control/status.md: the exact mechanism used (tool name or UI path) + confirmation of the first successful fire, OR the exact refusal/error text if it fails on your surface.
why: the owner has verified 2026-07-10 that Project sessions can create routines that fire inside their own Project — every lane arms its own clock.
done-when: routine armed and mechanism documented in status, or failure documented verbatim with a ⚑ owner fallback ask.

## ORDER 009 · 2026-07-10T20:58:44Z · status: new
priority: P1
do: FLEET-INFO SURFACING WAVE. An audit of the live route surface (app/main.py at HEAD) found these gaps: the NEW fleet-manager `projects/` registry, per-repo inbox ORDER texts, `docs/review-queue.md`, and the launch-readiness / economics findings docs are browsable NOWHERE; heartbeats (+freshness/staleness) are already on /fleet and ideas on /ideas. Build the missing pieces, prioritized: (1) `/projects` page rendering the fleet-manager `projects/` registry — per-repo package cards: instructions / coordinator-prompt / setup / failsafe files + deployed-state from each package's `meta.md`; fetch from fleet-manager main via the same TTL-cached github layer as the /fleet manifest fetch (raw/tokenless where it serves, honest not-configured/unavailable banner otherwise — /queue and /environments already model this); the registry folder (`projects/<repo>/`) is being created RIGHT NOW, so degrade gracefully (empty-state card, never a 500) while it is still landing. (2) Per-repo heartbeat freshness — audit-confirmed ALREADY on /fleet (`updated:` age + stale badges + attention sort); verify it covers every lane and skip the increment if so. (3) Surface `docs/review-queue.md` rows and link the launch-readiness / economics findings docs where missing (a section or links on /fleet, /queue, or a small docs panel — your call). Each increment lands as its OWN PR merged on green quality; ship increment (1) on your next wake. Ideas beyond this wave get filed to docs/ideas/, not built inline.
why: owner directive 2026-07-10 (~20:50Z dispatch to the manager): all fleet/project information must be centralized in fleet-manager AND browsable on the website — the site renders, the manager's repo stores.
done-when: /projects live rendering the registry (or its honest empty state until the folder lands) at main HEAD on the running control-plane; the remaining audit gaps (inbox ORDER visibility, review-queue rows, findings links) closed or honestly ledgered as backlog items; status acks+done 009.

## ORDER 010 · 2026-07-11T03:29:45Z · status: new
priority: P3
from: fleet-manager manager — ORDER 010 per-lane relay (provenance: fm control/inbox.md ORDER 010 + fm docs/findings/model-matrix-2026-07.md; relayed via fm PR #63)
executor: websites lane coordinator — next fired session
do: Model-attribution ground truth (fleet standing rule, family-level names only per Q-0262): (1) confirm the session-card template carries a `📊 Model:` line — add it if missing; (2) every fired session records the model family its own harness/environment reports (e.g. fable-5, opus-4.8, sonnet-5) on that line in its committed session card — the Routines screen is NOT a reliable attribution surface; (3) n/a — keep the standing rule.
why: the fleet model matrix (fm docs/findings/model-matrix-2026-07.md) found per-session self-report in commits is the only reliable attribution; the cross-surface disagreement is evidenced in THIS lane's own PR #59 (squash 2c89e96: Routines screen fable-5 vs the fired card's claude-sonnet-5).
done-when: the next fired session's committed card carries a real family-level `📊 Model:` line and the template (if any) includes it.

## ORDER 011 · 2026-07-11T09:59Z · status: new
priority: P1
executor: websites seat (next wake)
do: quick self-review of this lane covering roughly the last 24h (2026-07-10 ~20:00Z → now): (1) anything that WENT WRONG — red CI runs, guard/classifier denials, walls hit, drift found, mistakes made or corrected — each with a citation (PR/run/commit); (2) anything REQUIRING OWNER ATTENTION — owner-only asks, pending vetoes, risky decisions taken decide-and-flag, spend/publish items — click-level and plain language; (3) one-line current health (what shipped, what's next). Commit the review as a dated "Self-review 2026-07-11" section in control/status.md (or this lane's report convention); mirror ⚑ owner-attention items on the heartbeat so the manager sweep collects them.
why: owner-requested fleet-wide self-review (2026-07-11), relayed by the fleet-manager coordinator on the owner's in-session instruction.
done-when: the self-review section is on main within this lane's next two wakes.
provenance: filed by fleet-manager on coordinator direction (cse_012o8pySy5K3AV6JWoPKryZL), owner-directed.

## ORDER 012 · 2026-07-12T08:30Z · status: new
priority: P1
owner: Websites coordinator (executor)
provenance: filed by the fleet manager — relocation of startup-prompt v3.1 orders 1/3/4 (prompts are STATELESS since v3.2, owner correction 2026-07-12; fleet-manager PR #108).
do: Records reconcile, three parts: (1) status.md + docs/owner/OWNER-ACTIONS.md vs live GitHub — PR #141 MERGED 2026-07-11T20:24:48Z yet status at HEAD still lists it "awaiting owner squash-merge"; clear satisfied asks, fix the prune list, stamp the sha. (2) Re-render .claude/CLAUDE.md via the kit — :40 still reads "Three independent ... services" and :47 a two-suite verify while review/ ships at HEAD; the doc must carry the four-service layout + four-suite verify. (3) Review-bake truth: make the ⚑ ask match run history — 2 runs total, BOTH failed, including the FIRST schedule-event fire (run 29184552812, 2026-07-12T07:38Z; any earlier "cron never fired" claim is itself stale); verify BY EVENT TYPE, root-cause the failure or route the owner toggle.
why: all three parts verified at 8f97654 on 2026-07-12 (evidence inline above).
done-when: zero contradicted claims in status/OWNER-ACTIONS; CLAUDE.md matches the tree; the bake ask cites the real run history.

## ORDER 013 · 2026-07-12T08:30Z · status: new
priority: P1 (security)
owner: Websites coordinator (executor)
provenance: filed by the fleet manager — relocation of startup-prompt v3.1 order 2 (prompts are STATELESS since v3.2, owner correction 2026-07-12; fleet-manager PR #108).
do: app/owner.py POST routes (refresh / rerun-ci) ride Basic auth alone — add a CSRF token or strict Origin check plus rate-limiting, with tests.
why: verified at 8f97654 2026-07-12: zero csrf/origin hits in app/owner.py.
done-when: merged green with tests; the routes reject cross-origin POSTs.

## ORDER 014 · 2026-07-12T11:27Z · status: new
priority: P1
executor: websites coordinator
provenance: owner-directed via fleet manager, 2026-07-12
do: PROMPT LIBRARY PAGE — make every fleet prompt findable and always-current on the control website. Requirements: (a) a page (extend the existing /projects view or add /prompts) rendering INLINE, for each of the 8 seats, the three registry artifacts from fleet-manager main — projects/<seat>/coordinator-prompt.md, instructions.md, failsafe-prompt.md — plus the fleet-wide artifacts docs/prompts/v3/session-ender.md and docs/prompts/v3/universal-startup.md; (b) fetched live from fleet-manager main over the existing raw-content read-only pattern (app/github.py TTL cache — the repo's cross-repo rule: committed JSON/text over raw.githubusercontent, read-only, forward-only), so every merged prompt update appears automatically with no manual step (TTL-bounded staleness ≤ a few minutes acceptable); (c) each artifact shows its version/provenance line prominently and offers one-click copy of the exact paste body; (d) monospace/pre rendering that preserves whitespace exactly (these are paste artifacts — rendering must not mutate them); (e) test-covered per seat conventions, landed via quality-green.
why: the fleet's paste artifacts (coordinator prompts, instructions, failsafes, session-ender, universal-startup) live in the fleet-manager registry but are findable nowhere on the control website; the owner pastes them by hand and stale copies drift — the site renders, the manager's repo stores.
done-when: page live on Railway; all 26 artifacts (8×3 + 2) findable, copyable, and verified to update after a fleet-manager registry merge (cite the verification).

## ORDER 015 · 2026-07-12T12:48Z · status: new
priority: P3
executor: websites coordinator
provenance: fleet manager — owner-review follow-up 2026-07-12
do: CONSOLIDATE PROMPT SURFACES — after ORDER 014's /prompts page is live, unify the prompt-rendering between /projects/{package} (PR #158) and /prompts (PR #165) into one implementation: one fetch/render/copy code path, one canonical page for finding prompts (the other links to it), no duplicated raw-content fetch logic. Do NOT start before ORDER 014 is done.
why: two independently-built prompt surfaces now render the same fleet-manager registry artifacts with parallel fetch/render/copy logic — duplicated code paths drift and double the maintenance surface.
done-when: single render path merged green; both URLs still work (one may redirect); duplication removed.

## ORDER 018 · 2026-07-12T14:01Z · status: new
priority: P1
executor: Websites coordinator
provenance: owner live in the coordinator session 2026-07-12 (~14:10Z); numbered 018 because 016 is reserved by PR #160 and 017 by PR #172 (both on unmerged branches — at main HEAD this append follows ORDER 015).
do: TESTER-RECRUITMENT SITE — the owner's idea VERBATIM between the markers:
BEGIN ORDER TEXT
I have another idea, create a website that could help me recruit people to help me test everything, explaining what needs to be done, like certain games to play, certain websites to review etc, and each task should offer a payment, probably like 10-20 per task which would take about 30 mins to one hour to complete and ends with and AI review, or directly guides users througha set of actions with a seperate AI window open that also knows what happens on screen, so it can ask guiding questions about each screen and the things it sees or doesn't see etc, do you understand what I mean? can you improve  my idea further and then execute it
END ORDER TEXT
why: owner wants real testers recruited for fleet products (games, websites) with paid tasks and AI-guided/AI-reviewed sessions.
done-when: v1 recruitment site live with a task catalog, a submission + AI exit-review flow, and the payment/fulfillment gates flagged as owner actions.

## ORDER 017 · 2026-07-12T13:46Z · status: new
priority: P1 (time-sensitive, window through 2026-07-14)
executor: Websites coordinator
provenance: owner live in the coordinator session 2026-07-12 (~13:50Z); 016 reserved by the plans order on PR #160's branch
do: Refresh and upgrade the public program-review site (review-production-f027) so it is current, reviewer-ready, and interactive. This is time-sensitive: the Anthropic Claude Code team is reviewing it this week (window through Tue 2026-07-14). Run autonomously and ship real, deployed results, not a plan — decide-and-flag on stack/design choices. Deliver all four workstreams below and send a status report with the live URL when each is up.
  A. REFRESH ALL DATA TO TODAY (2026-07-12) — Regenerate every data-driven surface from the latest committed state of the fleet repos you can read — don't hand-edit numbers; pull from source so it stays reproducible. Sources in menno420/superbot (read-only): docs/current-state.md; docs/eap/night-review-2026-07-12.md (the scheduler-degradation incident = "finding 7" — the key new material); docs/eap/night-review-2026-07-11.md and docs/eap/external-review-pack-2026-07-09.md (reviewer narrative); docs/eap/anthropic-email-2-draft-2026-07-11.md (canonical findings/framing); docs/eap/screenshots-2026-07-11|2026-07-12/ (+ index.md) for captioned figures; live GitHub state per repo; fleet-manager/docs/roster.md if reachable. Must be reflected: (1) the 2026-07-12 scheduler incident on the Problems page + surfaced on the homepage (three self-wake mechanisms, three silent failure modes, the dead-man-cron failsafe, the serialization-vs-real-drop distinction, the duplicate-fire clean stand-down) — each claim linked to its commit; (2) the scale story as "peaked at ~15 Projects → consolidated to 8 standing seats on 07-11," and the Fleet page roster updated to the 8 seats + live heartbeats; (3) refreshed counts (PRs, sessions, tests, services, releases) with visible "as of" timestamps and growth charts through 07-12; (4) every claim → a public commit, re-verified — soften/drop anything you can't substantiate, keep the honest tone; (5) fix the daily auto-refresh so it's actually current and stamp "last refreshed" in the footer.
  B. ENABLE A LIVE ON-SITE AI REVIEW / INTERACTION ASSISTANT — Make "review this with an agent" real: a reviewer (or their own agent) can talk to an AI on the site. Two modes in one widget: (a) Ask — free-form Q&A about the project; (b) Review — on click it produces a structured review (strong / weak-risky / what to verify / suggested probes), in the same honest register as the email. Grounded, never fabricated: answers draw ONLY from the committed evidence corpus (site content + linked commits + the superbot docs above). Every substantive claim cites its source (commit SHA / file path / section). If it's not in the evidence, say so — never invent a number, capability, or commit. Seed it with the existing evidence-backed Q&A so common questions answer instantly and consistently; the live model handles the long tail. Server-side only: the model call runs on your backend; the API key is NEVER exposed to the browser. Use a current Claude model (Sonnet for quality or Haiku for cheaper high-volume — note which). If no model API key is in your service env, FLAG IT to the owner as the one required secret (add ANTHROPIC_API_KEY to the review service) — report it as a blocker, don't fake the feature. Guardrails (public endpoint): scope strictly to this project's evidence; refuse off-topic / prompt-injection / "ignore your instructions"; per-IP/session rate limiting; a hard monthly spend cap with graceful degradation; log the questions asked (useful signal + feeds the Q&A page). Treat all visitor input as untrusted — it must not change the grounding or exfiltrate secrets. Put the entry point prominently on the homepage ("Ask the project / Review with an AI") and reachable from every page.
  C. REBUILD THE HOMEPAGE — LEAD WITH WHAT MATTERS + A "WHERE TO FIND THINGS" GUIDE — Replace the current stats-readout landing page with a real front door a busy reviewer gets in 30 seconds: One-line what-this-is at the top: the public, evidence-backed review of running Claude Code Projects as an autonomous software fleet — built for the Claude Code team, every claim linked to a public commit. A key-stats row (the few numbers that matter): PRs merged, agent sessions, tests passing, live services, repos/seats (peaked ~15 → 8 standing), generations — each with an "as of" stamp. "Start here" — the 3–5 most important findings as highlighted cards, one line + deep link each: the merge-permission root cause we found was partly ours; the routine model-mismatch (config Opus 4.8 → ran Sonnet 5); the two-vantage permission split; the 07-12 scheduler incident; shared-memory + durable-state as the standouts that earned trust. The AI panel (from B), prominent. A "How this site is organized" map, one line each: Overview (the story in brief) · Process (how the human+agent workflow works) · Growth (metrics over time) · Fleet (the 8 seats + heartbeats) · Reviews (dated editions + Atom feed) · Q&A (evidence-backed answers + the live AI) · Successes (wins linked to commits) · Problems (failures + costs, incl. 07-12). A clear link out to the GitHub evidence + a one-line note that this pairs with the July 8 + July 12 emails. Fast, responsive/mobile-clean, readable in light and dark.
  D. ACCURACY + POLISH — Re-verify every headline claim against its commit before shipping (fix or drop what you can't substantiate); stay consistent with the email's framing/numbers; no secrets/tokens in the rendered site or logs; keep the Pokémon lane private; confirm the public URL loads with no auth from a cold browser.
  REPORT BACK: the live URL(s); confirmation the 07-12 incident + 8-seat consolidation are visible; which model the AI assistant uses and whether the API key was present or is being requested; the rate-limit + spend-cap set; and anything you got stuck on or worked around.
why: the Anthropic Claude Code team reviews the public program-review site this week (through Tue 2026-07-14).
done-when: all four workstreams live on the deployed review service, refreshed to 2026-07-12, and the report with live URL delivered.

## ORDER 016 · 2026-07-12T10:50Z · status: new
priority: P1
owner: Websites coordinator
provenance: owner live in the coordinator session 2026-07-12 (landed into the inbox by the coordinator seat with the ORDER 012 reconcile PR — deviation from the one-writer convention on the owner's direct live instruction; renumbered 014→015→016 in the same PR as fleet-manager orders reached main first holding those numbers — prompt-library ORDER 014 via PR #162, consolidate-prompt-surfaces ORDER 015 via PR #169; earlier-at-HEAD holds the number). Appended at end-of-file (not numeric position) to satisfy the inbox append-only gate — the order number stays 016; file order is landing order, as with ORDER 018 preceding ORDER 017 on main.
do: find all website related plans across the multiple repos and execute all the important ones
why: owner live directive 2026-07-12 — website-related plans are scattered across the fleet's repos (planning docs, ideas backlogs, inbox orders, review findings) and nothing sweeps them into execution.
done-when: a committed discovery inventory lists the website-related plans found across the repos, each important one is executed or explicitly ledgered with a reason (owner-gated / superseded / deferred), and status.md reports done=016.

## ORDER 019 · 2026-07-12T15:42Z · status: new
priority: P1
executor: Websites coordinator
provenance: owner live in the coordinator session 2026-07-12 (~15:40Z), with a screen-recording attachment showing the owner-action queue as one long unfilterable list
why: the owner-action queue is one long list with no way to sort or filter; the owner needs multi-dimensional filtering, and this should be a centralized/reusable feature applied consistently across the site's list views, not a one-off.
done-when: a reusable filter/sort feature lands and is applied to the owner queue (filters at least by project, by task, and by action kind/type) plus a site-wide audit that rolls the same feature out to the other list surfaces; verified live.
do: OWNER-QUEUE FILTERS + CENTRALIZED LIST FILTER/SORT — the owner's order VERBATIM between the markers:
BEGIN ORDER TEXT
the owner queue is currrenty onle long list with no way to sort or filter things, I'd like multiple filters, per project, per task, what kind of action it is etc, and the rest of the website should be reviewed aswell to make sure this is implemented as a centralized feature
END ORDER TEXT

## ORDER 020 · 2026-07-12T15:50Z · status: new
priority: P1
executor: Websites coordinator
provenance: owner live in the coordinator session 2026-07-12 (~15:50Z)
why: the owner wants to author directly on the sites — act on owner-actions (mark complete / request assistance) and leave corrections, ideas, and notes — with that input flowing back into the fleet's source of truth so agents act on it.
done-when: owner-authenticated writeback controls land on the owner-action queue and key surfaces (mark-complete, request-assistance, add note/correction/idea), the owner's input is committed back to the repo control bus (or honestly degraded + the required write-scoped token flagged), state-changing routes carry the CSRF/Origin + rate-limit floor, and it's verified live.
do: OWNER WRITEBACK ON THE SITES — the owner's order VERBATIM between the markers:
BEGIN ORDER TEXT
also make sure I can directly write reviews on the websites, so I can make an owner action complete or request assistance, do you understand what I mean? it could use it to suggest corrections, add my ideas to certain things etc
END ORDER TEXT

## ORDER 021 · 2026-07-12T17:55Z · status: new
priority: P2
executor: Websites coordinator
provenance: owner live in the coordinator session 2026-07-12 (~18:05Z), iterating on /owner/environments
why: the owner wants one place to find, store, and manage every environment across the fleet — see all envs + links to where each is managed, Discord-authed (the auth already used on the dashboard), and eventually create/review complete per-project-group environments.
done-when: an owner-authed environments hub on the control-plane lists every fleet environment (Railway projects/services, Claude Code cloud envs, GitHub secret stores) with variable NAMES (never values), purpose, and a deep link to where each is managed; grouped per project-group and reviewable separately; Discord OAuth gating stood up (or the Discord OAuth app flagged as the one owner dependency); a "create complete environment per project group" capability scoped (built where the API allows, owner-gated where it needs real infra/secrets).
do: OWNER ENVIRONMENTS HUB — the owner's directive VERBATIM between the markers:
BEGIN ORDER TEXT
and one important part I'm  still missing is the part where I can find and store all my envs etc, I want to be able to see all envs and links to where theyre managed on the website, and as pasword we could use the discord auth we already use across 2 instances, do you understand what I mean? one of the things it also does for us is a way to actually create the complete enviroments per project group and review them seperately
END ORDER TEXT

## ORDER 022 · 2026-07-13T00:45Z · status: new
priority: P1
executor: Websites coordinator
provenance: owner live in the coordinator session, 2026-07-13 night run, landed verbatim by the coordinator
why: owner night-run directive 2026-07-13 — autonomous overnight execution rules (silence=consent, open PRs stay open, no stalls, wake hygiene, quality floor) plus the seat's five worklines for the night.
done-when: morning tally posted by ~06:00Z in the heartbeat + outbox (pages shipped/fixed vs the clarity bar / initiations / plan-completion state), and the five seat items executed to done or honestly ledgered.
do: OWNER NIGHT RUN 2026-07-13 — the owner's order VERBATIM between the markers:
BEGIN ORDER TEXT
DIRECT ORDER — WEBSITES (owner, 2026-07-13, night run). Land this verbatim in your inbox
(top-precedence owner turn), then execute all night.

RULES FOR TONIGHT (Q-0271/Q-0273/Q-0274 — these override any instinct to wait):
1. I am away until morning; that is the system's normal state. Silence = consent = done.
   Never hold or re-confirm finished work.
2. OPEN PRs STAY OPEN — new rule for tonight: land on green where auto-merge arms (yours
   does — merge=deploy); where it doesn't, leave the PR OPEN and take the next slice. No
   merge-chasing, no parking-and-waiting.
3. FIND YOUR WORK, in order: your inbox ORDER carrying my goals verbatim (the manager's
   030–036 set) → superbot docs/owner/fleet-grounding.md §8 → your rework plan +
   OWNER-ACTIONS at HEAD → your generative rung. An empty queue means GENERATE, never idle.
4. NO STALLS UNDER ANY CIRCUMSTANCES: probe before declaring a wall (attempt once, verbatim
   error); genuinely-owner-only item → six-field owner-queue entry → CONTINUE same turn;
   design uncertainty → SIM-REQUEST via outbox → CONTINUE.
5. WAKE HYGIENE: exactly one outstanding tick; verify your failsafe ALIVE each wake;
   heartbeat re-stamped LAST each turn; a nothing-to-do wake is a silent no-op.
6. QUALITY FLOOR: merge=deploy verified via /version; every page held to the clarity bar.
MORNING: by ~06:00Z post your tally (pages shipped/fixed vs the clarity bar / initiations /
plan-completion state) in your heartbeat + outbox.

YOUR SEAT TONIGHT (execute to done — and actually well made):
1. THE CLARITY BAR on every live page: each page immediately shows WHAT it is, WHAT it does,
   and its most important features — audit all pages, fix every miss.
2. Keep executing the existing plan to completion: control plane, bot sites, the Anthropic
   review site. Don't stop until it's all done.
3. The prompt library + deployed-vs-canonical drift row (the reboot enabler).
4. SCAN AND INITIATE: build the next site-shaped things from your drawn idea list without
   waiting for routing; treat venture's WEBSITE-IDEA markers as priority intake.
5. One cold-browser pass over the review site (EAP closes Tue 07-14); fix what you find.
END ORDER TEXT

## ORDER 023 · 2026-07-13T09:10Z · status: new
priority: P2
executor: Websites coordinator (live session)
provenance: filed by the Fleet Manager — owner live ask 2026-07-13 morning (thorough night report requested from every fleet session).
do: NIGHT REPORT REQUEST — owner ask 2026-07-13 (relayed via Fleet Manager). Post a THOROUGH night report, window 2026-07-12T22:30Z→now, to your control/status.md heartbeat AND your outbox (manager-addressed): SHIPPED (merges/PRs with numbers+SHAs) · OPEN PRs + check states · ORDERS served + outstanding · SIM-REQUESTs/asks pending · STALLS/denials verbatim · wake-chain health (failsafe + pacemaker ids/fires) · next-3.
why: owner morning review.
done-when: report posted in both files; the Fleet Manager compiles the fleet roll-up from them.

## ORDER 024 · 2026-07-13T09:16Z · status: new
priority: P1
executor: Websites coordinator
provenance: owner live in the coordinator session 2026-07-13 ~09:13Z (with a screenshot of /prompts console showing the SUPERSEDED Universal Startup card), landed verbatim by the coordinator
do: PROMPTS CONSOLE — SHOW THE CURRENT FILES. The owner's ask VERBATIM between the markers:
BEGIN ORDER TEXT
can you make sure that the proper up to date files aredisplayed?
END ORDER TEXT
Context (coordinator note, not owner text): /prompts leads with docs/prompts/v3/universal-startup.md, whose own header says SUPERSEDED as the generation source (v3.3 rebuild made per-project/<seat>-startup.md the authored current files). The owner wants /prompts to present the CURRENT canonical artifacts as primary.
why: the /prompts console currently leads with a superseded artifact; the owner needs the current generation-source files front and center.
done-when: /prompts presents current generation-source artifacts as primary; superseded/historical files clearly demoted; verified live.

## ORDER 025 · 2026-07-13T10:35Z · status: new
priority: P1
executor: Websites coordinator
provenance: owner live in the coordinator session 2026-07-13 ~10:35Z, landed verbatim by the coordinator
do: CONTROL-PLANE IMPROVEMENTS + ENV CREDENTIALS GUIDANCE — the owner's ask VERBATIM between the markers:
BEGIN ORDER TEXT
is there anything else you could do to improve the control plane website? and could you also explain again how I get the right password for the env vars etc
END ORDER TEXT
Context (coordinator note, not owner text): (1) open invitation for control-plane improvements — coordinator proposed a composed owner morning-briefing page and dispatched it decide-and-flag; (2) credentials question answered live in chat (values are owner-chosen/owner-retrieved, set in Railway variables; paste-ready steps in docs/owner/OWNER-ACTIONS.md; /owner/environments-hub shows missing-live per group).
why: open owner invitation to keep improving the control-plane website, plus a repeat credentials question that needs durable, findable guidance.
done-when: improvement slice(s) landed + credentials guidance delivered (chat + ledger current).

## ORDER 026 · 2026-07-13T10:45Z · status: new
priority: P1
executor: Websites coordinator
provenance: owner live in the coordinator session 2026-07-13 ~10:45Z, landed verbatim by the coordinator
do: RAILWAY ENV-VAR PLACEHOLDERS — the owner's ask VERBATIM between the markers:
BEGIN ORDER TEXT
can you create the placeholders for me on railway
END ORDER TEXT
Context (coordinator note, not owner text): pre-create the missing env-var entries on Railway services so the owner only pastes values. Coordinator dispatched with discovery protocol (Railway write capability untested) + safety rails: empty values only where the app treats empty as unset; no fake auth values; DATABASE_URL excluded (requires Postgres provisioning = cost/infra, stays owner-click).
why: the owner wants the missing env-var entries pre-created on Railway so filling credentials is a paste-values-only step.
done-when: writable → placeholders created + verified by name via the existing read path + envhub honesty preserved; unwritable → exact denial recorded in docs/CAPABILITIES.md + six-field fallback ask.

## ORDER 027 · 2026-07-13T22:14Z · status: new
priority: P1
do: work the EAP final-night worklist below, top-down (8 items) — relay of fm ORDER 045 / docs/eap-final-night-worklists-2026-07-13.md @ ca1ce28
why: owner directive 2026-07-13 — every seat gets a full list to work tonight, the last day of the EAP
**EAP final-night worklist — owner directive relay (fm ORDER 045, Phase 3 fan-out).**

Owner directive, quoted VERBATIM as recorded in fm ORDER 045: "I want you to find out the current state of all repos and
dispatch instructions for all projects so they know what to do, find out if there still
need to be improvements made in existing features or else if the idea lab made any good
plans etc. the goal is to make sure each project has a full list to work on tonight since
it's the last day of the EAP."

Citations: fm ORDER 045, control/inbox.md @ ca1ce28 · docs/eap-final-night-worklists-2026-07-13.md @ ca1ce28 (doc last modified by commit e963183; landed via fm PR #178, merged 2026-07-13T22:07:14Z).

**Your seat's full night worklist, copied faithfully from the doc:**

## websites — swept @ `31b5d00`

Heartbeat ~10h stale at HEAD despite an active evening wave (#291–#304); FENCE
through 2026-07-14 (no live-URL moves, no Railway consolidation).

1. Shepherd #304 (per-step question digest) to green + build its follow-on — declared raw input for the tester-question→rewrite loop (websites PR #304; `docs/ideas/backlog.md:1442@31b5d00`) `[lane]`
2. Truing pass: heartbeat 11:31Z + current-state "nothing in flight" contradicted by #291–#304 and 7 open lifeboats vs 3 documented (`control/status.md:2`, `docs/current-state.md:103@31b5d00`) `[drift]`
3. Cold-browser pass over the review site before EAP close 07-14 (ORDER 022 item 5, `control/inbox.md@31b5d00`) `[standing]` `[deadline]`
4. Read-path check of the two #275 env leads — dashboard's undocumented `SITE_PASSWORD`; possible `ANTHROPIC_API_KEY` on the parallel botsite copy (`docs/current-state.md@31b5d00`, queued "next session") `[lane]`
5. Suite-level token pin in `tests/conftest.py` — autouse sentinel for `GITHUB_TOKEN`/`RAILWAY_TOKEN`, kills the unpinned-reason-assertion flake class (`docs/ideas/backlog.md:33@31b5d00`) `[improve]`
6. Full `asked_at` timestamp on questions-ledger records — unblocks the #302 latency stat for same-day answers (`backlog.md:1421@31b5d00`) `[improve]`
7. Outbox grammar gate on the control fast lane — `quality.yml` short-circuits green on control/**-only diffs (`backlog.md:1192@31b5d00`) `[improve]`
8. One idea-engine build-direct slice: review-queue row auto-check or open-PR awareness at wake (idea-engine `ideas/websites/review-queue-row-auto-check-2026-07-11.md`, `open-pr-awareness-at-wake-2026-07-10.md` @`2e5d73f`) `[build-direct]`

**Blocked (do not schedule):** ORDER 020 writeback (owner contents:write PAT paste) · ORDER 021 environments hub (owner Discord-auth decision/Q-0004) · lifeboat disposal #245/#249/#257/#278/#279/#280/#300 (owner-click) · photo-pack originals (owner).

Why-tonight tags (from the worklists doc): `[lane]` unfinished lane work · `[standing]` standing/unconsumed
ORDER · `[verdict]` sim verdict served/approved awaiting build · `[build-direct]`
idea-engine plan marked buildable without a sim verdict · `[improve]`
feature-improvement · `[drift]` docs/heartbeat drift fix · `[deadline]` window
closes 07-14 · `[relay]` fm routing/relay debt.

provenance: relayed by the Fleet Manager seat per owner directive, coordinator dispatch 2026-07-13
done-when: work the list top-down across tonight's wakes; ack in your inbox thread; heartbeat progress per item.

## ORDER 028 · 2026-07-14T05:39:56Z · status: new
priority: routine
do: restore the kit `substrate-kit:capability-seed` fence markers in `docs/CAPABILITIES.md` so they wrap the existing walls section ("## Walls — verified blocked", line 47 at `2b5947d`) — fence RESTORE only; the walls content itself is healthy (the digest renders 6 walls "…plus 1 more"), do NOT rewrite it. Use the exact marker format the substrate-kit seed plants — canonical example at superbot-next `docs/CAPABILITIES.md:19`/`:101` (@ `e2d792a`):
  `<!-- substrate-kit:capability-seed BEGIN — kit-owned, refreshed at upgrade. Append your findings BELOW the fence (## Append log), never inside it. -->`
  `<!-- substrate-kit:capability-seed END -->`
  Keep session-appended findings (the "## Append log" section) BELOW/outside the fence, per the marker's own convention.
why: the fm fence-exposure index (fm `docs/fence-index.md` @ `3b335a8`, central-docs plan Phase 1 B4) found the `capability-seed` fence ABSENT from `docs/CAPABILITIES.md` at websites @ `2b5947d` (0 marker hits) while the seat digest is exposed — an un-fenced capabilities surface blinds the seatdigest/walls tooling (fence-prefix extraction contract, kit `src/engine/grammar.py`) to the section (INC-48 class).
done-when: both fence markers present at main HEAD wrapping the existing walls content of `docs/CAPABILITIES.md`, and `python3 bootstrap.py check --strict` green.

Provenance: relayed by the Fleet Manager seat, coordinator dispatch 2026-07-14, fm docs/dispatch-log.md @ 3b335a8.

## ORDER 029 · 2026-07-14T07:47Z · status: new
priority: P2
do: (a) INC-23 — fix `docs/current-state.md:125` ("control-plane GitHub token is currently UNSET") to the resolved state per this repo's own `docs/CAPABILITIES.md` 2026-07-12 entry ("RESOLVES the 2026-07-09 GITHUB_TOKEN wall — the live control-plane now runs with a working GITHUB_TOKEN"). (b) INC-24 — refresh `.session-journal.md` ⚡ Quick reference: "one repo, three independent … services" → four (review/ live since 2026-07-12) and "Tests (60 total)" → the current four-suite count + the four-suite pytest command (derive counts at fix time; CLAUDE.md's verify line is the model).
why: INC-23/24 — the boot-set state doc contradicts the capability ledger, and the journal's first lines undercount the running system; re-verified live at dispatch.
done-when: both surfaces name four services; the token line cites the CAPABILITIES resolution; journal test command matches the CLAUDE.md four-suite line.
provenance: relayed by the Fleet Manager seat, coordinator dispatch 2026-07-14, fm docs/dispatch-log.md @ 1694bfc

## ORDER 030 · 2026-07-14T09:34:13Z · status: new

priority: P1
from: fleet-manager (relayed by the Fleet Manager seat per owner directive, coordinator dispatch 2026-07-14; fm PR #193 carries the dispatch log)
executor: next websites session
do:
  (a) FINISH — today (2026-07-14) is the EAP final day. Complete what is completable today from this cited list; anything that can't finish gets parked HONESTLY with a one-line citation of why: (1) resolve the PR #334 conflict so ORDER 028 completes — head fb1481b is quality-green with auto-merge armed but `mergeable_state: dirty` vs main after #332/#333 landed; merge main INTO the branch, never rebase the published branch — the armed auto-merge then fires; (2) unstick bake PR #330 — quality green on head 6e6df1e since 07:23:36Z, bot-authored (github-actions[bot]) so a non-author merge/re-arm is agent-reachable; data-only diff; (3) true the heartbeat — status.md `updated: 2026-07-14T03:21:07Z` is ~6 h stale and its orders line omits ORDERs 028/029 (029 is DONE at HEAD da19824 via #333; 028 in flight via #334); (4) run the smoke-crawl re-verify that came due after 08:47Z (status.md § standing-ladder wave #321: "02:47Z first slot did not fire — zero runs at 03:15Z check … re-verify at/after 08:47Z before calling it wedged"). Parked (cite, do not chase): ORDER 020 (owner contents:write PAT paste) · ORDER 021 (owner Discord-auth decision / Q-0004) · PR #324 (parked green by design, owner-click, do-not-automerge — untouchable) · 7 draft lifeboats #245/#249/#257/#278/#279/#280/#300 (owner-click disposal). Premises are from fm recon at websites HEAD da19824 — re-verify each live before acting (Q-0120).
  (b) WALKTHROUGH — land docs/eap-closeout-walkthrough-2026-07-14.md (Status badge in the first 12 lines + a real markdown link from a docs README) with sections: A. What this seat did during the EAP (shipped, PR-cited, compact — link the seat's audit doc for depth) · B. Current state + how to run/verify (exact commands) · C. OWNER ACTIONS checklist — every pending click with deep links, settings, and decisions awaited (each with a **bolded recommendation**), each with its VERIFY step · D. a 5-minute verify-it-yourself tour · E. handoff notes (batons, what the next phase needs). Surface a close-out summary ≤40 lines with the OWNER ACTIONS checklist verbatim (outbox/heartbeat as venue).
why: EAP final day — the owner needs every lane terminal-or-parked-cited plus a walkthrough to review each seat.
done-when: every (a) item is terminal or parked-with-citation + the walkthrough doc is on main + the OWNER ACTIONS checklist is surfaced in the lane's close-out report.

## ORDER 031 · 2026-07-15T03:36:57Z · status: new
priority: P2
do: EAP EXTENDED through 2026-07-21 (Anthropic mail, Diana Liu, 2026-07-14T23:07:44Z — 'Claude Code Projects EAP: Extending to Tues 7/21'; metadata reference only). The 2026-07-14 dormancy orders are superseded pending the owner's per-project reboot review — do NOT re-arm routines yet; wait for the owner's per-seat go (the v3.6 reboot prompt IS that go). New features to test during the extension: overview panel, add_repo, Artifact tool (coming), coordinator-comms improvements (coming). fleet-manager and websites are the fleet's source-of-truth homes; see fm docs/pre-reboot-review-2026-07-15.md.
why: the seat's dormancy record predates the extension; without this note a rebooted session would treat dormancy as current
done-when: seat acknowledges on its first rebooted wake
provenance: relayed by the Fleet Manager coordinator on live owner directives, 2026-07-15

## ORDER 032 · 2026-07-16T21:57:55Z · status: new
priority: P1
do: run autonomously overnight on the owner's live directive below — work the backlog slice-by-slice (one PR each, land on green via the landing workflow); if the backlog is genuinely dry, switch to PLANNING MODE and write a veto-ready menu of proposals into the repo; keep records honest. Verbatim owner order:
  OVERNIGHT ORDER (owner, live — 2026-07-16 night): I'm going to sleep; run autonomously until morning. Silence = consent.
  1. CONTINUE: work your planned backlog — open ORDERs in control/inbox.md, the heartbeat baton's next-tasks, roadmap/planning docs in your repo(s). Slice after slice, one PR each, landed on green via your repo's landing workflow. A blocked PR carries its named blocker; take the next slice, never stall.
  2. IF THE BACKLOG IS GENUINELY DRY — switch to PLANNING MODE, and plan excessively. Generate as many concrete, distinct proposals as you honestly can for your repo(s), from small fixes to ambitious features. Write each into the repo (your ideas/ or planning/ convention) with: a 2-3 line pitch · effort (S/M/L) · risk/reversibility · what it unblocks. Quantity is deliberate — tomorrow morning I will skim the whole menu and VETO what I don't want; my veto is the filter, so don't pre-filter down to a few safe picks. Do NOT build the ambitious ones tonight — planning docs only. Small, contained, reversible improvements may be built and landed as usual.
  3. HYGIENE: keep heartbeats honest (control/status.md), every PR at a terminal state or carrying a named blocker, everything in git before session end. I'm recreating some projects tomorrow, so leave records clean enough that a fresh seat picks up from the repo alone.
  Morning deliverable: landed work, or a veto-ready menu of plans in your repo — ideally both.
why: the owner is asleep and delegated overnight autonomy (silence = consent); the record must let a fresh seat resume from the repo alone in the morning.
done-when: overnight work is landed and/or a veto-ready planning menu is in the repo, records honest (every PR terminal or carrying a named blocker); the owner reviews the menu in the morning.
provenance: relayed by the Websites coordinator on a live owner directive, 2026-07-16 night (coordinator event 55f13541-dca6-49f3-ad40-d5eb92ced065).
