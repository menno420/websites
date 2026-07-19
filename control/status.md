# websites · status

updated: 2026-07-19T11:30:46Z
phase: PR #441 landing — the born-red botsite `/submit` live-badge fix + ASK-0004/ASK-0002 ledger finalize. ORDER 034 is now DONE: the owner set `DATABASE_URL` on botsite in his 2026-07-19 Railway hub session, botsite redeployed 2026-07-19T08:27:36Z and a live POST `/submit` persisted a real Postgres row — durable intake verified live. This PR gates the stale "Stub — not wired" copy on `intake_live` so it disappears now that the store is live, and marks ASK-0004 (botsite DATABASE_URL) + ASK-0002 (control-plane Discord login) satisfied-with-evidence. Moderation of the stored submissions still needs `SITE_PASSWORD` on botsite (ASK-0006).
health: green — four service suites green + python3 bootstrap.py check --strict green; tests/test_own_heartbeat.py 5/5.
last-shipped: #440 — control heartbeat true (ORDER 036 discharged, landing/baton), merged 2026-07-19; main tip f8caa03.
blockers: none
orders: acked=001-037 done=001-020,022-037 (021 open — owner-gated; 034 done — durable botsite /submit intake verified live 2026-07-19: DATABASE_URL set on botsite resolving to the Postgres service, redeploy 08:27:36Z, a live POST /submit persisted a real Postgres row; 036 discharged — BAKE_PAT landing path proven, ASK-0008 finalized via merged PR #439; 037 done — botsite owner login unified on Discord OAuth, PR #442 landing on green, ASK-0006 reshaped to the fleet-wide Discord login with SITE_PASSWORD as optional fallback).
routine: failsafe cron `trig_01FYyvu2EytWF5NSEzLU2qLD` "Websites failsafe wake" `45 */2 * * *` ARMED · next 2026-07-19T08:45Z · last-fired 2026-07-19T06:45Z; bound to the predecessor session_012kFFGxzt9ntSDi7jkE36z3; rebind rides the hub venue (this coordinator's trigger/send_later arming is classifier-denied). send_later chain: none pending.
landing: pushed-unmerged claude/botsite-submit-live-badge — this branch's /submit live-badge fix + ASK-0004/ASK-0002 ledger finalize (PR #441; born-red, self-lands on the complete flip). Prior coordinator PR #440 merged (f8caa03); no other open PRs.
deployed: main f8caa03 (#440) · four Railway services (control-plane / botsite / dashboard / review, superbot-websites project); Railway redeploys on merge, live re-verification is the follow-up (merge=deploy). botsite /submit is now DURABLE — DATABASE_URL live, Postgres-backed intake confirmed writing (ASK-0004 satisfied); the owner moderation queue GET /submit/queue.json still returns 503 until SITE_PASSWORD lands on botsite (ASK-0006).
claims: control/claims/botsite-submit-live-badge.md is this branch's in-flight claim, removed in this PR's flip commit so it merges away clean (no drift-gate orphan). control/claims/ otherwise holds only README.md.
needs-owner: the ⚑ rows in docs/owner/OWNER-ACTIONS.md (mirror below).

## NEXT-2-TASKS baton
1. Build the botsite `/submit` moderation → GitHub-issue mirror now that intake persists (rework Q5); with ORDER 037 landed (PR #442), the owner queue read-back GET /submit/queue.json + /testing/owner now unlock via the fleet-wide Discord login (ASK-0006 reshaped — redirect URI + the four DISCORD_*/OWNER_* vars on botsite; SITE_PASSWORD optional fallback).
2. /testing SQLite→Postgres port (deferred from PR #425): bring the botsite submissions-store test coverage to Postgres parity now that the DB exists.

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
