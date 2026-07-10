# 2026-07-10 — Fleet polish batch: stalled-claim aging on /orders + /queue.json + kit rollup on /fleet

> **Status:** `in-progress` — branch `claude/fleet-polish-batch`; flips to
> `complete` + the real PR number after the PR exists.

- **📊 Model:** claude-fable-5 · worker · routine-fired build slice (continuous mode, slice 8 — 23:12Z nudge)

**What this session was about:** the 23:12Z send_later continuation. Inbox at
HEAD has no order past 009; latest heartbeat is this session's own (no
sibling active). Work-ladder rung 3 — the coordinator-blessed bundle of
three small backlog captures, all presentation/parse over ALREADY-FETCHED
data (zero new fetches): (a) **stalled-claim aging on `/orders`**
(`parse_orders` learns the claim's ISO timestamp — the field slice 6's
review said should have been extracted the first time — and a claim older
than the ritual's ~24h expiry badges `claim stale?`); (b) **`/queue.json`**
(the manager's machine round-trip over `owner_queue.overview()`); (c)
**kit-version rollup on `/fleet`** (summary header over the already-parsed
`kit:` lines).

## What was done

- (work in progress — filled at close-out)
