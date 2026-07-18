# websites · status

updated: 2026-07-18T06:00:00Z
phase: backlog build — C15 durable ask IDs on the owner-action queue: each ⚑ ask now carries a stable content-derived id (`owner_queue.ask_uid` — the ledger `ID: ASK-NNNN` when present, else a hash of the normalized headline), and the gated `/owner/queue` writeback routes resolve their target ask BY that id instead of by the raw headline text, rejecting an unknown/stale id safely. Branch `claude/durable-ask-ids`; a NEXT-TASKS slice of the standing overnight ORDER 032.
health: green — origin/main advanced: C14 self-cleaning owner queue (#386), the orphan-claim cleanup (#387), B1 arcade live/blocked counts on dashboard /status (#388), C1 honest counts on /work /history /console (#389), A4 arcade JSON schema CI guard (#390), and R6 review bake-generator unit tests (#391) all landed. Last full four-suite run 1804 (2026-07-18, this session — 1792 + 12 new durable-ask-id tests).
last-shipped: #391 — origin/main head 8b918f4.
orders: acked=001-032 done=001-019,023-031 — unchanged. C15 ships as a backlog slice of the standing overnight ORDER 032, not an order completion.
routine: failsafe cron `trig_01FYyvu2EytWF5NSEzLU2qLD` "Websites failsafe wake" (cron `45 */2 * * *`) bound to the coordinator session; a ~15-min send_later pacemaker chain is kept alive coordinator-side. Old failsafe `trig_01VRT9F6jYNXym3nn18vVQQK` retiring (not re-armed). Tool wall: the capitalized alias `mcp__Claude_Code_Remote__list_triggers` is classifier-blocked; lowercase `mcp__claude-code-remote__list_triggers` works.
blockers: none
landing: pushed-unmerged claude/durable-ask-ids — PR #392 READY (C15 durable ask ids on the owner-action queue); merges via server-side auto-merge-enabler on green (agents cannot self-merge, classifier since 2026-07-15). Open PRs: this one.
deployed: 8b918f4 · four Railway services live (control-plane/botsite/dashboard/review). C15 touches the control-plane only — `app/owner_queue.py` (the `ask_uid`/`resolve_uid` derivation + the `uid` on each ask object), `app/owner.py` (writeback routes resolve by the durable id), `app/templates/owner_queue.html` (the hidden identifier); the `/queue.json` `uid` field is contract-pinned. No env, no workflow, no cross-service change; the CSRF/same-origin floor is preserved.
claims: no active claims (no claim filed — no active contention; committed branch-claims orphan on squash-merge, so the branch-named claim would outlive its branch and red main post-merge — the #387 cleanup class).
notes: WIND-DOWN standing — the Claude Code Projects EAP goes READ-ONLY 2026-07-21; the autonomous apparatus is being retired and the Project recreated (inventory: docs/NEXT-TASKS.md → "Wind-down / retirement"). C15 is a contained, reversible control-plane slice, independent of the retirement set.
needs-owner: the 16 ⚑ rows in docs/owner/OWNER-ACTIONS.md (mirror below) — none resolved this session.

## ⚑ OWNER-ACTION mirror (canonical: docs/owner/OWNER-ACTIONS.md) — 16 open, none resolved this session
- ASK-0001 — answer Q-0004: where live bot control lives (or keep /admin dry-run).
- ASK-0002 — create the Discord OAuth app for the future armed panel (after Q-0004).
- ASK-0003 — provision the scoped control-API token + separate armed Railway service (after Q-0004).
- ASK-0004 — create the botsite submissions PostgreSQL + connection string.
- ASK-0005 — set up PayPal Payouts + put its two credentials on the botsite service.
- ASK-0006 — decide the unwired SITE_PASSWORD on the botsite Railway service (wire or remove).
- ASK-0007 — mint the fine-grained contents-write PAT → GITHUB_TOKEN on control-plane + botsite.
- ASK-0008 — extend that PAT with PR write + store as BAKE_PAT Actions secret (unblocks hands-off nightly bake).
- ASK-0009 — delete the unused SITE_PASSWORD variable from the dashboard service.
- ASK-0010 — publish the lumen-drift-v1.3 release on gba-homebrew (unblocks the arcade Download button).
- ASK-0011 — flip product-forge Settings → Pages → Source to GitHub Actions (unblocks the games-web Play link).
- ASK-0012 — run the Gumroad publish pass for the ten publish-ready titles/products (details in docs/owner/OWNER-ACTIONS.md).
- ASK-0013 — hand off the full-res photo originals for the two wallpaper packs (details in docs/owner/OWNER-ACTIONS.md).
- ASK-0014 — pick the Ultramarine title: "The Widow's Blue" or keep Ultramarine (details in docs/owner/OWNER-ACTIONS.md).
- ASK-0015 — decide the §5 illustration gate for the two picture books + three Puddle Museum editions (details in docs/owner/OWNER-ACTIONS.md).
- ASK-0016 — arrange the native-speaker Dutch proofread for de-papieren-sinaasappel (details in docs/owner/OWNER-ACTIONS.md).

## NEXT-2-TASKS baton
1. The next NEXT-TASKS slice — e.g. B6 config-drift /env surface, or A2 cross-link games ↔ arcade.
2. The following NEXT-TASKS slice after it.
- Blocked-not-mine: O-020 / O-021 (gated on owner credentials — the ASK-0001..0009 provisioning set); R10 (workflow-touch / hub-venue — needs the owner-side hub decision).
- Standing owner-side: recreate the Project from `main` once the EAP successor is chosen + strip the retired routine/heartbeat/coordinator apparatus (this file included) — EAP goes read-only 2026-07-21.

kit: v1.17.0
