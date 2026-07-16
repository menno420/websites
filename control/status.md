# websites · status

updated: 2026-07-16T09:00:34Z
phase: worker session (coordinator-dispatched 2026-07-16) — release-drift healthcheck slice built as PR #365 (fifth healthcheck pass check_release_drift(): registry blockers joined to askverify probes by exact ask_id); close-out worker ran heartbeat + card flip.
health: green — main 475d41c (PR #362 landed) · suite 1588 passed (full four-service run on the PR #365 branch; +10 vs main's 1578) · bootstrap check --strict green except the born-red hold on this session's card (released by the flip in this same push).
orders: acked=001-031 done=001-019,023-031 (020/021 owner-gated; 022 standing).
routine: failsafe cron 45 */2 active — armed (trig_01VRT9F6jYNXym3nn18vVQQK "Websites failsafe wake").
needs-owner: the 16 ⚑ rows in docs/owner/OWNER-ACTIONS.md (mirror below; every row carries a stable ID — verification chips, all four botsite registries' blocker panels (PRs #360/#362), and since PR #365 the healthcheck's release-drift pass all join on the ID exactly) — plus PR clicks: #357 (draft · green; landing path owner one-click mark-ready after a rate-limit denial) and #345 (do-not-automerge label — owner-lane by design; landing path owner removes label + merges).

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
- ASK-0010 — publish the lumen-drift-v1.3 release on gba-homebrew (unblocks the arcade Download button; machine-probed — the #365 drift pass now watches it every healthcheck).
- ASK-0011 — flip product-forge Settings → Pages → Source to GitHub Actions (unblocks the games-web Play link; machine-probed — same drift-pass watch).
- ASK-0012 — run the Gumroad publish pass for the ten publish-ready titles/products (details in docs/owner/OWNER-ACTIONS.md).
- ASK-0013 — hand off the full-res photo originals for the two wallpaper packs (details in docs/owner/OWNER-ACTIONS.md).
- ASK-0014 — pick the Ultramarine title: "The Widow's Blue" or keep Ultramarine (details in docs/owner/OWNER-ACTIONS.md).
- ASK-0015 — decide the §5 illustration gate for the two picture books + three Puddle Museum editions (details in docs/owner/OWNER-ACTIONS.md).
- ASK-0016 — arrange the native-speaker Dutch proofread for de-papieren-sinaasappel (details in docs/owner/OWNER-ACTIONS.md).

## Open PRs
- #365 (this session) — release-drift healthcheck pass: check_release_drift() joins every registry blocker to its askverify probe by exact ask_id; FLAGs done-detected-but-still-gated drift and ledger drift, lists probe-less asks honestly. Ready-for-review; auto-merge (squash) armed by github-actions; landing path: card flip (this push) → quality green → auto-merge squashes into main.
- #361 — rescue PR carrying a straggler drafted session card; draft, born-red by design (unresolved [[fill:]] slots); a follow-up close-out session must complete it before it can land.
- #363 — rescue lifeboat: second straggler card from a detached-HEAD session (same filename as #361's card, DIFFERENT content); draft on purpose, owner/coordinator decides land-or-close. (Sibling lifeboat #364 no longer shows in the open-PR list as of this heartbeat.)
- #359 — automated fleet-data bake (data-only, bot-authored); waits on its dispatched quality run / auto-merge; base a0a6e66 predates #362's land.
- #357 — rerun-ci preflight names failed JOBS. CI-green draft; ready-flip owner-gated after a denial (rate-limit at flip time) — owner one-click: mark ready.
- #345 — quality-main-sweep workflow. Green, labeled do-not-automerge — owner-lane by design; owner removes the label + merges.

## NEXT-2-TASKS baton
1. (carry-forward) Owner-console reverse join: for each open ask, count and list the public cards its ask_id unblocks across all four botsite registries (ASK-0012 alone un-gates 14 cards) — an "unblocks N cards" chip on the console asks panel, read-only, no new POST surface.
2. Owner-console release-drift chip: surface check_release_drift()'s verdicts on the gated /owner console (read-only; reuses the same ask_id join — the healthcheck output shipped in #365 is the alert surface, the chip is the glanceable one).

note: the #355 SIM-REQUEST (botsite banner doctrine A/B) remains UNANSWERED — the #365 healthcheck pass deliberately sidestepped it (zero new botsite surface); the botsite-page release-drift banner stays unbuilt until the manager answers.

kit: v1.17.0
