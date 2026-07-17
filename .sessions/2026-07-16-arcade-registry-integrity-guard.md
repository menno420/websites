# arcade-registry-integrity-guard

> **Status:** `complete` — branch `claude/arcade-registry-integrity-guard`;
> a new read-only guard test (`botsite/tests/test_arcade_registry_integrity.py`,
> 54 rows) over the four committed blocker registries. All four service suites
> green (1685 passed); kit gate green once this card flips. No source or data
> changed — the guard asserts through the shipped `botsite.blockers` schema.

## Slice
A **data-integrity guard** for the committed botsite blocker registries. The
owner-console + arcade story (availability summaries, "unblocks N cards"
chips, verification-chip ledger joins shipped in #368/#369/#371) all rest on
the `blocker` object — `owner_action` / `unblocks` / `ask_id` — being
well-formed across `arcade.json`, `catalog.json`, `products.json` and
`puddle_museum.json`. Because every loader is fail-soft (a malformed blocker
silently normalizes to `None`), bad committed data does not crash — it just
makes a blocker panel or an owner-click count quietly vanish. This guard reds
CI when the committed registry data drifts out of shape, so the silent-loss
failure mode becomes a loud test failure.

Read-only: the test asserts over the committed JSON and imports the schema
single-source-of-truth (`botsite.blockers.ASK_ID_RE` / `normalized_blocker`).
No source or data changes — a NEW test file only, zero overlap with the open
arcade/console drafts.

## Files
- `botsite/tests/test_arcade_registry_integrity.py` — the guard (new).

## What it asserts
- Every raw `blocker.ask_id` present matches the canonical `ASK_ID_RE`
  imported from `botsite/blockers.py` (no re-stated regex).
- Every committed `blocker` survives `normalized_blocker` (non-empty
  `owner_action` + `unblocks`) — no blocked card silently loses its panel.
- No duplicate identity keys within a registry (slug / edition lang).
- Orphan-reference guard: every referenced `ask_id` exists in the
  `docs/owner/OWNER-ACTIONS.md` ledger (`ID: ASK-NNNN` lines); defensively
  skips if the ledger is unreadable rather than going flaky-red.

💡 Idea: the same raw-vs-normalized delta could power a `bootstrap check`
advisory that names WHICH committed blocker degraded to `None` (silent-loss
detector), turning the guard from a red test into an actionable finding line.

📊 Model: Claude Opus · high · arcade-guard build

Previous-session review: `.sessions/2026-07-16-console-dispatch-readiness.md`
surfaced the seat dispatch-readiness chips by reusing already-computed
coverage — the same read-only, reuse-the-loader discipline this guard follows
(it asserts through the shipped schema rather than re-deriving it).

⚑ Self-initiated: no — overnight coordinator-dispatched build slice.
