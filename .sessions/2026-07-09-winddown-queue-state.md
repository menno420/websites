# 2026-07-09 — gen-1 wind-down: commit the queue state

> **Status:** `in-progress` — wind-down Phase 1: settle open PRs (none found open),
> then commit the roadmap/queue state to the repo so a gen-2 Project can boot from
> `main` alone.

- **📊 Model:** claude-fable-5 (wind-down worker session)

**What this session is about:** the lane is moving gen-1 → gen-2. A fresh
Project boots only from what is committed on `main`, so everything that lives
only in chat/session state gets settled or committed now: (1) disposition every
open PR (result: zero open PRs — verified via the GitHub API this session),
(2) write the DONE / IN-FLIGHT / NEXT queue state into a durable doc, (3) update
`docs/current-state.md` and overwrite `control/status.md` as the deliberate last
step.
