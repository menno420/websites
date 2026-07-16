# Arcade + Dashboard — overnight proposal menu (2026-07-16)

> **Status:** `plan` — veto-ready proposal menu. Docs-only. Generated on the owner's overnight order (event 55f13541).

Grounded on HEAD `da63857` (#357). 24 distinct proposals across two services, small fixes → ambitious features. **Owner's veto is the filter** — this is deliberately broad, not pre-narrowed.

Legend — Effort: **S** small / **M** medium / **L** large. Risk & reversibility: ✅ contained + reversible / ↩️ reversible but touches shape / ⚠ needs a decision or new data before build.

---

## A. Botsite / Fleet Arcade (`botsite/`)

### A1 · Build the `/games` launch-readiness summary (#371) — **M** ✅
`/games` (app.py:207) still just lists in-chat game features from `site.json` with no readiness UI, while `/arcade` has the full `availability_summary` strip (arcade.py:119, arcade.html:17-60). Port that pattern: a live/blocked/owner-clicks summary strip atop `/games`. **Unblocks:** the last named open arcade issue; parity between the two game surfaces.

### A2 · Cross-link `/games` ↔ `/arcade` — **S** ✅
Neither template points at the other; a visitor on `/games` never discovers `/arcade` readiness and vice-versa. Add a one-line pointer strip in each. **Unblocks:** discoverability; the two overlapping surfaces stop being dead ends.

### A3 · Arcade "owner action queue" section — **S** ✅
`availability_summary` already computes `owner_clicks` deduped by `ask_id`; surface the actual list of pending `owner_action` strings (with `ask_id` ledger refs) as a dedicated panel on `/arcade`, not just a count. **Unblocks:** owner sees exactly which clicks unblock which games in one place.

### A4 · Arcade JSON schema CI guard — **S** ✅
`arcade.py:60` validates required fields at load (fail-soft); add a test/CI assertion that every `arcade.json` entry passes full schema + enum + blocker-schema validation so a malformed new game fails the build, not silently drops. **Unblocks:** safe game onboarding by non-authors.

### A5 · Shareable arcade filter presets — **S** ✅
`listfilter.py` already powers filter/sort/search; expose availability/maturity as URL query presets (`/arcade?availability=live`) with shareable canonical links + "N results" honesty line. **Unblocks:** deep-linking to "playable now" etc.

### A6 · Arcade maturity lanes (roadmap view) — **S** ✅
Render prototype/beta/playable as distinct visual lanes on `/arcade` (currently one flat grid). Reads existing `maturity` enum, no data change. **Unblocks:** a roadmap read of the fleet's games at a glance.

### A7 · Per-game OpenGraph / share cards — **S** ✅
`arcade_detail.html` has no per-game meta tags; add title/description/OG tags so a shared game link previews properly. **Unblocks:** social/chat sharing of individual games.

### A8 · Arcade games in `palette.json` — **S** ✅
The command-palette index (app.py:548) omits arcade games; add each game as a searchable palette entry (name + tagline + detail_url). **Unblocks:** keyboard-navigable game discovery.

### A9 · Reusable blocker/availability chip partial — **S** ✅
The blocker panel markup lives inline in `arcade.html`; extract a Jinja partial (`_blocker_chip.html`) reused by catalog/products/puddle-museum (which already share `blockers.py`). **Unblocks:** consistent blocker UX across all registries; A3 and dashboard surfaces reuse it.

### A10 · Arcade link-drift probe surfacing — **M** ↩️
`arcade_probe.py` probes outbound game links; surface its freshness/last-checked result on `/arcade/{slug}` (e.g. "link verified" vs "unchecked"). **Unblocks:** trust signal on live/download links; catches rotted URLs before visitors do.

### A11 · Game onboarding flow — **M** ↩️
A schema-guided `/arcade/submit` (or docs walkthrough) for proposing a new game — honest stub like `/submit` (app.py:534), emitting a ready-to-paste `arcade.json` block. **Unblocks:** game intake without hand-editing JSON; feeds A4's guard.

### A12 · `/games` machine-readable readiness JSON — **M** ↩️
A `/games/readiness.json` (or extend `palette.json`) emitting the A1 summary as JSON, so the dashboard can consume arcade readiness over committed JSON (D-side, see B-group). **Unblocks:** the cross-service arcade-status surface (C1) without a live import.

### A13 · Arcade activity feed — **M** ↩️
An atom/RSS feed of newly-added / newly-live games (ties to the existing `activity-atom-feed` idea). Derives from `arcade.json` + git. **Unblocks:** subscribers get notified when a blocked game goes live.

### A14 · "Unblock narrative" per blocked game — **M** ⚠
On `/arcade/{slug}`, render a short narrative pulling the ask ledger state via `ask_id` (the askverify join, `app/askverify.py`) — "blocked on ASK-0010: <owner_action>; verified?/pending". ⚠ depends on askverify data being readable to botsite over committed JSON. **Unblocks:** end-to-end blocker storytelling from public page to owner console.

---

## B. Dashboard (`dashboard/`)

### B1 · Arcade live/blocked counts on `/status` — **S** ↩️
`/status` (app.py:288) shows bot count cards; add arcade fleet readiness counts sourced from botsite's committed `arcade.json` over raw.githubusercontent.com (same mechanism as `console.json`). **Unblocks:** one dashboard glance covers games too, not just bots.

### B2 · Dashboard schema-drift banner test coverage — **S** ✅
The `dashboard_schema_issue` / `console_contract_issue` honest banners (data_source.py) have thin test coverage; add tests asserting they fire on contract drift and stay silent when clean. **Unblocks:** confidence the honesty banners actually trip.

### B3 · Command-stats trend sparkline — **S** ✅
`/` and `/commands` show `command_stats` as flat numbers; add a small sparkline/trend visual. Client-side, no data change. **Unblocks:** at-a-glance sense of command usage movement.

### B4 · Dashboard `palette.json` parity — **S** ✅
Ensure the dashboard palette (app.py:320) covers all routes/admin surfaces the way botsite's does; audit + fill gaps. **Unblocks:** consistent keyboard nav across services.

### B5 · `/ideas` reads `docs/ideas/backlog.md` states — **M** ↩️
`/ideas` (app.py:234) renders ideas data; wire it to reflect the real backlog lifecycle states (captured/planned/built/retired) from committed data. **Unblocks:** the dashboard idea board matches the repo's actual idea ledger.

### B6 · `env.html` unused/missing-var flags — **M** ↩️
`/env` (app.py:227) maps env usage; cross-check against a committed manifest and flag vars that are referenced-but-unset or set-but-unused. **Unblocks:** config-drift visibility before a deploy surprises someone.

### B7 · Admin audit export/snapshot — **M** ↩️
The dry-run admin audit log (app.py:450) is in-memory and clears on restart; add a JSON export/download (like `/testing/owner/export.json`) so a dry-run session's audit trail survives. **Unblocks:** reviewable record of what the panel would have done.

### B8 · Dashboard "owner one-glance" adds arcade owner-clicks — **M** ↩️
`/console` (app.py:256) renders the owner one-glance from `console.json`; fold in pending arcade owner-clicks (from `arcade.json` committed JSON) so the single glance covers game blockers too. **Unblocks:** unifies bot + game owner actions in one console view.

### B9 · Functions/commands catalogue search — **S** ✅
`/functions` and `/commands` are category-grouped lists with no in-page filter; vendor the botsite `listfilter` pattern for client-side search. **Unblocks:** finding a command without scrolling.

---

## C. Cross-service (committed JSON only — never a live import)

### C1 · Dashboard arcade-readiness surface — **M/L** ↩️
A dedicated dashboard view (or `/console` card) showing the full Fleet Arcade readiness — live/blocked/owner-clicks per game — consuming botsite's committed `arcade.json` (or A12's readiness JSON) over raw.githubusercontent.com. Honors the read-only forward-only doctrine. **Unblocks:** dashboard becomes the single oversight surface for bots AND games.

### C2 · Fleet-wide owner-action inbox — **L** ⚠
Aggregate every pending `owner_action` across arcade + catalog + products + puddle-museum (all now share `blockers.py`'s `{owner_action, unblocks, ask_id}` schema) into one dashboard "owner action inbox," deduped by `ask_id`, joined to askverify chip state. ⚠ largest scope; needs a decision on where the canonical aggregate lives. **Unblocks:** one place for the owner to see and clear every fleet blocker.

---

## Buildable-tonight candidates (small, contained, reversible)
If any single small win is picked for immediate build: **A2** (cross-link), **A6** (maturity lanes), **A8** (palette entries), **B3** (sparkline), **B9** (catalogue search) — each is botsite/dashboard-local, template-only or additive, and reversible by revert.

## Not tonight (ambition — plan only)
A11 (onboarding flow), A13 (activity feed), A14 (unblock narrative), B8 (console owner-clicks), C1 (arcade-readiness surface), C2 (fleet owner-action inbox) — these need a build slice and, for ⚠ items, an owner decision first.
