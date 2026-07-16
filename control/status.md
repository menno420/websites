# websites · status

updated: 2026-07-16T20:49:17Z
phase: failsafe-wake session — no active send_later work-loop chain was found anywhere in the fleet for this project (checked the full trigger set; only the 2h failsafe cron itself was armed) despite a burst of landed PRs earlier today; trued this heartbeat to current main HEAD and re-armed the loop.
health: green — main da63857 (#357 landed, latest of a run of merges this heartbeat had not yet recorded: #345, #368, #369, #370, #357) · two feature branches pushed-unmerged, not yet checked for CI/mergeable state this session: claude/arcade-catalog-blockers (730e540), claude/games-availability-summary (d0ead52) — next session should verify and land or continue them.
orders: acked=001-031 done=001-019,023-031 (020/021 owner-gated; 022 standing).
routine: armed · cron 45 */2 (trig_01Cn7F2UvE62uDykSYQCDhtF "Websites failsafe wake") · re-armed a 15-min continue-the-work-loop send_later chain this heartbeat since none was found active.
landing: pushed-unmerged claude/failsafe-heartbeat-20260716-2049 (this status.md overwrite — no GitHub API scope in this session to open a PR; attempted a direct control-only push to main as a fallback, see notes for outcome)
needs-owner: the 16 ⚑ rows in docs/owner/OWNER-ACTIONS.md (mirror below; every row carries a stable ID — verification chips, all four botsite registries' blocker panels (PRs #360/#362), and since PR #365 the healthcheck's release-drift pass all join on the ID exactly). PR-click items #357 and #345 are DROPPED from this list — both merged to main this session's git log shows, so the asks are resolved; withdrawing per the control/README hygiene rule (expire stale asks every session).

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
(unverified this session — no GitHub API scope; the below is inferred from git branch state only, not live CI/mergeable status)
- #361 — rescue PR carrying a straggler drafted session card; draft, born-red by design (unresolved [[fill:]] slots); a follow-up close-out session must complete it before it can land.
- #363 — rescue lifeboat: second straggler card from a detached-HEAD session (same filename as #361's card, DIFFERENT content); draft on purpose, owner/coordinator decides land-or-close.
- #359 — automated fleet-data bake (data-only, bot-authored); waits on its dispatched quality run / auto-merge; base a0a6e66 predates #362's land.
- claude/arcade-catalog-blockers (branch tip 730e540) — arcade catalog blockers + availability summary strip; session card flipped complete; not yet on main — next session should check its PR's CI/mergeable state.
- claude/games-availability-summary (branch tip d0ead52) — games front door Fleet Arcade launch-readiness summary; session card flipped complete; not yet on main — next session should check its PR's CI/mergeable state.

## NEXT-2-TASKS baton
Both prior baton items shipped since the last heartbeat (unblocks-N-cards chip → #368; release-drift chip → #370). Baton is empty — next session should pick fresh self-initiated work per the ⚑ needs-owner / notes below, or land the two pending branches above.

note: the #355 SIM-REQUEST (botsite banner doctrine A/B) remains UNANSWERED — still sidestepped, zero new botsite surface since; the botsite-page release-drift banner stays unbuilt until the manager answers. This heartbeat is a failsafe-wake catch-up, not a build session — it did not independently verify CI/mergeable state on the two pending branches above, only that they exist pushed and unmerged.

kit: v1.17.0
