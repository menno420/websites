# websites · status

updated: 2026-07-20T04:36:56Z
phase: slice 1 landed — submissions_store on shared _db shim; queue top = NAV reachability GET guard for app/ (slice 2)
health: green — four service suites green (2083 passed) + python3 bootstrap.py check --strict passes its own assertions; the only red is the by-design born-red HOLD on this session's in-progress card, released at the flip. tests/test_own_heartbeat.py 5/5.
last-shipped: #446 — botsite /testing store SQLite→Postgres dual backend (durable tester-queue data), merged 2026-07-19; main tip d4bd00b.
blockers: none
orders: acked=001-038 done=001-038 (021 closed w/ evidence #444; 037/038 done #442/#443; 036 done)
routine: failsafe cron `trig_01FYyvu2EytWF5NSEzLU2qLD` "Websites failsafe wake" `45 */2 * * *` ARMED · bound to the predecessor session_012kFFGxzt9ntSDi7jkE36z3; rebind rides the hub venue (this coordinator's trigger/send_later arming is classifier-denied). send_later chain: none pending.
landing: pushed-unmerged claude/submissions-store-shim (PR #449) — routes botsite/submissions_store.py onto the shared botsite/_db.py shim (_Conn/_Row/_pg_row_factory), making the shim a genuine two-consumer module (born-red, self-lands on the complete flip). Prior PRs #434–#448 are all terminal (merged/closed); this is the only open PR.
deployed: main d4bd00b (#446) · four Railway services (control-plane / botsite / dashboard / review, superbot-websites project); Railway redeploys on merge (merge=deploy), live re-verification is the follow-up. botsite /submit is DURABLE — DATABASE_URL live, Postgres-backed intake confirmed writing (ASK-0004 satisfied); this slice re-routes that live path behaviour-preservingly. The owner moderation queue GET /submit/queue.json + /testing owner reads still 503 until the botsite Discord-login vars land (ASK-0006).
claims: control/claims/submissions-store-shim-2026-07-19.md is this branch's in-flight claim, removed in this PR's flip commit so it merges away clean (no drift-gate orphan). control/claims/ otherwise holds only README.md.
needs-owner: the ⚑ rows in docs/owner/OWNER-ACTIONS.md (mirror below).

## NEXT-2-TASKS baton
1. NAV reachability GET guard for `app/` (slice 2): add a TestClient GET bucket over app/ page routes asserting non-5xx (documented allowed status set for gated pages), mirroring the PAGES_NOT_IN_NAV reachability guard the other three services got (#416/#418/#421) — app/ is the last service without it. Test-only, zero prod risk. Per docs/plans/next-cycle-2026-07-19.md slice 2.
2. askverify probes for observable-but-unprobed asks (slice 3): add automated probes that assert the observable state of asks currently tracked only by prose (e.g. the /submit durable-intake and the Discord-login-gated owner surfaces), so ASK status is machine-checked rather than hand-asserted. Per docs/plans/next-cycle-2026-07-19.md slice 3.

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
