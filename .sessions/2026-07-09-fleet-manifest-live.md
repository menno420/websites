# 2026-07-09 — /fleet lane set from the live manifest

> **Status:** `in-progress` — born-red card; flips to `complete` as the deliberate last step once the work is present and verified.

- **📊 Model:** Opus 4.8 · worker · fleet-manifest-live

**What this session is about to do:** self-directed improvement on the `/fleet`
control-plane page — derive the fleet lane set **live** from the manager's
canonical manifest (`menno420/superbot` → `docs/eap/fleet-manifest.md`) instead of
the hand-kept `config.FLEET_LANES` copy, with an honest fallback to that list when
the manifest can't be fetched/parsed; and fix the websites dogfood `control/status.md`
timestamp to a full ISO value so its own `/fleet` row shows a real freshness age.
This resolves the D-0021 "lane-set is hand-kept / drift risk" ⚑ flagged to the owner.
