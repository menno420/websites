# 2026-07-12 — ORDER 017 coordinator: review-site refresh, four workstreams shipped and cold-verified live

> **Status:** `complete` — branch `claude/session-card-2026-07-12-order-017`;
> record-only close-out card for today's coordinator session, born complete
> in its only commit (the work it records is already merged to main —
> mirroring PR #163's record-only session-card pattern).

- **📊 Model:** Claude Fable 5 · webagent coordinator (worker fan-out) · order

**What this session was about:** Rung: order — executed ORDER 017, the
review-site refresh for the Anthropic review window (PR #172 carried the
order onto `control/inbox.md`). This was the COORDINATOR session: a webagent
session that decomposed the order into four workstreams, fanned each out to
a build worker on its own branch/PR, reviewed and merge-trained the results,
and cold-verified the live site after the landings. This card is the
coordinator's own record, landed as a close-out chore (each worker's card
shipped inside its own PR).

## What was done

- **ORDER 017 executed end-to-end — 4 merged PRs, one per workstream:**
  - **#175 — workstream A, data refresh** (merge `50dd661`): the
    2026-07-12 scheduler incident leads `/problems`; the fleet page
    reflects the 8-seat structure; as-of footer stamps on the stats
    surfaces; a review-service row added to the control-plane deploy
    board. Card: `.sessions/2026-07-12-order-017-review-data-refresh.md`.
  - **#174 — workstream B, `/ask` AI assistant** (merge `2c6700e`):
    claude-sonnet-5 called server-side (the key never reaches the
    client), $25/mo spend cap, per-IP 20/h + 100/d and 500/d global rate
    limits. Card: `.sessions/2026-07-12-order-017-ai-assistant.md`.
  - **#180 — workstream C, homepage front door** (merge `d7721bb`): the
    30-second homepage rebuild, dependent on A+B landing first. Card:
    `.sessions/2026-07-12-order-017-homepage.md`.
  - **#184 — workstream D, private-lane filter** (merge `790aa5e`): the
    Pokémon lane stays private on every public surface of the review
    service. Card: `.sessions/2026-07-12-order-017-private-lane-filter.md`.
- **Cold verification:** the merged result was verified on the live
  deployment at `review-production-f027.up.railway.app` from a cold client,
  not a warm build session; the final check after #184 landed showed the
  site serving sha `790aa5ef` — exactly main HEAD at close (the #184
  squash-merge), so the deploy pipeline converged on everything shipped.
- **Orchestration shape:** worker fan-out from a webagent coordinator
  session — the coordinator never built on the shared checkout; each
  workstream got a fresh worker on its own branch, PRs opened READY with
  auto-merge armed; landings ran B → A → C → D (C depended on A+B; D
  closed the order's compliance line last).
- **Outstanding ⚑ owner action (carried forward, not new):** the repo's
  Actions "Allow GitHub Actions to create and approve pull requests"
  toggle is still off, so the scheduled review-bake cannot self-land its
  data-refresh PRs — workstream A shipped the honest degradation for
  exactly this wall; the toggle remains the unblock.
- Verified (this card's own gates, 2026-07-12T16:04Z): `python3 -m pytest
  tests/ botsite/tests dashboard/tests review/tests -q` — 555 passed;
  `python3 bootstrap.py check --strict` — PASS.

⚑ Self-initiated: no — ORDER 017 close-out chore (the coordinator session's
own record), the order's final deliverable.

## 💡 Session idea

**Committed fan-out manifest for coordinator sessions** — when a
coordinator decomposes an order into worker branches, commit a small
manifest next to the order doc (workstream → branch → PR → card slug →
state), updated as PRs land. Worth having because today's fan-out state
(four workers, dependency-ordered merges, cold-verify results) lived only
inside the webagent conversation — a dead coordinator loses the map, and a
sibling session re-deriving it from `git log` costs a boot. Deduped against
`docs/ideas/backlog.md` + the queue-state NEXT list: dispatch-readiness
chips and the `wait-deploy.py` sha poller exist; nothing covers committed
fan-out state. Not yet captured in the backlog — this close-out lands
card-only by design; the backlog bullet is the follow-up.

## ⟲ Previous-session review

The workstream-D session (#184) did well: an accent-aware privacy sweep
that caught two "Pokémon" forms plain `grep -i` misses, and it said plainly
that the stats.json filter was hand-applied where the REST bake is walled.
What it missed (workflow, order-wide): no workstream owned the
coordinator's own close-out card, so the order's record lands as a trailing
chore hours after the last merge — the order template should name the
coordinator card as an explicit final deliverable, branch and slug included,
from the start.
