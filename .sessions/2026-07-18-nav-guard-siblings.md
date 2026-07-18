# 2026-07-18 — NAV-completeness guards for botsite + dashboard

> **Status:** `complete` — branch `claude/nav-guard-siblings`, PR #418. The
> born-red hold on this card kept the `quality` gate red until the two guard
> tests landed green; this flip releases it.

- **📊 Model:** Claude Opus 4.8 · high · test authoring (router-introspection guard)

**What this session is about:** extend the router-introspection
NAV-completeness guard to the `botsite` and `dashboard` services. The review
service shipped this guard earlier today (`2026-07-18-review-nav-guard.md`,
PR #416) and `app/` already has route coverage via `tests/test_nav_manifest.py`
over its single `app/nav.py` manifest — but botsite and dashboard both carry
hand-maintained `NAV` lists in their `app.py` that drift silently: a new page
route left out of NAV ships orphaned from the header, and a NAV entry pointing
at a dead path fails nothing at runtime.

## Plan

- New `botsite/tests/test_nav_completeness.py` + `dashboard/tests/test_nav_completeness.py`,
  each self-contained per service (introspects only its own `app.routes`,
  recursing included routers — no cross-service imports). Test-only, no
  production code change.
- Design difference from the review guard: botsite and dashboard both have
  real HTML pages deliberately OUTSIDE the top nav (home `/`, the design /
  submission surface, the gated `/admin` / owner-queue pages). So each guard
  uses an explicit `PAGES_NOT_IN_NAV` allowlist ALONGSIDE `NON_PAGE_PATHS`:
  every top-level GET route must be classified as a nav page (`NAV`), a
  non-page endpoint (`NON_PAGE_PATHS` — feeds/probes/assets/redirects), or an
  intentional off-nav page (`PAGES_NOT_IN_NAV`). Three assertions per service:
  NAV paths all resolve to routes, every page route is classified, and the
  classification lists have no stale entries.

⚑ Self-initiated: no — coordinator-dispatched, promoting the review guard
card's session idea (extend the router-introspection NAV guard to botsite +
dashboard) from a flagged gap into shipped tests.

## What was done

- New `botsite/tests/test_nav_completeness.py` and
  `dashboard/tests/test_nav_completeness.py` (test-only, 3 assertions each).
  Both share the review guard's `_iter_get_routes` (recurses `app.routes`,
  following included routers) + `_top_level_get_paths` (drops path-parameter
  routes) shape, self-contained per service (each introspects only its own
  `app.routes`, no cross-service import). Each classifies every top-level GET
  route as a nav page (`NAV`), a non-page endpoint (`NON_PAGE_PATHS` —
  feeds/probes/assets, plus dashboard's two 302 cross-service redirects), or
  an intentional off-nav page (`PAGES_NOT_IN_NAV` — home, the design/submit
  surface, the gated owner/admin pages). `test_nav_entries_resolve_to_routes`
  fails on a dead nav link; `test_every_page_route_is_classified` fails on an
  orphaned page; `test_classification_lists_have_no_stale_entries` fails on a
  stale allowlist entry.
- No production code change — `botsite/app.py`, `dashboard/app.py`, templates,
  data, and env are untouched.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests review/tests -q`
  — **1926 passed, 1 warning** (the pre-existing Starlette/httpx testclient
  deprecation, not this work; 6 new tests, 3 per service);
  `python3 bootstrap.py check --strict` — GREEN after this flip (its only red
  before the flip was the DESIGNED born-red hold on this card's in-progress
  Status).

## 💡 Session idea

**Add a reachability assertion to the NAV guards.** The three shipped guards
(review + botsite + dashboard) and `app/`'s `test_nav_manifest.py` verify that
every route is *classified*, but nothing checks that an intentional
off-nav page still *responds*. A successor could assert every
`PAGES_NOT_IN_NAV` entry returns HTTP 200 via `TestClient`, so a deliberately
hidden page (home, `/design`, `/admin`) can't silently 500/404 while the
classification list still names it as a live page. Worth having because a
route staying registered is a weaker guarantee than it still rendering — the
current guard would pass on a page that throws at request time. Deduped
against `docs/ideas/backlog.md` + the review card's own idea (extend the guard
to siblings — now shipped by this session): this is a distinct property
(reachability vs. classification), no duplicate.

## ⟲ Previous-session review

`.sessions/2026-07-18-review-nav-guard.md` (the review guard, now complete)
did the right thing by naming the sibling-service extension as its explicit
session idea rather than over-reaching in one PR — this session executes that
idea cleanly, and its `PAGES_NOT_IN_NAV` allowlist is the one refinement the
review card could not foresee (review had no deliberate off-nav pages; botsite
and dashboard do).
