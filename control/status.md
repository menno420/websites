# websites · status

updated: 2026-07-19T08:09:06Z
phase: heartbeat truing — ORDER 036 discharged; main advanced to 86d1eca (ASK-0008 ledger finalize, PR #439), past the prior heartbeat's a5fdad4 tip. This pass trues orders/landing/routine/baton against live GitHub — PR #434 (BAKE_PAT wiring), #438 (proof bake), #439 (ASK-0008 finalize) all merged; stale bot bake PRs #422 + #437 closed unmerged.
health: green — four service suites green (1979 passed) + python3 bootstrap.py check --strict green; tests/test_own_heartbeat.py 5/5.
last-shipped: #439 — finalize ASK-0008 ledger, BAKE_PAT landing path proven, merged 2026-07-19T08:01:15Z; main tip 86d1eca.
blockers: none
orders: acked=001-036 done=001-020,022-036 (021 open — owner-gated; 036 discharged — proof dispatch run 29678801173 actor menno420 success, bake PR #438 authored by the BAKE_PAT identity with a real pull_request quality check + auto-merge, stale bot PRs #422+#437 closed, ASK-0008 finalized via merged PR #439).
routine: failsafe cron `trig_01FYyvu2EytWF5NSEzLU2qLD` "Websites failsafe wake" `45 */2 * * *` ARMED · next 2026-07-19T08:45Z · last-fired 2026-07-19T06:45Z; bound to the predecessor session_012kFFGxzt9ntSDi7jkE36z3; rebind rides the hub venue (this coordinator's trigger/send_later arming is classifier-denied). send_later chain: none pending.
landing: pushed-unmerged claude/status-truing-036 — this control/** fast-lane truing PR (self-lands on green). Prior coordinator PRs terminal: #434/#438/#439 merged (07:50/07:53/08:01Z), #422/#437 closed unmerged (superseded bot bakes). No other open PRs.
deployed: main 86d1eca (#439) · four Railway services (control-plane / botsite / dashboard / review, superbot-websites project); Railway redeploys on merge, live re-verification is the follow-up (merge=deploy). botsite /submit stays in-memory until DATABASE_URL lands (ASK-0004).
claims: control/claims/status-truing-036.md is this branch's in-flight claim, removed in this PR so it merges away clean (no drift-gate orphan). control/claims/ otherwise holds only README.md.
needs-owner: the ⚑ rows in docs/owner/OWNER-ACTIONS.md (mirror below).

## NEXT-2-TASKS baton
1. Railway unblock pending the owner's choice (two-paste vs a settings allow-rule) → then verify the live botsite /submit write→read once DATABASE_URL lands (ASK-0004), set the Discord OAuth env vars (ASK-0002), and run the owner login test.
2. /testing SQLite→Postgres port (deferred from PR #425): bring the botsite submissions-store test coverage to Postgres parity once the DB exists.

## ⚑ OWNER-ACTION mirror (canonical: docs/owner/OWNER-ACTIONS.md)
- ASK-0002 — add a redirect URI to the existing SuperBot Discord app + copy client id/secret/owner-id/session-secret onto the control-plane Railway env (REUSE per the ASK-0001 decision). Unblocks the shipped owner login flow.
- ASK-0003 — provision the scoped control-API token + separate armed Railway service (the armed bot-control write path, stubbed).
- ASK-0004 — create the botsite submissions PostgreSQL + set DATABASE_URL on botsite. CODE SHIPPED (PR #425); goes live the moment the variable lands.
- ASK-0005 — set up PayPal Payouts + put its two credentials on the botsite service.
- ASK-0006 — decide the unwired SITE_PASSWORD on the botsite Railway service (wire or remove).
- ASK-0009 — delete the unused SITE_PASSWORD variable from the dashboard service.
- ASK-0012 — run the Gumroad publish pass for the ten publish-ready titles/products.
- ASK-0013 — hand off the full-res photo originals for the two wallpaper packs.
- ASK-0014 — pick the Ultramarine title: "The Widow's Blue" or keep Ultramarine.
- ASK-0015 — decide the §5 illustration gate for the two picture books + three Puddle Museum editions.
- ASK-0016 — arrange the native-speaker Dutch proofread for de-papieren-sinaasappel.

kit: v1.17.0
