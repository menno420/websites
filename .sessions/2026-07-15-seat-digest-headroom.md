# 2026-07-15 — seat digest regen + orientation headroom

> **Status:** `in-progress` — branch `claude/seat-digest-headroom-20260715`;
> two payload slices: `docs/seat-digest.md` regeneration and an
> orientation-budget trim of the boot-read set.

- **📊 Model:** Claude Fable · medium · docs-only (seat-digest regen + boot-read trim)

**What this session is about:** two small maintenance slices in one PR.
(1) `docs/seat-digest.md` — the committed digest is stale against a fresh
render (pre-existing `seat-digest-stale` advisory, flagged as the baton in
`.sessions/2026-07-15-walls-cards-heartbeat.md`) and is missing the three
2026-07-15 walls PR #346 appended to `docs/CAPABILITIES.md`; regenerate
with `python3 bootstrap.py seat-digest` (derived render — never
hand-edited). (2) Orientation headroom — the boot-read set sits at
6997/7000 words (3 words of headroom; split: `docs/current-state.md` 6264
· `docs/AGENT_ORIENTATION.md` 733). Trim stale or duplicated narrative
from `docs/current-state.md` — superseded in-flight notes, history already
preserved in git and session cards — never factual claims still true,
never the Status badge placement, never `control/` files. Target: [[fill:
achieved headroom after trim]].

⚑ Self-initiated: no — dispatched under the owner's live work grant
(accept-edits session mode).

## Close-out

**Evidence:**

- files touched this branch: [[fill: file list at flip]]
- git: [[fill: branch/PR/sha evidence at flip]]
- verify: [[fill: pytest + strict-check lines at flip]]

**Judgment:**

- Decisions made: [[fill: decisions at flip]]
- Next session should know: [[fill: baton at flip]]

## 💡 Session idea

[[fill: one genuine idea, deduped against docs/ideas/, at flip]]

## ⟲ Previous-session review

[[fill: review of .sessions/2026-07-15-walls-cards-heartbeat.md at flip]]
