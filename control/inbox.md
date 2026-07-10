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
