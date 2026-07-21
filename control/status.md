# websites · status

updated: 2026-07-21T08:14:23Z
phase: cycle 2026-07-20 product-frontier slices S1–S4 landed + live (#462 plan/baton, #463 S1 edition auto-drafter + edition-002, #464 S2 arcade catalog +Gloamline, #466 S3 cross-service fleet nav strip, #467 S4 /owner inline actions panel). Remaining seat-buildable work is the thin ungated product frontier (S5 submitter status lookup top, S6 arcade richer detail — docs/plans/next-cycle-2026-07-20.md); owner-gated items (Discord-login vars) unchanged.
health: green — four service suites green (2153 passed) + python3 bootstrap.py check --strict passes its own assertions (only advisory warnings remain, all on untouched files / non-exit-affecting). tests/test_own_heartbeat.py 5/5.
last-shipped: #467 — app: inline owner actions-now panel on /owner home (S4), merged 2026-07-21; main tip 16e0d50.
blockers: none
orders: acked=001-038 done=001-038 (021 closed w/ evidence #444; 037/038 done #442/#443; 036 done)
routine: failsafe cron `trig_01FYyvu2EytWF5NSEzLU2qLD` "Websites failsafe wake" `45 */2 * * *` ARMED · bound to the predecessor session_012kFFGxzt9ntSDi7jkE36z3; rebind rides the hub venue (this coordinator's trigger/send_later arming is classifier-denied). send_later chain: none pending (walled).
landing: all-merged — today's product-frontier slices #462/#463/#464/#466/#467 all terminal, 0 open claude/* PRs. The 2026-07-20 cycle's S1–S4 slices are fully merged to main; no drift-gate orphans.
deployed: main 16e0d50 · four Railway services (control-plane / botsite / dashboard / review, superbot-websites project); Railway redeploys on merge (merge=deploy), live re-verification is the follow-up. botsite /submit is DURABLE — DATABASE_URL live, Postgres-backed intake confirmed writing (ASK-0004 satisfied). The owner moderation queue GET /submit/queue.json + /testing owner reads still 503 until the botsite Discord-login vars land (ASK-0006/0017).
claims: control/claims/ holds only README.md — no drift-gate orphans.
needs-owner: the ⚑ rows in docs/owner/OWNER-ACTIONS.md (mirror below).

## NEXT-2-TASKS baton
1. S5 submitter status lookup (per docs/plans/next-cycle-2026-07-20.md): the top remaining ungated seat-buildable slice. Issue an opaque ref token on /submit, show it on the thank-you screen, add read-only GET /submit/status/{ref} → {status} with an honest not-found fallback; dual SQLite⇄Postgres schema add via _db.py. value med · size M · gate none.
2. S6 arcade richer detail: optional screenshots/controls/changelog in arcade_detail.html behind fail-soft guards (mirrors the optional-blocker pattern). gate partial — some screenshot originals may be owner-held, scope to capturable. HONESTY GUARD: beyond S5/S6 the ungated product frontier is thin — do not invent backlog. The S1 review-bake cron wiring (auto-draft+land editions on the BAKE_PAT path) stays a routed-out HUB-VENUE follow-on (.github/workflows/**).

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
