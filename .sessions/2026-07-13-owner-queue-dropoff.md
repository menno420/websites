# 2026-07-13 — owner queue: drop-offs section (abandoned guided sessions)

> **Status:** `in-progress` — branch `claude/owner-queue-dropoff-0713`; flips to `complete`
> + PR number as the deliberate LAST code step.

- **📊 Model:** [[fill:model]] · worker · backlog-promotion

**What this session was about:** backlog promotion — the `captured` bullet
"Abandoned guided sessions surfaced on the owner queue" in
`docs/ideas/backlog.md` (2026-07-13, from the #292 guide-transcript-evidence
session 💡). A tester who chats with the AI guide but never submits leaves
persisted `guide_exchanges` rows (PR #292) the owner can never see, because
the owner queue at GET /testing/owner iterates submissions only. This session
adds a small read-only "Drop-offs" owner-queue section listing
claimed-but-never-submitted claims that have guide-chat activity — exchange
count + last exchange time, full transcript behind the same collapsed
`<details>` the submissions view uses.

## What was done

- [[fill:what-was-done]]
- Verified: [[fill:verification]]

⚑ Self-initiated: no — backlog promotion of the `captured` bullet
"Abandoned guided sessions surfaced on the owner queue"
(`docs/ideas/backlog.md`, 2026-07-13).

## 💡 Session idea

[[fill:idea]]

## ⟲ Previous-session review

[[fill:previous-session-review]]
