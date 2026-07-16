# websites · status

updated: 2026-07-16T08:29:03Z
phase: worker session (coordinator-dispatched 2026-07-16) — registries ask_id-join slice built as PR #362 (catalog/products/puddle-museum blockers join the ledger); finishing worker ran heartbeat + card flip.
health: green — main bd79558 (PR #360 landed) · suite 1578 passed (full four-service run on the PR #362 branch; +59 vs main's 1519) · bootstrap check --strict pass after the card flip (born-red hold released).
orders: acked=001-031 done=001-019,023-031 (020/021 owner-gated; 022 standing).
routine: failsafe cron 45 */2 active — armed (trig_01VRT9F6jYNXym3nn18vVQQK "Websites failsafe wake").
needs-owner: the 16 ⚑ rows in docs/owner/OWNER-ACTIONS.md (mirror below; every row carries a stable ID — verification chips and, since PRs #360/#362, all four botsite registries' blocker panels join on the ID exactly) — plus PR clicks: #357 (draft · green; landing path owner one-click mark-ready after a rate-limit denial) and #345 (do-not-automerge label — owner-lane by design; landing path owner removes label + merges).

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
- ASK-0012 — run the Gumroad publish pass for the ten publish-ready titles/products (new 2026-07-16 via PR #362; details in docs/owner/OWNER-ACTIONS.md).
- ASK-0013 — hand off the full-res photo originals for the two wallpaper packs (new 2026-07-16 via PR #362; details in docs/owner/OWNER-ACTIONS.md).
- ASK-0014 — pick the Ultramarine title: "The Widow's Blue" or keep Ultramarine (new 2026-07-16 via PR #362; details in docs/owner/OWNER-ACTIONS.md).
- ASK-0015 — decide the §5 illustration gate for the two picture books + three Puddle Museum editions (new 2026-07-16 via PR #362; details in docs/owner/OWNER-ACTIONS.md).
- ASK-0016 — arrange the native-speaker Dutch proofread for de-papieren-sinaasappel (new 2026-07-16 via PR #362; details in docs/owner/OWNER-ACTIONS.md).

## Open PRs
- #362 (this session) — catalog/products/puddle-museum blockers join the ledger by ask_id (ledger rows ASK-0012..0016; shared botsite/blockers.py normalizer; blocker panels on all three pages; four-registry cross-surface pin). Ready-for-review, cross-agent reviewed APPROVE; auto-merge (squash) armed; landing path: card flip (this heartbeat's session) → quality green → auto-merge squashes into main.
- #361 — rescue PR carrying a straggler drafted session card; draft, born-red by design (unresolved [[fill:]] slots); a follow-up session must complete the close-out before it can land.
- #359 — automated fleet-data bake (data-only, bot-authored); waits on its dispatched quality run / auto-merge, base predates #360's land.
- #357 — rerun-ci preflight names failed JOBS. CI-green draft; ready-flip owner-gated after a denial (rate-limit at flip time) — owner one-click: mark ready.
- #345 — quality-main-sweep workflow. Green, labeled do-not-automerge — owner-lane by design; owner removes the label + merges.

## NEXT-2-TASKS baton
1. (carry-forward) Release-drift banner via the shared ask_id: scripts/healthcheck.py already imports both app and botsite — join each blocker's ask_id to its askverify probe and FLAG when the probe says done-detected while the registry still says unavailable (parked at PR #349; buildable with zero new botsite network surface).
2. Owner-console reverse join: for each open ask, count and list the public cards its ask_id unblocks across all four botsite registries (ASK-0012 alone un-gates 14 cards) — an "unblocks N cards" chip on the console asks panel, read-only, no new POST surface.

kit: v1.17.0
