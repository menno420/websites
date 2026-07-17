# Session — arcade owner-action queue panel

> **Status:** `complete`

- **📊 Model:** Claude Opus · high · botsite-feature build

## Goal
Surface the actual list of distinct pending owner clicks on `/arcade` as a consolidated "Owner action queue" panel — today the summary strip shows only a count. Menu pick A3 (docs/planning/arcade-dashboard-menu-2026-07-16.md, PR #373).

## Scope
- botsite/ only. `arcade.py` gets a pure, fail-soft `pending_owner_actions()` helper; `arcade.html` renders the panel; route passes it through. Read-only, reversible by revert. No cross-service import.

## 💡 Session idea
The owner-action queue is a natural seam for a fleet-wide inbox: catalog/products/puddle-museum already share `blockers.py`'s `{owner_action, ask_id}` schema, so `pending_owner_actions()` could generalize into one deduped cross-registry click list (menu C2) once a canonical aggregate location is decided.

## ⟲ Previous-session review
`.sessions/2026-07-16-arcade-registry-integrity-guard.md` (complete) added a build-gating schema/enum guard over the committed arcade registry — honest, well-scoped coverage that this panel now leans on: because every committed blocker is guaranteed to carry a valid `owner_action`, the queue panel can trust the registry it renders.
