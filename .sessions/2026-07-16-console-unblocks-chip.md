# 2026-07-16 — owner-console "unblocks N cards" reverse-join chip

> **Status:** `in-progress`

- **📊 Model:** Claude Opus · high · console-feature build (owner-console unblocks-N-cards reverse-join chip)

**What this session is about:** the owner console already tells the owner
*what* each open owner-action ask is and whether a read-only probe can
verify it (`app/askverify.py` verdict chips). It does not tell him the
*blast radius* — how many public product cards are held closed behind that
one ask. This session adds the reverse join: a pure, testable helper
(`app/card_gating.py`) loads the four committed botsite registries
(`botsite/data/{arcade,catalog,products,puddle_museum}.json`) from disk,
walks their `blocker.ask_id` fields, and returns `ask_id -> [cards it
gates]` aggregated across every registry. `app/owner.py` wires the count
onto each queue item and `owner_queue.html` renders an "unblocks N cards"
chip beside the existing verify chip. Read-only end to end: no new route,
no state change, no CSRF surface.

⚑ Self-initiated: no — dispatched build slice.

## Close-out

**Evidence:** _(filled at the flip commit)_

**Judgment:** _(filled at the flip commit)_

## 💡 Session idea

_(filled at the flip commit)_

## ⟲ Previous-session review

_(filled at the flip commit)_
