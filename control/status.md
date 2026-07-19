# websites · status

updated: 2026-07-19T18:45:23Z
phase: FAILSAFE WAKE — heartbeat truing. Main has been quiet at 8d18d54 (#443) for 6.5h after a very active day (14 PRs #436-#443 in the ~11h before that); this pass trues the stale (~6.5h old) heartbeat and flags ORDER 021 as the next buildable item now that its stated blocker (Discord OAuth decision) is resolved. No code changes made this wake — see landing/blockers.
health: green — re-synced to origin/main (8d18d54) this wake; did not re-run the full suite (prior wake already confirmed 1979 passed + strict check green at a5fdad4, and every commit since has landed via the normal quality-gated PR path, so the tree is presumed green by the same evidence the coordinator itself cites — not independently re-verified this wake).
last-shipped: #443 — dashboard Discord OAuth owner login for the admin surface (ORDER 038), merged 2026-07-19T12:15:11Z; main tip 8d18d54.
blockers: this session's `api.github.com` access is still walled — "GitHub access is not enabled for this session. An org admin must connect the Claude GitHub App for this organization." (unchanged since the first failsafe recovery at 06:53Z). A prior cross-session claim that this is session-specific, not fleet-wide, is credible (a same-day commit cf314c2 landed under the owner's own GitHub identity) — so this is very likely NOT blocking the live coordinator, only this failsafe session's own ability to open PRs.
orders: acked=001-038 done=001-020,022-038 (021 open, NO LONGER owner-gated on its stated blocker — the Discord-auth decision it was waiting on shipped across all three services via #426/#442/#443; the environments-hub feature itself is seat-buildable now. Not built this wake — a 6.5h quiet period with zero stuck PRs/red CI isn't the same failure shape as the earlier dead-pacemaker stall, and building a P2 feature from a failsafe session risks the same collision this lane hit earlier today).
routine: failsafe cron `trig_01FYyvu2EytWF5NSEzLU2qLD` "Websites failsafe wake" `45 */2 * * *` — this wake fired on it, three prior wakes (14:45/16:45 quiet-gap watch, now 18:45 confirms 6.5h with no new commits/orders/PRs). send_later pacemaker: not re-armed by this failsafe session (see notes — avoiding a second loop on top of what looks like an idle-not-dead coordinator).
landing: pushed-unmerged claude/heartbeat-truing-20260719b — this heartbeat-truing commit only (control-only diff); 0 open PRs found on GitHub at write.
deployed: main 8d18d54 (#443) · four Railway services (control-plane / botsite / dashboard / review, superbot-websites project) — not re-verified live this wake, treat as last-known-good.
claims: control/claims/ empty except README.md — no stale claims.
needs-owner: the ⚑ rows below, unchanged this wake.
notes: this is the SECOND heartbeat-truing branch pushed unmerged by this failsafe session today (first: claude/heartbeat-truing-20260719, now superseded by the coordinator's own #436 and moot). Per control/README.md's stranded-work rule, any future PR-capable session may open/merge this branch verbatim, or simply supersede it with its own truing pass — do not chase merging it specifically.

## NEXT-2-TASKS baton
1. ORDER 021 — Owner Environments Hub. Now seat-buildable: Discord OAuth (its stated blocker) is live on all three services. Scope per the inbox text: list every fleet environment (Railway projects/services, Claude Code cloud envs, GitHub secret stores) with variable NAMES only, purpose, and a deep link to where each is managed; gate behind the existing Discord owner session.
2. Build the botsite `/submit` moderation → GitHub-issue mirror now that intake persists (rework Q5) — queue read-back unlocks via the same Discord login (ASK-0006 reshaped).

## ⚑ OWNER-ACTION mirror (canonical: docs/owner/OWNER-ACTIONS.md)
- ASK-0003 — provision the scoped control-API token + separate armed Railway service (the armed bot-control write path, stubbed).
- ASK-0005 — set up PayPal Payouts + put its two credentials on the botsite service.
- ASK-0006 — decide the unwired SITE_PASSWORD on the botsite Railway service (wire or remove); wiring it also unlocks the /submit owner moderation queue (GET /submit/queue.json) now that intake persists.
- ASK-0009 — delete the unused SITE_PASSWORD variable from the dashboard service.
- ASK-0012 — run the Gumroad publish pass for the ten publish-ready titles/products.
- ASK-0013 — hand off the full-res photo originals for the two wallpaper packs.
- ASK-0014 — pick the Ultramarine title: "The Widow's Blue" or keep Ultramarine.
- ASK-0015 — decide the §5 illustration gate for the two picture books + three Puddle Museum editions.
- ASK-0016 — arrange the native-speaker Dutch proofread for de-papieren-sinaasappel.

kit: v1.17.0
