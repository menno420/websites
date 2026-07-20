# websites · status

updated: 2026-07-20T08:04:12Z
phase: cycle 2026-07-19 executed: slices 1–6 all landed; queue drained to hygiene + owner-gated items
health: green — four service suites green (2132 passed) + python3 bootstrap.py check --strict passes its own assertions (only advisory warnings remain, all on untouched files / non-exit-affecting). tests/test_own_heartbeat.py 5/5.
last-shipped: #455 — botsite /directory .gba download probe now follows redirects (302 → CDN no longer a false-negative), merged 2026-07-20; main tip 7c3484b.
blockers: none
orders: acked=001-038 done=001-038 (021 closed w/ evidence #444; 037/038 done #442/#443; 036 done)
routine: failsafe cron `trig_01FYyvu2EytWF5NSEzLU2qLD` "Websites failsafe wake" `45 */2 * * *` ARMED · bound to the predecessor session_012kFFGxzt9ntSDi7jkE36z3; rebind rides the hub venue (this coordinator's trigger/send_later arming is classifier-denied). send_later chain: none pending.
landing: all-merged — this cycle's three slice PRs are terminal: #453 (committed signal-registry data file, slice 4), #454 (auto-discovering vendored-copy AST core guard, slice 5), #455 (/directory follow_redirects, slice 6) all merged to main. No open claude/* PRs from this cycle. #452 (kit-upgrade) is the owner's PR, still open — left as-is, it rides the hub venue.
deployed: main 7c3484b (all six slices landed) · four Railway services (control-plane / botsite / dashboard / review, superbot-websites project); Railway redeploys on merge (merge=deploy), live re-verification is the follow-up. botsite /submit is DURABLE — DATABASE_URL live, Postgres-backed intake confirmed writing (ASK-0004 satisfied). The owner moderation queue GET /submit/queue.json + /testing owner reads still 503 until the botsite Discord-login vars land (ASK-0006).
claims: control/claims/ holds only README.md — all three slice claims deleted in their flip commits (no drift-gate orphans).
needs-owner: the ⚑ rows in docs/owner/OWNER-ACTIONS.md (mirror below).

## NEXT-2-TASKS baton
1. Refresh docs/current-state.md header (lags main by ~26+ PRs — says #421, HEAD is #455) and fold in this cycle's three new guards/registry (signal-registry data file #453, vendored-copy AST core guard #454, /directory redirect-follow probe #455); update main sha, open-PR line, and the four-suite passed count (2132). Per docs/plans/next-cycle-2026-07-19.md Hygiene.
2. Orientation-headroom trim toward the boot-set word cliff (boot set 6909/7000 words, 91 headroom; current-state alone 6176) and clear the residual kit advisories: fix the model-line advisories on the three 2026-07-19 cards (-botsite-discord-oauth, -dashboard-discord-oauth, -submissions-store-shim) to the PL-004 `model · low|medium|high · class` form, then `python3 bootstrap.py seat-digest` regen. Per docs/plans/next-cycle-2026-07-19.md Hygiene.

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
