# 2026-07-10 — `.sessions/` card template + ender checklist (queue-state NEXT item 3)

> **Status:** `complete` — PR #64 (`claude/session-card-template`),
> squash-merge on `quality` green.

- **📊 Model:** Claude Fable 5 · worker · routine-fired build slice

**What this session was about:** the 20:00Z wake of the 4-hourly routine.
Work-ladder rung 2 (queue-state NEXT list): inbox at HEAD has no order past 008
and `control/status.md` reports done=001-008, so the first rung with work is
the NEXT list — item 2 (manifest smoke check) landed as PR #59, leaving
**item 3: the `.sessions/` card template carrying the `📊 Model:` line + ender
checklist**, also `planned` in `docs/ideas/backlog.md`, "so no future
grandfather backfill (the ORDER 004 class) is ever needed."

## What was done

- **`.sessions/README.md`** — the deliverable: a copy-paste card template
  (fenced block) whose sections are exactly the four gate needles
  (`**Status:**` born-red form, `📊 Model:` at FAMILY level, `## 💡 Session
  idea` with the REQUIRED one-line "worth having because", `## ⟲
  Previous-session review`), plus a work-ladder-rung prompt and a verification
  line with real output slots — followed by a 7-item **ender checklist** run
  before flipping `complete` (flip-last, family-only model naming, idea dedup +
  capture in `backlog.md`, review line, real test/check output, no `[[fill:`
  leftovers, heartbeat-last).
- **Placement decision (the load-bearing bit):** the template is EMBEDDED in
  the README, not shipped as `.sessions/TEMPLATE.md` — verified against
  `bootstrap.py` (`latest_session_log` skips only `README.md`) and
  `quality.yml` (card derivation: `'.sessions/*.md' ':!.sessions/README.md'`,
  then `tail -1`): a standalone template file would be picked up as this PR's
  session card and/or the mtime-fallback card of every future card-less PR,
  and its born-red example status would red the gate. The README now documents
  this trap explicitly ("Do not add one").
- **`docs/ideas/backlog.md`** — card-template idea moved `planned` → Built
  (with the placement rationale); session idea appended as `captured`.
- **`docs/planning/queue-state-2026-07-09-winddown.md`** — NEXT items 2 and 3
  struck DONE (item 2 = PR #59; the addendum's "not yet merged / branch
  pushed" passage about the 16:01Z session was stale — that work was rescued
  and merged as PR #59, now said so); resume point moved to **NEXT item 4**
  (heartbeat enrichment).
- Sibling-session note: woke 6 minutes after PR #63 (`claude/routine-prompt-doc`,
  READY, card complete) was opened by a concurrent session; deliberately left
  it to its own session and kept this diff off `docs/project/README.md` to
  avoid a merge conflict.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests -q` —
  **143 passed**; `python3 bootstrap.py check --strict` — green with this
  card complete (deps via `scripts/setup-env.sh`, summary "failures: none").

⚑ Self-initiated: no — queue-state NEXT item 3 (rung 2 of the work ladder),
also `planned` in `docs/ideas/backlog.md`.

## 💡 Session idea

**Open-PR awareness at wake (sibling-session collision check)** — one
wake-ritual step listing open PRs + PR-less unmerged `claude/*` branches
before picking a work rung. Worth having because concurrent sessions are now
the norm (this wake started 6 minutes after a sibling opened PR #63, and the
queue-state ledger still called merged work "not yet merged") — one glance at
live open work prevents duplicate builds, shared-file merge conflicts, and
false rescue alarms, the order-claim fix applied to branches. Deduped against
`docs/ideas/backlog.md` + queue-state NEXT: heartbeat enrichment's `landing:`
line covers a session's OWN branch only; nothing covers siblings'. Captured in
`docs/ideas/backlog.md` +
`docs/ideas/open-pr-awareness-at-wake-2026-07-10.md`.

## ⟲ Previous-session review

The previous wake pair (#61 ladder + #62 kit v1.7.0) shipped clean bounded
slices with honest evidence, but left `control/status.md` stale after the
last merge (heartbeat still says `kit: v1.6.0`, HEAD `f6e3cc3`, "#61 pending"
— all three superseded by #61/#62 landing) — heartbeat-LAST means after the
final merge of the session, not before it; this session's close-out
overwrites it.
