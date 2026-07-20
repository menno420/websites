# websites · status

updated: 2026-07-20T04:55:01Z
phase: slice 2 landed — app/ NAV reachability guard; queue top = askverify probes for observable-but-unprobed asks (slice 3)
health: green — four service suites green (2084 passed) + python3 bootstrap.py check --strict passes its own assertions; the only red is the by-design born-red HOLD on this session's in-progress card, released at the flip. tests/test_own_heartbeat.py 5/5.
last-shipped: #449 — botsite submissions_store routed onto the shared botsite/_db.py shim (genuine two-consumer dual backend), merged 2026-07-20; main tip 8c5aeb0.
blockers: none
orders: acked=001-038 done=001-038 (021 closed w/ evidence #444; 037/038 done #442/#443; 036 done)
routine: failsafe cron `trig_01FYyvu2EytWF5NSEzLU2qLD` "Websites failsafe wake" `45 */2 * * *` ARMED · bound to the predecessor session_012kFFGxzt9ntSDi7jkE36z3; rebind rides the hub venue (this coordinator's trigger/send_later arming is classifier-denied). send_later chain: none pending.
landing: pushed-unmerged claude/app-nav-reachability (PR #450) — adds tests/test_nav_manifest.py::test_every_top_level_get_route_is_reachable, a router-derived TestClient GET bucket over all 42 app/ top-level GET routes asserting non-5xx (gated /owner/* pinned to the documented {401,503} set, /owner/login to 200), the last of the four services to get the reachability guard (#416/#418/#421). Test-only, born-red, self-lands on the complete flip. Prior PRs #434–#449 are terminal (merged/closed); this is the only open PR.
deployed: main 8c5aeb0 (#449) · four Railway services (control-plane / botsite / dashboard / review, superbot-websites project); Railway redeploys on merge (merge=deploy), live re-verification is the follow-up. botsite /submit is DURABLE — DATABASE_URL live, Postgres-backed intake confirmed writing (ASK-0004 satisfied). The owner moderation queue GET /submit/queue.json + /testing owner reads still 503 until the botsite Discord-login vars land (ASK-0006). This slice is test-only — no deployable surface changed.
claims: control/claims/app-nav-reachability-2026-07-19.md is this branch's in-flight claim, removed in this PR's flip commit so it merges away clean (no drift-gate orphan). control/claims/ otherwise holds only README.md.
needs-owner: the ⚑ rows in docs/owner/OWNER-ACTIONS.md (mirror below).

## NEXT-2-TASKS baton
1. askverify probes for observable-but-unprobed asks (slice 3): add read-only probes for (a) Discord-OAuth-configured (`/owner/login` → 302 → discord.com) on botsite + dashboard (ASK-0006/0017) and (b) the `/submit` live signal (ASK-0004), following the existing six-probe contract in `app/askverify.py` (which at 412,422 still says "no read-only probe exists" for the now-observable 302-target signal). Async probe returning still-open / done-detected; unit test against a stubbed 302 target. Per docs/plans/next-cycle-2026-07-19.md slice 3.
2. committed signal-registry data file (slice 4): a committed registry (name → baker → raw-URL → consumers) so each drift/parity fan-out is a data edit, not a code hunt — generalising the join pattern tests/test_registry_drift.py already proves. Schema + consumer-reachability test over the JSON. Per docs/plans/next-cycle-2026-07-19.md slice 4.

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
