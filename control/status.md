# websites · status

updated: 2026-07-15T13:06:44Z
phase: ACTIVE — EAP extended through 2026-07-21 per ORDER 031 (control/inbox.md @ 3cac461), acknowledged 2026-07-15 (first rebooted wake); session-ender heartbeat.
health: green — main 873cb4a · suite 1458 passed · bootstrap check --strict pass · quality green: latest run 29417011094 success.
last-shipped: five PRs landed this wake — #344 (reboot truing / ORDER 031 ack) · #346 (walls ledger + card grammar + heartbeat) · #347 (seat digest + orientation headroom 6567/7000) · #348 (launch preflight verdicts — owner asks machine-verified on the gated console, live-verified /version 4b7c20c) · #349 (arcade /arcade/{slug} detail pages with launch-blocker panels, live-verified /version 873cb4a).
blockers: none.
orders: acked=001-031 done=001-019,023-031 (020/021 owner-gated; 022 standing).
routine: armed — failsafe cron trig_01VRT9F6jYNXym3nn18vVQQK ("Websites failsafe wake" · 45 */2 * * * · Q-0265 prompt), bound to the coordinator session, verified via list_triggers 2026-07-15T03:48Z; pacemaker = send_later ~15-min chain, one pending at a time.
needs-owner: 9 open ⚑ rows in docs/owner/OWNER-ACTIONS.md (re-verified 2026-07-15) plus the three parked PRs in notes below.
notes: PARKED/NEEDS-OWNER — PR #342 (draft rescue lifeboat, discardable) · PR #343 (bake fleet-data refresh; owner: approve workflow run 29397321395 or hand-merge; durable fix = BAKE_PAT secret) · PR #345 (quality-main-sweep; owner: remove do-not-automerge label + merge). NEXT-2-TASKS BATON — (1) owner clicks land #345/#343 (console verdict chips will confirm BAKE_PAT/SITE_PASSWORD automatically); (2) next mission increments — botsite release-drift banner (doctrine decision needed: new botsite outbound surface) + console-POST preflight screens.
kit: v1.17.0
