# 2026-07-16 — Registry blockers join the ledger by ask_id (catalog, products, puddle museum)

> **Status:** `in-progress` — branch `claude/registries-askid`; extending PR
> #360's optional blocker+ask_id object from arcade.json to the three
> remaining botsite registries (catalog.json, products.json,
> puddle_museum.json), with the ledger rows, askverify joins, blocker
> panels, and cross-surface pins to match.

- **📊 Model:** Fable (Claude 5 family) · medium · feature build

**Goal:** PR #360 gave arcade.json blockers a stable `ASK-NNNN` join key
into `docs/owner/OWNER-ACTIONS.md` and `app/askverify.py`. Its own baton
said the follow-up is cheap: "the same optional blocker+ask_id object fits
catalog.json / products.json / puddle_museum.json unchanged." This slice
does exactly that: a shared `botsite/blockers.py` normalizer (arcade's
fail-soft semantics, refactored out and imported back), optional `blocker`
objects on the not-live entries of the three registries, honest six-field
ledger rows for the genuine owner actions (Gumroad publish pass,
photo-packs originals handoff, ultramarine rename decision, §5
illustration gate, de-papieren-sinaasappel proofread), askverify REGISTRY
joins with `probe=None` + honest reasons, blocker panels on catalog /
products / puddle-museum templates mirroring arcade_detail's ledger-ref
line, and the cross-surface consistency pin extended to all four
registries. The 5 write-slice parked catalog titles get NO blocker — they
are agent work, not owner actions.

⚑ Self-initiated: no — coordinator-dispatched slice, promoted from PR
#360's close-out baton (`.sessions/2026-07-16-arcade-askid-join.md`,
"Next session should know").

## Close-out

**Evidence:**

- files touched this branch: [[fill: at flip]]
- git: branch `claude/registries-askid` from `main` @ `bd79558`; PR [[fill]].
- verify: [[fill: pytest + check --strict results at flip]]

**Judgment:**

- Decisions made: [[fill: at flip]]
- Next session should know: [[fill: at flip]]

## 💡 Session idea

[[fill: at flip]]

## ⟲ Previous-session review

[[fill: at flip]]
