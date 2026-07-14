---
state: built
origin: session:2026-07-10-session-card-template
shipped_pr: 90
shipped_repo: menno420/websites
merged_date: 2026-07-11
outcome: shipped
---

# Open-PR awareness at wake — sibling-session collision check (2026-07-10)

> **Status:** `ideas`

## The gap

The wake ritual reads `control/inbox.md`, `control/status.md`, and the
queue-state ledger — but **never the repo's open PRs**. Lived twice on
2026-07-10:

- The 20:00Z wake started ~6 minutes after a sibling session pushed
  `claude/routine-prompt-doc` and opened PR #63 (READY, card complete,
  unmerged). Nothing in the ritual surfaces this; only an ad-hoc
  `git ls-remote` + PR list caught it before both sessions edited
  `docs/project/README.md` and produced a merge conflict.
- The queue-state addendum still described the ORDER-008 branch as "not yet
  merged" hours after it landed as PR #59 — a committed ledger goes stale the
  moment a sibling merges, but the live PR list never lies.

## The idea

Add one step to the wake ritual (and one line to
`docs/project/project-instructions.md` when its char budget next allows):
**list open PRs + unmerged `claude/*` branches at session start**, before
picking a work rung. Cheap mechanical form: a `scripts/open-work.py` (or a
documented `git ls-remote --heads origin` + PR-list one-liner) that prints
open PRs, their head branches, and any remote `claude/*` branch with commits
not on `main` — three states per item: PR open (leave it to its session),
branch pushed PR-less (rescue candidate per the stranded-work protocol), or
merged-stale (ledger drift to fix).

## Why it's worth having

Concurrent sessions are now the norm (4-hourly routine + coordinator
dispatches + owner sessions); the inbox/status bus covers orders but not
in-flight code. One glance at open work prevents duplicate builds, merge
conflicts on shared files, and false "needs rescue" alarms — the same class
of failure the order-claim ritual fixed for orders, applied to branches/PRs.

Deduped against `docs/ideas/backlog.md` + queue-state NEXT: heartbeat
enrichment adds a `landing:` line describing a session's OWN branch state;
nothing covers discovering OTHER sessions' open PRs/branches at wake.

## Forward-only note — doc-step slice shipped (2026-07-13)

The wake-ritual DOC step — the idea's original ask, and the idea-engine
probe report's named smallest shippable slice (§8), explicitly skipped when
`scripts/open_work.py` self-served via PR #90 — shipped 2026-07-13 in this
PR: the sweep step now lives in `docs/project/routine-prompt.md` (v2 WAKE
paste block) and `docs/project/project-instructions.md` (ROUTINE-FIRED
protocol, with the shipped script's real state table), drift-guarded by
`tests/test_wake_ritual_docs.py` against the script source's literal state
labels. The sweep stays a live read — its output is never committed (the
probe's staleness-inversion trap).
