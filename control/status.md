# websites · status

updated: 2026-07-19T07:22:32Z
phase: heartbeat truing — main advanced to a5fdad4 (ORDER 034 durable /submit intake, PR #425); the prior heartbeat (2026-07-18T21:42:45Z) still described PR #426 in-flight and deployed baad569, both stale. This pass trues orders/landing/routine/deployed against live GitHub. Supersedes claude/heartbeat-truing-20260719 (9a1598c), whose one-commit fix failed tests/test_own_heartbeat.py by dropping "ARMED" from the routine line.
health: green — four service suites green (1979 passed) + python3 bootstrap.py check --strict green; tests/test_own_heartbeat.py 5/5.
last-shipped: #425 — botsite durable /submit intake via DATABASE_URL (ORDER 034), merged 2026-07-18T21:52:35Z; main tip a5fdad4.
blockers: none
orders: acked=001-036 done=001-020,022-035 (021 + 036 open — 021 owner-gated; 034 done code-half via PR #425 with ASK-0004 narrowed to the one DATABASE_URL paste; 035 done via PR #426; 036 in-flight via PR #434 bake-path BAKE_PAT wiring, owner-gated on the merge click + ASK-0008 BAKE_PAT secret).
routine: failsafe cron `trig_01FYyvu2EytWF5NSEzLU2qLD` "Websites failsafe wake" `45 */2 * * *` ARMED · next 2026-07-19T08:45Z · last-fired 2026-07-19T06:45Z (that fire spawned the degraded session that pushed the now-superseded claude/heartbeat-truing-20260719); bound to the predecessor session_012kFFGxzt9ntSDi7jkE36z3; rebind rides the hub venue (this coordinator's trigger/send_later arming is classifier-denied). send_later chain: none pending.
landing: pushed-unmerged claude/status-truing-20260719 — this heartbeat-truing PR (control/** fast lane, self-lands on green). Prior coordinator PRs terminal: #414/#425/#426/#435 merged, #413/#422 closed. #434 (BAKE_PAT workflow wiring · hub venue) OPEN but conflicting with current main (mergeable_state dirty) and held by the do-not-automerge label — needs a rebase onto a5fdad4 + the owner merge click.
deployed: main a5fdad4 (#425) · four Railway services (control-plane / botsite / dashboard / review, superbot-websites project); Railway redeploys on merge, live re-verification is the follow-up (merge=deploy). botsite /submit stays in-memory until DATABASE_URL lands (ASK-0004).
claims: control/claims/status-truing-20260719.md is this branch's in-flight claim, deleted in the flip commit so it merges away clean (no drift-gate orphan). control/claims/ otherwise holds only README.md.
needs-owner: the ⚑ rows in docs/owner/OWNER-ACTIONS.md (mirror below).

## NEXT-2-TASKS baton
1. Prove the BAKE_PAT bake path once PR #434 lands (owner merge click + ASK-0008 BAKE_PAT Actions secret) — confirm the scheduled review-bake commits again — then verify the live botsite write→read on /submit after DATABASE_URL lands (ASK-0004) and the owner Discord login once the OAuth env is set (ASK-0002).
2. /testing SQLite→Postgres port (deferred from PR #425): bring the botsite submissions-store test coverage to Postgres parity.

## ⚑ OWNER-ACTION mirror (canonical: docs/owner/OWNER-ACTIONS.md)
- ASK-0002 — add a redirect URI to the existing SuperBot Discord app + copy client id/secret/owner-id/session-secret onto the control-plane Railway env (REUSE per the ASK-0001 decision). Unblocks the shipped owner login flow.
- ASK-0003 — provision the scoped control-API token + separate armed Railway service (the armed bot-control write path, stubbed).
- ASK-0004 — create the botsite submissions PostgreSQL + set DATABASE_URL on botsite. CODE SHIPPED (PR #425); goes live the moment the variable lands.
- ASK-0005 — set up PayPal Payouts + put its two credentials on the botsite service.
- ASK-0006 — decide the unwired SITE_PASSWORD on the botsite Railway service (wire or remove).
- ASK-0008 — extend the O-020 PAT with PR write + store as BAKE_PAT Actions secret (unblocks PR #434's bake path).
- ASK-0009 — delete the unused SITE_PASSWORD variable from the dashboard service.
- ASK-0012 — run the Gumroad publish pass for the ten publish-ready titles/products.
- ASK-0013 — hand off the full-res photo originals for the two wallpaper packs.
- ASK-0014 — pick the Ultramarine title: "The Widow's Blue" or keep Ultramarine.
- ASK-0015 — decide the §5 illustration gate for the two picture books + three Puddle Museum editions.
- ASK-0016 — arrange the native-speaker Dutch proofread for de-papieren-sinaasappel.

kit: v1.17.0
