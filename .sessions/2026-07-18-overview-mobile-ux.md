# 2026-07-18 — Overview count badges → drill-downs + mobile legibility

> **Status:** `complete` — branch `claude/overview-mobile-ux`, PR **#404**.
> The owner tapped 7 times on `/fleet` count badges (`18 lanes`, `12 stale`,
> `9 outstanding orders`, …) that LOOKED tappable but had no handler, and long
> monospace values in the per-seat status cards clipped off the right edge on a
> phone. This session makes each count a real server-rendered drill-down to the
> lanes behind it, flattens the purely-informational pills so only drill-downs
> read as interactive, and wraps + contrast-bumps the mobile value/label cells.

- **📊 Model:** Claude Opus 4.8 · medium · feature build

**What this session is about:** `/fleet` (control-plane overview, live at
control-plane-production) renders a fleet-heartbeat card whose summary strip is a
row of count pills and, below, one status card per lane. Two owner problems:
(1) the count pills look like filters/buttons but do nothing — the owner wants to
tap `12 stale` and SEE WHICH lanes are stale; (2) at 480px the per-seat status
cards clip long values (heartbeat prose, `done=` lines, trigger IDs, branch/tool
names) behind a horizontal scrollbar, and the grey label column is hard to read.
Both are GET views — the CSRF/same-origin floor is untouched.

⚑ Self-initiated: no — coordinator-dispatched (owner-live UX ask).

## Close-out

**Evidence:**

- **the drill-downs — `app/fleet.py` `overview()`:** each summary count and its
  member list are now derived TOGETHER (one source of truth — a count can never
  disagree with the list the page expands under it). Nine new summary keys carry
  the lanes behind each count: `total_lanes`, `live_lanes`, `stale_lanes`,
  `broken_lanes`, `errored_lanes`, `no_file_lanes`, `stranded_lanes`,
  `silent_routine_lanes`, `outstanding_order_lanes`. Every count is now
  `len(<its list>)` (outstanding-orders sums the per-lane id lists). No new
  fetch, no new route, no state — pure presentation over the already-fetched
  lanes.
- **the template — `app/templates/fleet.html`:** a `count_drill` macro renders
  each count as an inline `<details class="drill">` whose expanded `.drill-list`
  names the exact lanes, each deep-linked to that lane's card anchor
  (`#lane-<repo>`); stranded/outstanding drills carry the branch / order-ids.
  A zero count degrades to a flat non-interactive `.tag` badge (no dead
  expander). Purely-informational pills — per-lane `stale`/health, `live from
  registry`, `all acked done`, the routine/landing/tooling annotations, the
  coverage tags — are now `.b.tag` (flat). Each lane card gained
  `id="lane-<repo>"`.
- **the CSS — `app/templates/base.html`:** `.drill` expander styling with a
  caret INSIDE the pill (▸/▾) so it reads as interactive without hover, i.e. on a
  phone; a `.drillrow` flex container keeps closed badges a compact strip but
  lets an opened expander take its own full-width row; `.b.tag` drops the
  button-ish outline. `table.kv` value cells get `overflow-wrap:anywhere` +
  `word-break:break-word`, the label column bumps from the faint `--dim` grey to
  `#c9d1d9`, and the phone-width `min-width:520px` scroll rule is overridden
  (`min-width:0`) for the kv table so it wraps to fit instead of scrolling.
- **contract pin — `tests/test_fleet_json_contract.py`:** the `/fleet.json`
  summary payload changed (nine member-list keys), so the pinned `SUMMARY_KEYS`
  set was updated in the same PR per contract-pin discipline.
- **tests — new `tests/test_fleet_overview_drilldowns.py` (13 cases):** each
  count's drill-down lists EXACTLY its lanes (stale → only the stale lanes; same
  for live / no-file / outstanding-with-ids / stranded-with-branch / packages);
  a zero count renders a flat non-drill tag (and a 0-count badge with the
  `{% if %}` guard renders nothing at all); the overview stays GET-only
  (`POST /fleet` → 405 — no state route added, CSRF floor untouched);
  count == member-list length (single source of truth); and the `.kv`
  wrap/contrast/anchor markup is present.
