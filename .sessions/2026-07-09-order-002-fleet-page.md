# 2026-07-09 — ORDER 002 · /fleet page

> **Status:** `in-progress`

- **📊 Model:** Opus 4.8 · worker · fleet-order-002

**What this session is about to do:** execute fleet ORDER 002 (control/inbox.md,
P1) — build a public `/fleet` page on the control-plane board that renders **every
fleet lane's `control/status*.md`** as one glanceable heartbeat screen, so the owner
can see which agents are running and how far along they are without opening each
session one by one. One row/card per lane (the 10 lanes named in the order and the
`docs/eap/fleet-manifest.md` registry): parsed heartbeat fields (updated-age with a
stale badge, phase, health with a green/red/red-by-design indicator, last-shipped,
blockers, ⚑ needs-owner), plus last-commit age + open-PR count per repo, the full
status body rendered as markdown, and a GitHub deep-link. Reuses the app's TTL-cached
github layer + markdown renderer; honest per-lane absence/error banners; nav link;
mobile-safe; tests. Ships forward-only through the `quality` gate; control-plane
auto-deploys on merge; live-verified against the running deploy.
