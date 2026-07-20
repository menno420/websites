# 2026-07-20 — regenerate the stale seat-digest render

> **Status:** `in-progress` — branch `claude/seat-digest-regen`, PR #<pending>.
> `bootstrap.py check --strict` flags `[seat-digest-stale]`: the committed
> `docs/seat-digest.md` differs from a fresh render of its sources (the skill
> index + capability ledger), and downstream seat prompts extract those bytes.
> This regenerates it via `python3 bootstrap.py seat-digest` (never hand-edited)
> to clear the advisory. Born red; the flip to `complete` is the LAST step.

- **📊 Model:** opus-4.8 · low · docs-only

**What this session is about:** the final hygiene item from the 2026-07-19
cycle's NEXT-2-TASKS baton (`control/status.md`): after the records-refresh
(#458) cleared the model-line + orientation-headroom advisories, the one
remaining non-exit-affecting advisory is `[seat-digest-stale]`.
`docs/seat-digest.md` is a derived render of the skill index + capability
ledger; the committed copy drifted from those sources, so a fresh
`bootstrap.py seat-digest` render re-syncs the bytes the fleet's downstream
seat prompts consume.

Work-ladder rung: order — the `control/status.md` NEXT-2-TASKS baton (item 2,
seat-digest regen), closing out the cycle's Hygiene slice.

⚑ Self-initiated: no — the status-baton hygiene follow-through.

## What was done

- `docs/seat-digest.md` — regenerated via `python3 bootstrap.py seat-digest`
  (derived render, never hand-edited); re-synced to its current sources so the
  `[seat-digest-stale]` advisory clears.
- `control/claims/seat-digest-regen.md` — work claim (deleted in the flip).
- Verified before flip: [[fill: strict result at flip]].

**Verify plan:** `python3 bootstrap.py check --strict` (confirm
`[seat-digest-stale]` no longer fires and `all checks passed`); four-suite
(`env -u DATABASE_URL python3 -m pytest tests/ botsite/tests dashboard/tests review/tests -q`)
stays green — this touches only a docs render.

## 💡 Session idea

The `[seat-digest-stale]` advisory is non-exit-affecting, so the derived render
drifts silently between hygiene passes until someone notices. A tiny CI step (or
a fast-lane check) that re-renders the seat-digest and fails if the committed
bytes differ would make the "never hand-edit; regenerate on source change"
contract executable instead of advisory. Deduped against `docs/ideas/backlog.md`
+ NEXT: not present. To capture in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

`.sessions/2026-07-20-records-refresh.md` (#458) trued `docs/current-state.md`
to the #456 ledger, trimmed boot-read 6176→2093 words to open orientation
headroom, and fixed the three off-taxonomy PL-004 model lines — clearing every
advisory except this derived-render one. This slice closes that last item so the
strict check runs fully clean.
