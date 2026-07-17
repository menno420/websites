# 2026-07-17 — Dashboard arcade live/blocked counts (B1)

> **Status:** `in-progress` — branch `claude/dashboard-arcade-counts`; the
> dashboard `/status` page will gain an arcade live/blocked count read from the
> committed `botsite/data/arcade.json` over raw.githubusercontent.com (the same
> fetch mechanism the console feed uses), degrading honestly when the feed can't
> be fetched. [[fill:one-line result at flip]]

- **📊 Model:** [[fill:model · effort · task-class]]

**What this session is about:** the dashboard `/status` page shows inventory
counts for the bot (subsystems, cogs, commands, ideas, bugs …) but says nothing
about the fleet arcade. B1 (NEXT-TASKS §1) adds an arcade line to `/status`:
total games with a live count and a blocked count, read live from the committed
`botsite/data/arcade.json` over raw.githubusercontent.com — an additive,
read-only GET render, no state change, no new credential, no cross-service
import.

⚑ Self-initiated: no — coordinator-dispatched backlog slice (B1) of the standing
overnight ORDER 032.

## Close-out

**Evidence:**

- files touched this branch: [[fill:files]]
- git: [[fill:branch + commit SHAs]]
- verify: [[fill:four-suite + bootstrap check results]]

**Judgment:**

- Decisions made: [[fill:decisions]]
- Next session should know: [[fill:handoff]]

## 💡 Session idea

[[fill:one genuine session idea]]

## ⟲ Previous-session review

[[fill:one-line review remark on the previous card]]
