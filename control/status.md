# websites · status

updated: 2026-07-20T04:22:43Z
phase: planning pass v2 landed; queue top = submissions_store→_db._Conn shim
health: green — four service suites green (2070 passed) + python3 bootstrap.py check --strict passes its own assertions; the only red is the by-design born-red HOLD on this session's in-progress card, released at the flip. tests/test_own_heartbeat.py 5/5.
last-shipped: #446 — botsite /testing store SQLite→Postgres dual backend (durable tester-queue data), merged 2026-07-19; main tip d4bd00b.
blockers: none
orders: acked=001-038 done=001-038 (021 closed w/ evidence #444; 037/038 done #442/#443; 036 done)
routine: failsafe cron `trig_01FYyvu2EytWF5NSEzLU2qLD` "Websites failsafe wake" `45 */2 * * *` ARMED · bound to the predecessor session_012kFFGxzt9ntSDi7jkE36z3; rebind rides the hub venue (this coordinator's trigger/send_later arming is classifier-denied). send_later chain: none pending.
landing: pushed-unmerged claude/botsite-db-shim — this branch's botsite/_db.py shim extraction + CAPABILITIES wall fix + heartbeat true (born-red, self-lands on the complete flip). Prior PRs #434–#446 are all terminal (merged/closed); 0 open before this PR.
deployed: main d4bd00b (#446) · four Railway services (control-plane / botsite / dashboard / review, superbot-websites project); Railway redeploys on merge (merge=deploy), live re-verification is the follow-up. botsite /submit is DURABLE — DATABASE_URL live, Postgres-backed intake confirmed writing (ASK-0004 satisfied); the owner moderation queue GET /submit/queue.json + /testing owner reads still 503 until the botsite Discord-login vars land (ASK-0006).
claims: control/claims/botsite-db-shim.md is this branch's in-flight claim, removed in this PR's flip commit so it merges away clean (no drift-gate orphan). control/claims/ otherwise holds only README.md.
needs-owner: the ⚑ rows in docs/owner/OWNER-ACTIONS.md (mirror below).

## NEXT-2-TASKS baton
1. Route `submissions_store` onto `_db._Conn` (make the shim real): migrate botsite/submissions_store.py off its inline per-function psycopg.connect onto the _Conn/_Row/_pg_row_factory plumbing botsite/_db.py now exports and testing_store.py already consumes — the second copy before it drifts. Behaviour-preserving; extend botsite/tests store tests to assert dual-backend behaviour-identical (run env -u DATABASE_URL). Baton item, per docs/plans/next-cycle-2026-07-19.md slice 1.
2. NAV reachability GET guard for app/ (slice 2): add a TestClient GET bucket over app/ page routes asserting non-5xx (documented allowed status set for gated pages), mirroring the PAGES_NOT_IN_NAV reachability guard the other three services got (#416/#418/#421) — app/ is the last service without it. Test-only, zero prod risk. Per docs/plans/next-cycle-2026-07-19.md slice 2.

## ⚑ OWNER-ACTION mirror (canonical: docs/owner/OWNER-ACTIONS.md)
- ASK-0003 — provision the scoped control-API token + separate armed Railway service (the armed bot-control write path, stubbed).
- ASK-0005 — set up PayPal Payouts + put its two credentials on the botsite service.
- ASK-0006 — set the four Discord-login vars (+ redirect URI) on the botsite Railway service (SITE_PASSWORD now optional fallback); this also unlocks the /submit owner moderation queue (GET /submit/queue.json) + /testing owner reads now that intake persists.
- ASK-0009 — delete the unused SITE_PASSWORD variable from the dashboard service.
- ASK-0012 — run the Gumroad publish pass for the ten publish-ready titles/products.
- ASK-0013 — hand off the full-res photo originals for the two wallpaper packs.
- ASK-0014 — pick the Ultramarine title: "The Widow's Blue" or keep Ultramarine.
- ASK-0015 — decide the §5 illustration gate for the two picture books + three Puddle Museum editions.
- ASK-0016 — arrange the native-speaker Dutch proofread for de-papieren-sinaasappel.
- ASK-0017 — set the same four Discord-login values + one redirect URI on the dashboard service (unlocks the dashboard admin surface's owner-gated dry-run actions).

kit: v1.17.0
