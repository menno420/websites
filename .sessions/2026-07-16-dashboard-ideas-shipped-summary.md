# 2026-07-16 — Dashboard /ideas: shipped-idea count on the hero

> **Status:** `complete` — branch `claude/dashboard-ideas-shipped-summary`; the
> `/ideas` backlog hero now shows `· K shipped` alongside its `N ideas` total,
> closing the inconsistency with the sibling `/bugs` hero (which already shows
> `· K open`). Backed by a pure `data_source.idea_stats(data)` helper whose
> shipped set (`done`/`implemented`) matches the per-idea badge, so the hero
> figure equals the count of green badges on the page. Read-only; +4 tests.

- **📊 Model:** Claude Opus · high · dashboard-feature build

**What this session is about:** the `/ideas` backlog page hero shows only a
raw `N ideas` total, while its sibling backlog page `/bugs` shows `N bugs · K
open` — a secondary count that tells the reader at a glance how much of the
board is actionable. This slice closes that inconsistency: a pure
`data_source.idea_stats(data)` helper counts total / shipped / open (shipped =
the same `done`/`implemented` status set the per-idea badge already greens), and
the `/ideas` hero surfaces `· K shipped` when any idea has shipped. Read-only:
no new route, no state change, no POST, no CSRF surface. Fully covered by tests.

💡 Idea: the `/status` board's per-count cards could carry the same shipped/open
split for ideas and bugs (a mini stacked figure), so the one-glance board shows
progress, not just totals.

**Previous-session review** (`.sessions/2026-07-16-games-availability-summary.md`):
exemplary single-source-of-truth discipline — the games front door reused
`arcade.availability_summary` rather than recomputing counts. This session
follows the same rule: `idea_stats`' shipped set matches the badge's own
classification so the hero figure equals the count of green badges on the page,
no drift between summary and rows.
