# 2026-07-13 — review-site cold pass: fix findings ahead of EAP close (ORDER 022 item 5)

> **Status:** `complete` — branch `claude/review-cold-pass`, PR #228.

- **📊 Model:** Claude Fable 5 · worker · cold-pass review + fixes

**What this session was about:** ORDER 022 item 5 — cold-browser pass over
the live review site (EAP closes 2026-07-14); fix findings within existing
routes; clarity bar per item 1. Order rung: dispatched by the coordinator
from the 2026-07-13 night-run ORDER 022 (item 5); scope is review/ +
review/tests only, no URL/structure changes.

## What was done

- <findings + fixes land here as the pass proceeds>
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — <pending>; `python3 bootstrap.py check --strict` —
  <pending>.

## Cold pass findings (live audit of review-production-f027.up.railway.app)

- **F1 — fixed (broken, sitewide):** `SBDS.initChrome()` was defined by the
  vendored `review/static/ds/ds.js` but never called — at 375px the nav
  links were hidden with a dead hamburger (no mobile navigation at all), the
  theme toggle did nothing, and both header buttons rendered as empty
  icon-less squares. Fix: new `review/static/site.js` (the botsite/dashboard
  `static/app.js` idiom — guard on `window.SBDS`, call `SBDS.initChrome()`,
  register the server-rendered nav in the palette; no network fetch, the
  service stays network-free), included from `base.html` after `ds.js`.
  Test-pinned in `review/tests/test_review.py`.
- **F2 — fixed (confusing):** /fleet offered an always-empty "hub · 0"
  disposition pill (the fixed facet universe includes "hub"; the committed
  mirror has 0 hub-disposition lanes) while the page prose calls two seats
  "hub". Fix at the route layer, never the data: `review/app.py` now drops
  zero-count facet options that are not actively selected; an active
  zero-count value (e.g. a `/fleet?disposition=hub` deep link) keeps its
  "on" pill + removable ✕ chip so it can always be un-filtered. The vendored
  `listfilter.py` / `_listfilter.html` stay byte-identical to app/'s copies
  (test-pinned). Tests in `test_fleet.py` (real mirror) +
  `test_review_filters.py` (synthetic suppress-unless-active).
- **F3 — skipped with reason (cosmetic):** Google Fonts is the only external
  runtime dependency. Deliberately NOT vendored now — surface stability
  ahead of the 2026-07-14 EAP close beats a cosmetic self-containment win.
  Flagged as a candidate follow-up: vendor the two font families under
  `review/static/` after the EAP window.
- **Clean bill from the same audit:** 41/41 internal URLs return 200; 0
  broken external links; the clarity bar passes on all pages; 0px mobile
  horizontal overflow.

⚑ Self-initiated: no — coordinator-dispatched slice of ORDER 022 item 5.

## 💡 Session idea

<pending — captured at close with its one-line "worth having because",
deduped against `docs/ideas/backlog.md` + the queue-state NEXT list.>

## ⟲ Previous-session review

<pending — written at close.>
