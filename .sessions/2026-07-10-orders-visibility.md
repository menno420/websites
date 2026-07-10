# 2026-07-10 — /orders: per-repo inbox ORDER visibility with outstanding computation (backlog promotion)

> **Status:** `in-progress` — branch `claude/orders-visibility`; flips to
> `complete` + the real PR number after the PR exists.

- **📊 Model:** claude-fable-5 · worker · routine-fired build slice (continuous mode, slice 6 — 22:14Z nudge)

**What this session was about:** the 22:14Z send_later continuation. Inbox at
HEAD has no order past 009; work-ladder rung 3 — promoted the backlog's
**per-repo inbox ORDER visibility** capture (ORDER 009's audit named per-repo
`control/inbox.md` ORDER texts as browsable nowhere; the bullet notes it
"pairs naturally with the heartbeat enrichment's outstanding-orders
computation"). Coordinator concurred it is the higher-value pick over the
own-heartbeat self-check. Build: an `/orders` page — every fleet repo's
inbox ORDER blocks parsed and cross-referenced against that repo's own
heartbeat `done=`/`claimed-by:` lines, so each order renders with an honest
open / claimed / done badge and "what's outstanding fleet-wide" becomes one
glance.

## What was done

- (work in progress — filled at close-out)
