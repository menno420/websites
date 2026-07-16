# websites · status

updated: 2026-07-16T21:32:26Z
phase: failsafe-wake work-loop cycle 3 — synced, no new inbox order, nothing landed since cycle 2, ASK-0017 not yet decided. Deliberately NOT opening another feature branch this cycle: five branches from this lane are already pushed-unmerged behind the ASK-0017 wall in under an hour, and more unlandable diffs just compound the backlog without being verifiable live. Holding at heartbeat-only until either a new inbox order arrives or a branch lands. Re-armed the chain.
health: green — main da63857, unchanged this cycle · dependencies now installed (`pip install -r requirements.txt` × 4 services) and full suite run: **1631 passed** (baseline; this cycle's diff is status.md-only, no code touched) · five branches now pushed-unmerged awaiting a PR (this session cannot open one — see ASK-0017): claude/failsafe-heartbeat-20260716-2049, claude/arcade-catalog-blockers (730e540), claude/games-availability-summary (d0ead52), claude/pr-tooling-ask-20260716, claude/heartbeat-20260716-2145 (this branch, cycles 2+3) · `bootstrap check --strict` green.
orders: acked=001-031 done=001-019,023-031 (020/021 owner-gated; 022 standing).
routine: armed · cron 45 */2 (trig_01Cn7F2UvE62uDykSYQCDhtF "Websites failsafe wake") · re-armed another 15-min continue-the-work-loop send_later chain this heartbeat.
landing: pushed-unmerged claude/heartbeat-20260716-2145 (this overwrite) — same wall as last cycle, see needs-owner.
needs-owner: the 17 ⚑ rows in docs/owner/OWNER-ACTIONS.md (mirror below) — ASK-0017 is new and blocking landing itself: connect the Claude GitHub App for the org (org-admin, one-time) so routine-fired sessions can open PRs; until then expect pushed-unmerged branches to keep piling up. Also: someone with PR tooling (interactive session or the owner) should open/merge the four branches listed under health above.

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
- ASK-0010 — publish the lumen-drift-v1.3 release on gba-homebrew (unblocks the arcade Download button; machine-probed by the release-drift healthcheck).
- ASK-0011 — flip product-forge Settings → Pages → Source to GitHub Actions (unblocks the games-web Play link; machine-probed, same drift-pass watch).
- ASK-0012 — run the Gumroad publish pass for the ten publish-ready titles/products (details in docs/owner/OWNER-ACTIONS.md).
- ASK-0013 — hand off the full-res photo originals for the two wallpaper packs (details in docs/owner/OWNER-ACTIONS.md).
- ASK-0014 — pick the Ultramarine title: "The Widow's Blue" or keep Ultramarine (details in docs/owner/OWNER-ACTIONS.md).
- ASK-0015 — decide the §5 illustration gate for the two picture books + three Puddle Museum editions (details in docs/owner/OWNER-ACTIONS.md).
- ASK-0016 — arrange the native-speaker Dutch proofread for de-papieren-sinaasappel (details in docs/owner/OWNER-ACTIONS.md).
- ASK-0017 — connect the Claude GitHub App for the org (unblocks routine-fired sessions landing their own PRs; new this cycle, see health above).

## Open PRs
(unverified this session — no GitHub API scope; inferred from git branch state only)
- #361 — rescue PR carrying a straggler drafted session card; draft, born-red by design (unresolved [[fill:]] slots); a follow-up close-out session must complete it before it can land.
- #363 — rescue lifeboat: second straggler card from a detached-HEAD session (same filename as #361's card, DIFFERENT content); draft on purpose, owner/coordinator decides land-or-close.
- #359 — automated fleet-data bake (data-only, bot-authored); waits on its dispatched quality run / auto-merge; base a0a6e66 predates #362's land.
- claude/arcade-catalog-blockers, claude/games-availability-summary, claude/failsafe-heartbeat-20260716-2049, claude/pr-tooling-ask-20260716, claude/heartbeat-20260716-2145 — pushed-unmerged, see health line.

## NEXT-2-TASKS baton
Empty — no new inbox order since #031, both prior baton items shipped (#368, #370). Deliberately held this cycle: with five branches from this lane already stuck behind ASK-0017, another speculative feature branch (e.g. the "stuck landing" console chip idea) would add to an unlandable pile rather than deliver verifiable value — building it once landing unblocks, or once there's a way to verify it live, is the better sequencing. Next session: if ASK-0017 is Decided, prioritize opening/merging the five pending branches above in one pass before starting new work.

note: the #355 SIM-REQUEST (botsite banner doctrine A/B) remains UNANSWERED, unchanged this cycle. Full four-service pytest baseline now available (deps installed this cycle) — see health line.

kit: v1.17.0
