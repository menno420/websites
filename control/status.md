# websites · status

updated: 2026-07-21T19:40:00Z
phase: cycle 2026-07-20 product-frontier COMPLETE — all six slices S1–S6 landed + live. S1 edition auto-drafter (#463), S2 arcade catalog +Gloamline (#464), S3 cross-service fleet nav strip (#466), S4 /owner inline actions panel (#467), S5 submitter status lookup (#469), S6 arcade richer detail (#470). The docs/plans/next-cycle-2026-07-20.md cycle is fully drained; owner-gated items (Discord-login vars) unchanged.
health: green — four service suites green (2176 passed) + python3 bootstrap.py check --strict passes its own assertions (only advisory warnings remain, all on untouched files / non-exit-affecting). tests/test_own_heartbeat.py 5/5.
last-shipped: #470 — botsite: richer arcade game detail pages (optional screenshots/controls/changelog, S6), merged 2026-07-21; main tip 546484a.
blockers: none
orders: acked=001-038 done=001-038 (021 closed w/ evidence #444; 037/038 done #442/#443; 036 done)
routine: failsafe cron `trig_01FYyvu2EytWF5NSEzLU2qLD` "Websites failsafe wake" `45 */2 * * *` ARMED · bound to the predecessor session_012kFFGxzt9ntSDi7jkE36z3; rebind rides the hub venue (this coordinator's trigger/send_later arming is classifier-denied). send_later chain: none pending (walled).
landing: all-merged — the 2026-07-20 cycle's slices S1–S6 (#462/#463/#464/#466/#467/#469/#470) are all terminal and merged to main; 0 open claude/* PRs; no drift-gate orphans.
deployed: main 546484a · four Railway services (control-plane / botsite / dashboard / review, superbot-websites project); Railway redeploys on merge (merge=deploy). S6 live re-verified 2026-07-21 — /arcade/lumen-drift and /arcade/games-web render Controls + Changelog sections; /arcade/mineverse renders Changelog and correctly omits Controls (fail-soft). botsite /submit is DURABLE — DATABASE_URL live, Postgres-backed intake confirmed writing (ASK-0004 satisfied); S5 GET /submit/status/{ref} live. The owner moderation queue GET /submit/queue.json + /testing owner reads still 503 until the botsite Discord-login vars land (ASK-0006/0017).
claims: control/claims/ holds only README.md — no drift-gate orphans.
needs-owner: the ⚑ rows in docs/owner/OWNER-ACTIONS.md (mirror below).

## NEXT-2-TASKS baton
Cycle drained — the groomed 2026-07-20 product-frontier cycle (S1–S6) is fully landed and live as of 2026-07-21. No seat-buildable ungated slices remain queued from that plan. HONESTY GUARD: do not invent backlog. Next groomed queue: docs/NEXT-TASKS.md. Standing routed-out follow-ons unchanged — the S1 review-bake cron wiring (auto-draft+land editions on the BAKE_PAT path) stays a HUB-VENUE follow-on (.github/workflows/**); owner-gated items are the ⚑ rows below.

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

kit: v1.20.1
