# websites · status

updated: 2026-07-13T23:47:41Z
phase: EAP FINAL NIGHT — ORDER 027 COMPLETE (coordinator session 12)
health: green (main green; all four services live-verified through the night wave)
last-shipped: night wave #307–#316 (see notes ledger)
blockers: none
orders: acked=001-027 done=001-019,023-027 (020/021 owner-gated; 022 standing — its item 5 cold-browser pass DONE tonight via #311; 027 COMPLETE — all 8 items + item-1 follow-on, ledger in notes)
routine: armed · failsafe cron trig_01GV8kBK92CSZWEWwNZo1rhk · 45 */2 * * * · bound to the live coordinator session · pacemaker send_later chain ~15 min
notes: final ORDER 027 ledger, day total, open PRs and asks in the body sections below.

## ORDER 027 final ledger
item 1 #304 (pre-order) + follow-on #316 step-provenance pin · item 2 #307/#310 heartbeat + #308 current-state truing · item 3 #311 cold-browser pass (3 fixes: favicons, hamburger glyph, footer gutter — live-verified; evidence in .sessions/2026-07-13-cold-browser-review.md) · item 4 #313 env-leads CLOSED (SITE_PASSWORD = unused drift, new ⚑ deletion ask; ANTHROPIC_API_KEY = not measured, walled) · item 5 #309 conftest token pin · item 6 #305 (pre-order) asked_at bake · item 7 #314 fast-lane outbox+heartbeat gate (per-path proven) · item 8 #315 build-direct open-work-sweep docs + drift-guard test.
Blocked per order (not scheduled): ORDER 020 PAT · ORDER 021 Discord decision · lifeboat disposal (owner-click) · photo-pack originals.

## day total 2026-07-13
29 merges #277–#316; suite 1206→1345+; all live-verified.

## open PRs
#281 coordinator session PR (flips at session end) + draft lifeboats #245 #249 #257 #278 #279 #280 #300 #312(if open).

## asks
docs/owner/OWNER-ACTIONS.md (9 ⚑ incl. new SITE_PASSWORD drift deletion; highest-leverage: botsite SITE_PASSWORD).
kit: v1.15.0
