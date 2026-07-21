# websites · status

updated: 2026-07-20T18:00:00Z
phase: cycle 2026-07-20 planned (docs/plans/next-cycle-2026-07-20.md); the seat-buildable hardening queue drained through #461. Remaining seat-buildable work is the product frontier (S1 edition auto-drafter top); owner-gated items (Discord-login vars) unchanged.
health: green — four service suites green + python3 bootstrap.py check --strict passes its own assertions (only advisory warnings remain, all on untouched files / non-exit-affecting). tests/test_own_heartbeat.py 5/5.
last-shipped: #459 — docs: regenerate seat-digest render (clears stale advisory), merged 2026-07-20; main tip 098c411.
blockers: none
orders: acked=001-038 done=001-038 (021 closed w/ evidence #444; 037/038 done #442/#443; 036 done)
routine: failsafe cron `trig_01FYyvu2EytWF5NSEzLU2qLD` "Websites failsafe wake" `45 */2 * * *` ARMED · bound to the predecessor session_012kFFGxzt9ntSDi7jkE36z3; rebind rides the hub venue (this coordinator's trigger/send_later arming is classifier-denied). send_later chain: none pending (walled).
landing: all-merged — #448–#459 all terminal, 0 open claude/* PRs. This cycle's hardening + docs slices are fully merged to main; no drift-gate orphans.
deployed: main 098c411 · four Railway services (control-plane / botsite / dashboard / review, superbot-websites project); Railway redeploys on merge (merge=deploy), live re-verification is the follow-up. botsite /submit is DURABLE — DATABASE_URL live, Postgres-backed intake confirmed writing (ASK-0004 satisfied). The owner moderation queue GET /submit/queue.json + /testing owner reads still 503 until the botsite Discord-login vars land (ASK-0006/0017).
claims: control/claims/ holds only README.md — no drift-gate orphans.
needs-owner: the ⚑ rows in docs/owner/OWNER-ACTIONS.md (mirror below).

## NEXT-2-TASKS baton
1. S1 review edition auto-drafter (per docs/plans/next-cycle-2026-07-20.md): the top seat-buildable slice. Review editions are unbuilt — only edition-001 (2026-07-11) exists, review-bake.yml bakes data mirrors but no editions — so the channel is silent, not owner-gated. Draft `review/gen_edition.py` from the committed baked mirrors following the editions.py reproducible-from-source doctrine. Queue after: S2 arcade catalog growth, S3 cross-service fleet nav strip.
2. Owner sitting on ASK-0006 + ASK-0017: set the four Discord-login vars + one redirect URI on BOTH the botsite and dashboard Railway services. That unblocks owner sign-ins (/owner/login 302, /admin/login 302) → the one /testing owner write. On completion a session runs the E2E gate verification and the new askverify console chips flip to done-detected.

## ⚑ OWNER-ACTION mirror (canonical: docs/owner/OWNER-ACTIONS.md)
- ASK-0003 — provision the scoped control-API token + separate armed Railway service (the armed bot-control write path, stubbed).
- ASK-0005 — set up PayPal Payouts + put its two credentials on the botsite service.
- ASK-0006 — set the four Discord-login vars (+ redirect URI) on the botsite Railway service (SITE_PASSWORD now optional fallback); this also unlocks the /submit owner moderation queue (GET /submit/queue.json) + /testing owner reads now that intake persists. Its console chip now auto-flips: /owner/login 302 (Discord) or /testing/owner 401 (SITE_PASSWORD) → done-detected.
- ASK-0009 — delete the unused SITE_PASSWORD variable from the dashboard service.
- ASK-0012 — run the Gumroad publish pass for the ten publish-ready titles/products.
- ASK-0013 — hand off the full-res photo originals for the two wallpaper packs.
- ASK-0014 — pick the Ultramarine title: "The Widow's Blue" or keep Ultramarine.
- ASK-0015 — decide the §5 illustration gate for the two picture books + three Puddle Museum editions.
- ASK-0016 — arrange the native-speaker Dutch proofread for de-papieren-sinaasappel.
- ASK-0017 — set the same four Discord-login values + one redirect URI on the dashboard service (unlocks the dashboard admin surface's owner-gated dry-run actions). Its console chip now auto-flips: /admin/login 302 → done-detected.

kit: v1.17.0
