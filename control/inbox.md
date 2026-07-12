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
