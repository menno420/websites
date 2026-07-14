# websites · status

updated: 2026-07-14T03:21:07Z
phase: EAP FINAL NIGHT — ORDER 027 complete + standing-ladder wave (coordinator session 12)
health: green (main green; live-verified through #323)
last-shipped: standing-ladder wave #318–#323 merged; #324 parked green by design
blockers: none
orders: acked=001-027 done=001-019,023-027 (020/021 owner-gated; 022 standing)
routine: armed · failsafe cron trig_01GV8kBK92CSZWEWwNZo1rhk · 45 */2 * * * · live coordinator session · pacemaker send_later chain ~15 min
notes: ORDER 027 final ledger, standing-ladder wave, sitting total, open PRs and asks in the body sections below.

## ORDER 027 final ledger
item 1 #304 (pre-order) + follow-on #316 step-provenance pin · item 2 #307/#310 heartbeat + #308 current-state truing · item 3 #311 cold-browser pass (3 fixes: favicons, hamburger glyph, footer gutter — live-verified; evidence in .sessions/2026-07-13-cold-browser-review.md) · item 4 #313 env-leads CLOSED (SITE_PASSWORD = unused drift, new ⚑ deletion ask; ANTHROPIC_API_KEY = not measured, walled) · item 5 #309 conftest token pin · item 6 #305 (pre-order) asked_at bake · item 7 #314 fast-lane outbox+heartbeat gate (per-path proven) · item 8 #315 build-direct open-work-sweep docs + drift-guard test.
Blocked per order (not scheduled): ORDER 020 PAT · ORDER 021 Discord decision · lifeboat disposal (owner-click) · photo-pack originals.

## standing-ladder wave
#318 claims-drift gate (squash-aware) + stale ORDER-026 claim swept + control-plane favicon · #319 project.index.json populated (4 real areas) · #320 testing-DB import valve (owner-auth, CSRF same-origin guard, replace-into-empty) · #321 scheduled Playwright smoke-crawl (47 2-23/6; WATCH: 02:47Z first slot did not fire — zero runs at 03:15Z check; GitHub cron lag on new workflows is common; re-verify at/after 08:47Z before calling it wedged) · #322 md relative-link rewrite + /favicon.ico on all four services (live-verified) · #323 import-valve referential pass (5 FK edges) · #324 automerge race reconciliation — PARKED GREEN BY DESIGN (its new rail labels workflow-touching PRs do-not-automerge; owner-click merge; landing path owner-click).

## sitting total
38 landed/parked #277–#324; suite 1206→1389; blocked-per-order items unchanged.

## open PRs
#281 (coordinator, flips at ender) + #324 (parked green, owner-click) + draft lifeboats #245 #249 #257 #278 #279 #280 #300.

## asks
docs/owner/OWNER-ACTIONS.md (9 ⚑; highest-leverage botsite SITE_PASSWORD).
kit: v1.15.0
