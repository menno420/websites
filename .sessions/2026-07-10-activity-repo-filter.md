# 2026-07-10 — ?repo= filter on the activity views (backlog promotion)

> **Status:** `in-progress` — branch `claude/activity-repo-filter`; flips to
> `complete` + the real PR number after the PR exists.

- **📊 Model:** claude-fable-5 · worker · routine-fired build slice (continuous mode, slice 10 — 00:14Z nudge, executed ~01:12Z)

**What this session was about:** the 00:14Z send_later continuation (queued;
executed ~01:12Z). Collision check: heartbeat at HEAD still carries this
chain's 23:57Z stamp and zero open PRs — no active sibling; a fresh session
did land #85 (kit v1.7.1 → v1.8.0) without a heartbeat overwrite. Inbox at
HEAD has nothing past 009. Work-ladder rung 3 — this chain's designated
pick: the **`?repo=` filter on the activity views** (idea file
`docs/ideas/activity-per-repo-filter-2026-07-09.md`, queue-state NEXT item
5): narrow `/activity`, `/activity.json`, `/activity.xml` to one repo so a
reader subscribes to a single lane's feed; reuses the cached timeline —
zero new fetch paths, fewer fetches when filtered.

## What was done

- (work in progress — filled at close-out)
