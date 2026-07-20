# websites · status

updated: 2026-07-20T05:15:52Z
phase: slice 3 landed — askverify Discord/submit probes; queue top = signal-registry data file (slice 4)
health: green — four service suites green (2092 passed) + python3 bootstrap.py check --strict passes its own assertions; the only red is the by-design born-red HOLD on this session's in-progress card, released at the flip. tests/test_own_heartbeat.py 5/5.
last-shipped: #450 — app/ NAV reachability GET guard (router-derived, all 42 top-level GET routes non-5xx), merged 2026-07-20; main tip 98b9eb1.
blockers: none
orders: acked=001-038 done=001-038 (021 closed w/ evidence #444; 037/038 done #442/#443; 036 done)
routine: failsafe cron `trig_01FYyvu2EytWF5NSEzLU2qLD` "Websites failsafe wake" `45 */2 * * *` ARMED · bound to the predecessor session_012kFFGxzt9ntSDi7jkE36z3; rebind rides the hub venue (this coordinator's trigger/send_later arming is classifier-denied). send_later chain: none pending.
landing: pushed-unmerged claude/askverify-discord-submit-probes (PR #451) — three read-only askverify probes that auto-flip owner-action chips: dashboard `/admin/login` 302 (ASK-0017), botsite `/submit` live-badge (ASK-0004), botsite `/owner/login` 302 prepended to the byte-preserved SITE_PASSWORD fallback (ASK-0006). Registry structure untouched (no new entries / signatures / ask-id rebinds); +8 unit tests. Behaviour-additive, born-red, self-lands on the complete flip. Prior PRs #434–#450 are terminal (merged/closed); this is the only open PR.
deployed: main 98b9eb1 (#450) · four Railway services (control-plane / botsite / dashboard / review, superbot-websites project); Railway redeploys on merge (merge=deploy), live re-verification is the follow-up. botsite /submit is DURABLE — DATABASE_URL live, Postgres-backed intake confirmed writing (ASK-0004 satisfied). The owner moderation queue GET /submit/queue.json + /testing owner reads still 503 until the botsite Discord-login vars land (ASK-0006). This slice is test-only + a domain-probe change — no route/template/deployable surface changed.
claims: control/claims/askverify-discord-submit-probes-2026-07-19.md is this branch's in-flight claim, removed in this PR's flip commit so it merges away clean (no drift-gate orphan). control/claims/ otherwise holds only README.md.
needs-owner: the ⚑ rows in docs/owner/OWNER-ACTIONS.md (mirror below).

## NEXT-2-TASKS baton
1. committed signal-registry data file (slice 4): a committed registry (name → baker → raw-URL → consumers) so each drift/parity fan-out is a data edit, not a code hunt — generalising the join pattern tests/test_registry_drift.py already proves. Schema + consumer-reachability test over the JSON. Per docs/plans/next-cycle-2026-07-19.md slice 4.
2. auto-discovering vendored-copy AST core guard (slice 5): a guard that discovers vendored copies of a core module by AST rather than a hand-maintained path list, so a new vendored copy can't silently drift from its source. Per docs/plans/next-cycle-2026-07-19.md slice 5.

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
