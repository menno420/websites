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
