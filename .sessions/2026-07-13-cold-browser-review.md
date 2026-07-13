# 2026-07-13 — Cold-browser pass #2 over the live review site + the 3 fixes it found

> **Status:** `complete` — PR #311, branch `claude/cold-browser-review-0713`;
> the second 2026-07-13 cold-browser pass (15 routes, 49/49 links) and its
> 3 fixes: favicon on all three sites, the hamburger's initial glyph, and
> the footer's horizontal gutter.

- **📊 Model:** Claude Fable 5 · landing worker · order-slice

**What this session was about:** ORDER 022 item 5 (`control/inbox.md`, "YOUR
SEAT TONIGHT": "One cold-browser pass over the review site (EAP closes Tue
07-14); fix what you find"), re-dispatched as ORDER 027 item 3. A second
cold-browser crawl of the live review site
(https://review-production-f027.up.railway.app, deployed `f47f7ce8`, snapshot
baked `d013a590`) was run against repo HEAD `95a9ef56` with real Chromium
(playwright-core, TLS verification on, `--ssl-version-max=tls1.2` for the
agent proxy). This session lands the pass's evidence and its 3 confirmed
fixes. (The first pass on 2026-07-13 was PR #228 — cold-pass F1/F2 comments
in `review/tests/test_review.py:430` and `review/app.py:196`.)

## Cold-pass evidence — per-page results

15 routes crawled at desktop 1280 and mobile 375×812, console + failed
requests captured, plus a same-site link check:

| Route | Status | Console errors | Failed reqs | Mobile overflow |
|---|---|---|---|---|
| / | 200 | 1 (favicon 404) | none | no |
| /process | 200 | 0 | none | no |
| /growth | 200 | 0 | none | no |
| /fleet | 200 | 0 | none | no |
| /reviews | 200 | 0 | none | no |
| /questionnaire | 200 | 0 | none | no |
| /ask | 200 | 0 | none | no |
| /successes | 200 | 0 | none | no |
| /problems | 200 | 0 | none | no |
| /questions | 200 | 0 | none | no |
| /fleet/superbot | 200 | 0 | none | no |
| /fleet/websites | 200 | 0 | none | no |
| /fleet/fleet-manager | 200 | 0 | none | no |
| /reviews/2026-07-11-edition-001 | 200 | 0 | none | no |
| /this-page-does-not-exist | 404 (branded page) | favicon only | — | no |

- **Link check: 49/49 same-site URLs OK** — the 14 visited pages, all 17
  `/fleet/{repo}` details (14 GET-checked), `/fleet.json`, `/story.json`,
  `/reviews/feed.xml`, and every filter-widget query variant. No broken
  internal links; no `/fleet/None` leaks from the two repo-less
  registry-only seats.
- Zero `pageerror` events, zero console warnings, zero horizontal overflow
  at 1280 or 375 on every page. `/ask` verified end-to-end (403 without
  Origin, grounded 200 with it).
- Content/data: nothing needing action — the snapshot-aged banner and the
  repo-less-seat footnote both handle their cases honestly by design.

## The 3 findings (all fixed this session)

1. **F1 — missing favicon, the site's only console error.** `GET
   /favicon.ico` 404s on every first visit (curl-confirmed; Chromium
   auto-requests it). Fix: `review/static/favicon.svg` (brand-tile SVG —
   the ds green gradient + the review header's ⟲ glyph as a stroke path)
   linked from `review/templates/base.html` head. Botsite and dashboard had
   the identical gap — same fix with their `bot` icon glyph.
2. **F2 — mobile hamburger renders empty until first tap.** At 375px,
   `[data-menu-toggle]` had `innerHTML === ""` at load; `initChrome`
   (`review/static/ds/ds.js:322-338`) painted the glyph only inside the
   click-driven `setMenu()`. Fix: paint `icon("menu", …)` at wiring time
   (ds.js ~line 331). Residue of cold-pass-F1 from PR #228, which wired
   `initChrome` but left the initial icon unpainted. ds.js is byte-identical
   across review/botsite/dashboard — all three copies updated to preserve
   the vendor pin.
3. **F3 — footer loses its horizontal gutter** (text flush to the viewport
   edge at both 1280 and 375; measured computed padding-left/right = 0).
   `.sb-footer-in` (`review/static/ds/components.css:546`) declared
   `padding: var(--sb-s-6) 0`, overriding `.sb-wrap-wide`'s gutter
   (components.css:64) by cascade order on the same element
   (`review/templates/base.html:80`). Fix: `padding: var(--sb-s-6)
   var(--sb-gutter)` — all three components.css copies updated.

## What was done

- `review/static/favicon.svg` + `botsite/static/favicon.svg` +
  `dashboard/static/favicon.svg` (new) and a `<link rel="icon"
  type="image/svg+xml" href="/static/favicon.svg">` in each service's
  `templates/base.html` head.
- `{review,botsite,dashboard}/static/ds/ds.js` — initial hamburger glyph
  painted in `initChrome` (one line beside the existing `aria-label` set);
  the three copies stay byte-identical.
- `{review,botsite,dashboard}/static/ds/components.css` — `.sb-footer-in`
  horizontal padding `0` → `var(--sb-gutter)`; copies stay byte-identical.
- `review/tests/test_review.py` — cold pass #2 memorialized: favicon link
  present + `/static/favicon.svg` served, ds.js carries the init-time glyph
  paint, `.sb-footer-in` carries the gutter.
- `docs/CAPABILITIES.md` — append-log entry: Chromium-via-Playwright behind
  the agent proxy needs `--ssl-version-max=tls1.2` (proxy resets the TLS 1.3
  ClientHello); verified working this session.
- `docs/ideas/backlog.md`: this session's 💡 captured as a new bullet.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — 1345 passed, 1 warning (+3 over main's 1342);
  `python3 bootstrap.py check --strict` — green except this card's own
  designed born-red HOLD (released by this flip).

⚑ Self-initiated: no — ORDER 022 item 5 / ORDER 027 item 3.

## 💡 Session idea

**Scheduled browser-level smoke-crawl in CI** — a scheduled Actions job
launching headless Chromium over each site's route inventory, failing on
console errors / pageerrors / failed requests / horizontal overflow at
375px — the browser-level complement to the curl-level `healthcheck.yml`
smoke. Worth having because both 2026-07-13 cold passes found real
rendering-only regressions (dead chrome wiring, a blank hamburger, a lost
footer gutter, a favicon 404) within hours of each other — visual-layer
rot demonstrably recurs and nothing automatic watches it. Deduped against
`docs/ideas/backlog.md` + the other `.sessions/*.md` cards: the
healthcheck bullets are status-code probes and the webhook-analyzer card
used Playwright once, ad hoc — no scheduled/browser-level crawl idea
exists. Captured in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

The venture-vetting-catalog session (PR #248) did well — 22 packets
curated with nothing invented, per-title states derived from each packet's
own Status/Verdict and pinned by a breakdown test; what it missed is what
its own 💡 admits: the whole catalog is hand-pinned to venture-lab
`2c039e3` with nothing watching for upstream drift, so its honesty has a
shelf life until that sha-drift nag gets built.
