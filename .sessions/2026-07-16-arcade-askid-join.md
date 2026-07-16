# 2026-07-16 — Arcade: launch-blocker panels join asks by ask_id

> **Status:** in-progress

**Goal:** the arcade per-game launch-blocker panels (PR #349) and the owner
console's verification chips (PR #358) tell the same story from the same
facts — but they share NO join key. The only machine join between a blocker
and its ask today is `app/askverify.py`'s two arcade probe entries
(`lumen-drift-release`, `product-forge-pages`), which sit `ask_id=None` and
bind purely by brittle keyword signatures over ask headline text. This slice
switches that join to the ledger's stable `ASK-NNNN` id as the PRIMARY key,
keeping the signature scan as the fallback for id-less rows.

**Scope (matches `control/claims/2026-07-16-arcade-askid-join.md`):**

- `docs/owner/OWNER-ACTIONS.md` — the two arcade owner clicks become real
  ledger rows with stable ids (append-only scheme: next free numbers
  ASK-0010 / ASK-0011); they were previously promises on the public arcade
  page with no ledger row at all.
- `app/askverify.py` — the two arcade REGISTRY entries flip from
  `ask_id=None` (signature-only) to their new exact ids; `match()` already
  prefers exact-ID with signature fallback (PR #358), so the join flips key.
- `botsite/data/arcade.json` + `botsite/arcade.py` — each `blocker` object
  gains an optional, fail-soft `ask_id` referencing its ledger row; the
  detail page renders the ledger ref. Both surfaces now flip from one
  ledger edit.
- Tests: botsite suite (schema + panel), tests/ suite (ID-primary join even
  when the old brittle key would mismatch; ID-less signature fallback;
  committed arcade.json ↔ ledger ↔ registry consistency pin).

**Plan:** ledger rows first (ids minted), registry ids second, arcade
schema + template third, tests alongside each; full four-suite verify +
`bootstrap.py check --strict` before every push; heartbeat overwrite
(coordinator-delegated) on this branch; card flips complete last.

⚑ Self-initiated: no — coordinator-dispatched slice promoted from the
NEXT-2-TASKS baton (`.sessions/2026-07-15-arcade-detail.md` idea, promoted
by `control/status.md` at a0a6e66).
