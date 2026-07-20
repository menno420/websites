# websites · status

updated: 2026-07-20T18:45:58Z
phase: FAILSAFE WAKE — heartbeat truing. Main advanced to 6971249 (#461, "ORDER 039 — fix red substrate-gate on kit v1.20.1 upgrade PR #452") since the last heartbeat, then went quiet ~5.5h. Flagging one anomaly (see blockers): PR #452 (kit upgrade, owner-opened, auto-merge armed since 06:07) is still open despite its stated blocker (#461) landing at 13:26 — over 5h with an armed, allegedly-unblocked PR not merging is a different shape than this lane's usual "waiting on an owner click" pauses. No code changes made this wake.
health: green as of the last full run this failsafe session did (a5fdad4, several cycles back) plus every commit since landing via the normal quality-gated path; not independently re-run this wake. kit at main HEAD is still v1.17.0 (PR #452's 1.20.1 bump has not merged).
last-shipped: #461 — control: ORDER 039 fix red substrate-gate on kit v1.20.1 upgrade PR #452, merged 2026-07-20T13:26:02Z; main tip 6971249.
blockers: PR #452 (chore(kit): upgrade substrate-kit 1.17.0 → 1.20.1, opened by the owner) shows auto-merge armed but is still open ~12.5h after arming and ~5.5h after its cited blocking gate was reportedly fixed in #461. This failsafe session cannot inspect its CI check-run states in detail (this session's own GitHub API access is separately walled — see prior heartbeats — and GitHub's PR checks UI needs JS the read-only web fetch can't execute), so cannot tell from here whether it's still red on something new, waiting on a required review, or just needs a manual merge click. Flagging for the owner rather than guessing.
orders: acked=001-039 done=001-039 (021 closed w/ evidence #444; 036-039 done)
routine: failsafe cron `trig_01FYyvu2EytWF5NSEzLU2qLD` "Websites failsafe wake" `45 */2 * * *` — this wake fired on it, three prior wakes (14:45/16:45/18:45) tracked the same PR #452 pause. send_later pacemaker: not re-armed by this failsafe session (consistent with treating an idle-not-dead coordinator as its own lane).
landing: pushed-unmerged claude/heartbeat-truing-20260720 — this heartbeat-truing commit only (control-only diff). PR #452 remains the one open PR fleet-wide at write.
deployed: main 6971249 (#461) · kit v1.17.0 still deployed (PR #452's 1.20.1 not yet live); four Railway services not re-verified this wake, treat as last-known-good.
claims: control/claims/ holds only README.md — no drift-gate orphans.
needs-owner: NEW — check PR #452 directly on GitHub (github.com/menno420/websites/pull/452): it's been armed-for-automerge since 06:07 today and its cited blocker (#461) landed at 13:26, but it's still open at 18:45 — likely just needs a look/manual merge click, but this session can't confirm why it hasn't gone through on its own. Plus the ⚑ rows in docs/owner/OWNER-ACTIONS.md (mirror below).

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
