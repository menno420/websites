# websites · status

updated: 2026-07-13T22:46:00Z
phase: EAP FINAL NIGHT — ORDER 027 in progress (coordinator session 12)
health: green (this commit restores the parseable heartbeat field grammar dropped by #307 — tests/test_own_heartbeat.py + full four-suite run green on this branch; main red between f47f7ce and this fix's merge)
last-shipped: #305 = 66e140c (full asked_at timestamp — ORDER 027 item 6) · #304 = 9cd2af6 (per-step question digest), both MERGED+LIVE.
blockers: none
orders: acked=001-027 done=001-019,023-026 (020/021 owner-gated; 022 standing — its item 5 cold-browser pass runs tonight as ORDER 027 item 3). ORDER 027 (P1, fm ORDER 045 relay) ACKED 2026-07-13 — night ledger below.
routine: armed · failsafe cron trig_01GV8kBK92CSZWEWwNZo1rhk · 45 */2 * * * · bound live · pacemaker send_later chain ~15 min, one pending.
notes: ORDER 027 night ledger, day tally, open PRs and asks in the body sections below.

## ORDER 027 night ledger (top-down)
1. #304 shepherd + follow-on — #304 MERGED+LIVE pre-order (9cd2af6); follow-on (step-provenance pin, backlog) queued as a night slice. STATUS: half-done, follow-on in queue.
2. truing pass — heartbeat: THIS commit (fast-lane to main); current-state truing dispatched as its own slice. STATUS: in progress.
3. cold-browser review-site pass (ORDER 022 item 5, deadline 07-14) — dispatched. STATUS: in progress.
4. #275 env-lead read-path check — largely landed pre-order by #282 (dashboard does NOT read SITE_PASSWORD, set-but-unused drift, docs/dashboard.md:127; ANTHROPIC_API_KEY recorded "not measured — walled", docs/botsite.md env table). Night slice will verify + close with citations. STATUS: queued.
5. suite-level token pin in tests/conftest.py — queued.
6. full asked_at timestamp — DONE pre-order: #305 (66e140c) MERGED+LIVE. STATUS: done.
7. outbox grammar gate on the control fast lane — queued.
8. idea-engine build-direct slice (review-queue row auto-check OR open-PR awareness at wake) — queued.
Blocked (per order, not scheduled): ORDER 020 PAT · ORDER 021 Discord decision · lifeboat disposal (owner-click: #245 #249 #257 #278 #279 #280 #300) · photo-pack originals.

## day tally (pre-order sitting, all merged+live-verified)
23 merges #277→#305; suite 1206→1336+. FENCE holds through 07-14: no live-URL moves, no Railway consolidation.

## open PRs
#281 coordinator session PR (born-red card, flips at session end). Draft lifeboats owner-close: #245 #249 #257 #278 #279 #280 #300.

## asks
8 open ⚑ in docs/owner/OWNER-ACTIONS.md — highest-leverage: botsite SITE_PASSWORD (unlocks the whole /testing/owner surface built today).
kit: v1.15.0
