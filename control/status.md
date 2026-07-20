# websites · status

updated: 2026-07-20T20:45:29Z
phase: FAILSAFE WAKE — root cause found on the PR #452 stall. A cross-session nudge pointed at inbox ORDER 039 (verified real in this session's own clone), itemizing 5 pre-existing wall mentions the new v1.20.1 substrate-gate flags as unattached. Fixed all 5 with minimal inline dated citations (no history deleted; read bootstrap.py's own clause-attachment grammar to place each date correctly) and confirmed locally: `bootstrap.py check --strict` now passes with zero false-wall findings on that branch. Pushed the fix directly onto PR #452's own branch (claude/kit-upgrade-v1.20.1, commit c67057f) ~18:50Z. It is now 2h later and PR #452 is STILL open — GitHub's checks UI for that commit reads "There are no checks for this commit": CI never fired on the push at all.
health: the FIX itself is verified green locally (bootstrap.py check --strict: all checks passed, the specific 5 findings gone). Main-tree health not independently re-run this wake (unchanged since prior full run at a5fdad4; every commit since has landed via the normal gated path).
last-shipped: #461 — control: ORDER 039 fix red substrate-gate on kit v1.20.1 upgrade PR #452, merged 2026-07-20T13:26:02Z; main tip 6971249 (unchanged — #452 has not merged).
blockers: PR #452's checks never ran on the newest commit (c67057f, pushed via this failsafe session's git proxy ~18:50Z) — "There are no checks for this commit" per GitHub's own checks UI. This matches a PRECEDENTED pattern already solved once in this repo (control/outbox.md, 2026-07-13 STALLS entry #3: a GITHUB_TOKEN/bot-authenticated push doesn't fire the `pull_request synchronize` event under GitHub's anti-recursion rule, so `quality`/`auto-merge-enabler` never trigger; the documented fix was closing and reopening the PR, since reopen is a user-context event). This failsafe session cannot close/reopen a PR (own GitHub API access separately walled), so this needs the owner: close PR #452, then reopen it, on github.com/menno420/websites/pull/452 — that alone should fire the checks on the already-fixed branch and let the existing armed auto-merge land it.
orders: acked=001-039 done=001-039 (021 closed w/ evidence #444; 036-039 done)
routine: failsafe cron `trig_01FYyvu2EytWF5NSEzLU2qLD` "Websites failsafe wake" `45 */2 * * *` — this wake fired on it; four prior wakes (14:45/16:45/18:45/20:45) tracked PR #452, escalating from "watch" to "root cause found + fix pushed" to "fix pushed but never checked — needs a close/reopen". send_later pacemaker: not re-armed by this failsafe session.
landing: pushed-unmerged claude/heartbeat-truing-20260720 (this heartbeat) + claude/kit-upgrade-v1.20.1 (PR #452's own branch, fix commit c67057f already on it — do NOT re-push more fix commits there, the content is correct, it just needs a checks re-trigger). PR #452 remains the one open PR fleet-wide at write.
deployed: main 6971249 (#461) · kit v1.17.0 still deployed (PR #452's 1.20.1 not yet live); four Railway services not re-verified this wake, treat as last-known-good.
claims: control/claims/ holds only README.md — no drift-gate orphans.
needs-owner: NEW, concrete, precedented — close PR #452 then reopen it (github.com/menno420/websites/pull/452) to force GitHub to fire checks on its already-fixed latest commit; the fix content itself is done and locally verified green, it just never got CI'd. Plus the ⚑ rows in docs/owner/OWNER-ACTIONS.md (mirror below).

## NEXT-2-TASKS baton
1. Owner sitting on ASK-0006 + ASK-0017: set the four Discord-login vars + one redirect URI on BOTH the botsite and dashboard Railway services. That unblocks owner sign-ins (/owner/login 302, /admin/login 302) → the one /testing owner write. On completion a session runs the E2E gate verification and the new askverify console chips flip to done-detected.
2. Product frontier behind the owner gate: arcade catalog growth · review editions cadence · tester payouts (PayPal Payouts, ASK-0005). Honest line: the seat-buildable hardening queue is executed through #459 and the strict gate is fully clean — no seat-buildable hygiene backlog remains; the frontier is product + owner-gated items.

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
