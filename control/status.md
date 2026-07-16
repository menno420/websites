# websites · status

updated: 2026-07-16T07:40:32Z
phase: worker session (coordinator-dispatched 2026-07-16) — arcade ask_id-join slice built as PR #360; heartbeat delegated by the coordinator.
health: green — main a0a6e66 · suite 1519 passed (full four-service run on the PR #360 branch; +16 vs main's 1503) · bootstrap check --strict pass (only the designed born-red hold on the branch's own in-progress card).
orders: acked=001-031 done=001-019,023-031 (020/021 owner-gated; 022 standing).
routine: failsafe cron 45 */2 active — armed (trig_01VRT9F6jYNXym3nn18vVQQK "Websites failsafe wake").
needs-owner: the 11 ⚑ rows in docs/owner/OWNER-ACTIONS.md (mirror below; every row carries a stable ID — verification chips and, since PR #360, the arcade blocker panels join on the ID exactly) — plus PR clicks: #357 (draft · green; landing path owner one-click mark-ready after a rate-limit denial) and #345 (do-not-automerge label — owner-lane by design; landing path owner removes label + merges).

## ⚑ OWNER-ACTION mirror (canonical: docs/owner/OWNER-ACTIONS.md)
- ASK-0001 — answer Q-0004: where live bot control lives (or keep /admin dry-run).
- ASK-0002 — create the Discord OAuth app for the future armed panel (after Q-0004).
- ASK-0003 — provision the scoped control-API token + separate armed Railway service (after Q-0004).
- ASK-0004 — create the botsite submissions PostgreSQL + connection string.
- ASK-0005 — set up PayPal Payouts + put its two credentials on the botsite service.
- ASK-0006 — set SITE_PASSWORD on the botsite Railway service.
- ASK-0007 — mint the fine-grained contents-write PAT → GITHUB_TOKEN on control-plane + botsite.
- ASK-0008 — extend that PAT with PR write + store as BAKE_PAT Actions secret (unblocks hands-off nightly bake).
- ASK-0009 — delete the unused SITE_PASSWORD variable from the dashboard service.
- ASK-0010 — publish the lumen-drift-v1.3 release on gba-homebrew (new 2026-07-16; unblocks the arcade Download button).
- ASK-0011 — flip product-forge Settings → Pages → Source to GitHub Actions (new 2026-07-16; unblocks the games-web Play link).

## Open PRs
- #360 (this session) — arcade launch-blocker panels join asks by ask_id (ledger rows ASK-0010/0011 minted; blocker.ask_id in arcade.json; askverify registry ids). Draft, born-red by design until the session card flips complete at close; landing path: card flip → quality green → server-side landing of green PRs.
- #357 — rerun-ci preflight names failed JOBS. CI-green draft; ready-flip owner-gated after a denial (rate-limit at flip time) — owner one-click: mark ready.
- #345 — quality-main-sweep workflow. Green, labeled do-not-automerge — owner-lane by design; owner removes the label + merges.

## NEXT-2-TASKS baton
1. Extend the structured blocker schema (owner_action / unblocks / ask_id) to the other botsite registries — catalog.json's hard-gated/parked entries, products.json coming-soon notes, puddle_museum.json's no-edition state — so every "not live yet" public card renders the same honest panel and joins the ledger by ID (the 2026-07-15 arcade-detail card's 💡 idea; the join key is now proven end-to-end by PR #360).
2. Release-drift banner via the shared ask_id: scripts/healthcheck.py already imports both app and botsite — join each arcade blocker's ask_id to its askverify probe and FLAG when the probe says done-detected while the registry still says unavailable (the coordinator-flagged follow-up parked at PR #349; now buildable with zero new botsite network surface).

kit: v1.17.0