- **verify:** `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` → **1871 passed, 1 warning** (exit 0; the only warning is the
  pre-existing Starlette/httpx TestClient deprecation). `python3 bootstrap.py
  check --strict` and `--require-session-log` → the only red is the DESIGNED
  born-red hold on THIS card, released at this flip (gating on exactly 1 card —
  mine).
- **phone-width Playwright (480px, Chromium at /opt/pw-browsers via
  `executable_path`):** against the app served locally with a stubbed GitHub
  layer, at a 480px viewport — (1) the `stale` count badge expanded on click
  (`open` False→True) revealing its lane list (`botsite, review`) and the
  outstanding-orders drill revealed per-lane ids; (2) no horizontal overflow
  (`body.scrollWidth == innerWidth == 480`; the `.kv` table 427px fits inside
  its 452px card); (3) the label `th` computed color is `rgb(201,209,217)` =
  `#c9d1d9`, the legible bump. Screenshots in the scratchpad
  (`fleet-phone-480-before.png`, `fleet-phone-480-expanded.png`).
- **files:** `app/fleet.py`, `app/templates/fleet.html`,
  `app/templates/base.html`, `tests/test_fleet_overview_drilldowns.py`,
  `tests/test_fleet_json_contract.py`, `control/status.md`, and this card.

**Judgment:**

- Decisions made: (1) **Derive the drill-down lists in Python next to the
  counts, not by re-filtering in Jinja** — a count and its list share one
  computation, so they can never drift (a template re-filter with slightly
  different "healthy" logic could show a count of N over a list of N±1). This
  cost nine new `/fleet.json` summary keys and one pin update — the right price
  for the invariant, and machine consumers (the manager) now read WHICH lanes,
  not just how many. (2) **Inline `<details>` expander, not a new route or query
  param** — the cleanest option that needs no new state and adds no CSRF surface;
  the data was already in the request. (3) **Caret INSIDE the pill as the
  affordance** — hover/cursor cues are invisible on a phone (where the owner
  actually tapped), so a ▸/▾ glyph is what marks a badge expandable; flattening
  the non-drill pills to `.tag` completes the signal (only carets are
  interactive). (4) **Scope the mobile wrap to a `.kv` class** — the global
  `min-width:520px` rule legitimately keeps wide data tables (activity timeline)
  scrollable; only the 2-column key/value status table should wrap.
- Next session should know: the `/fleet.json` summary now carries per-count
  member lists — reuse them rather than re-deriving "which lanes are stale" from
  the lane array. A NEW count added to the summary strip should follow the same
  pattern (member list + `count_drill`) so it drills too. And a live phone-width
  re-verify against the deployed control-plane (real registry data, real device)
  is the honest post-merge follow-up — the local check used a stubbed lane set.

## 💡 Session idea

**A "jump to first attention lane" affordance at the top of `/fleet`.** The page
already attention-sorts lanes (fetch-error → broken → stale/stranded/silent →
…), and now every summary count drills to its lanes — but on a phone the owner
still scrolls past the whole summary card to reach the first problem lane. A
single "↓ first needs-attention: <lane>" link under the summary strip (or making
the `N broken`/`N stale` drill entries the primary scroll target) would turn the
glance into one tap-to-the-problem. It reuses the sort rank already computed in
`_sort_key` and the anchors added this session — no new data, pure navigation.

## ⟲ Previous-session review

`.sessions/2026-07-18-declare-env-vars.md` (the session-ender, PR #403) closed
B6's loop by declaring the two env vars B6 had deliberately left visible-but-
unfixed, and updated both committed inventories plus the real-snapshot pin in
lockstep — exactly the three-place discipline `test_inventory_consistency.py`
enforces. Its surface-then-declare-across-two-sessions call was right, and its
💡 (collapse the declared side to one generated source so declaring a var is one
edit, not three) is a real follow-up worth a future slice; this session's own
"one source of truth for count + list" instinct is the same shape applied to a
different surface.
