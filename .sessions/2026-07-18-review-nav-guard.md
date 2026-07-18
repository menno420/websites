# 2026-07-18 — NAV-completeness guard for the review service

> **Status:** `complete` — branch `claude/review-nav-guard`, PR #416. The
> born-red hold on this card kept the `quality` gate red until the guard test
> landed green; this flip releases it.

- **📊 Model:** Claude Opus 4.8 · high · test writing (router-introspection guard)

**What this session is about:** add a guard test so the hand-maintained `NAV`
list in `review/app.py` cannot silently drift from the actual top-level page
routes. Today nothing fails when a page route is added to the router but left
out of NAV (an orphaned page), or when a NAV entry points at a path with no
route (a dead nav link). The previous `2026-07-18-review-questions-nav` card
(R1) fixed exactly one such orphan — a first-class `/questions` page that
returned 200 but was absent from the header NAV — and flagged this gap as its
session idea: a route-introspection completeness guard.

## Plan

- New `review/tests/test_nav_completeness.py`, three assertions, no production
  code change:
  1. every NAV path resolves to a registered top-level GET route (no dead nav
     links),
  2. every top-level GET route is either in NAV or on an explicit non-page
     allow-list (no orphaned pages),
  3. the non-page allow-list has no stale entries (all still routed).
- The test introspects `app.routes` (recursing included routers) and derives
  the truth from the FastAPI router rather than a second hand-maintained list.
- Test-only. No change to `review/app.py`, templates, data, or env.

⚑ Self-initiated: no — coordinator-dispatched, promoting the R1 card's session
idea (the NAV-completeness guard) from `docs/ideas` into a shipped test.

## What was done

- New `review/tests/test_nav_completeness.py` (test-only, 3 assertions):
  `_iter_get_routes` recurses `app.routes` (following included routers) to
  collect every GET `APIRoute`; `_top_level_get_paths` keeps those without a
  path parameter. `test_nav_entries_resolve_to_routes` fails on a NAV path
  with no route (dead nav link); `test_page_routes_are_in_nav_or_classified`
  fails on a top-level GET route that is neither in NAV nor on the explicit
  `NON_PAGE_PATHS` allow-list (orphaned page — the R1 failure class);
  `test_non_page_paths_are_registered` fails on a stale allow-list entry.
- No production code change — `review/app.py`, templates, data, and env are
  untouched.
- Verified: `python3 -m pytest review/tests -q` — 265 passed (3 new);
  `python3 -m pytest tests/ botsite/tests dashboard/tests review/tests -q` —
  **1920 passed, 1 warning** (the pre-existing Starlette/httpx deprecation,
  not this work); `python3 bootstrap.py check --strict` — GREEN after this
  flip (its only red before the flip was the DESIGNED born-red hold on this
  card's in-progress Status).

⚑ Self-initiated: no — coordinator-dispatched, promoting the R1 card's
`2026-07-18-review-questions-nav.md` session idea (a NAV-completeness guard)
from a flagged gap into a shipped test.

## 💡 Session idea

**Extend the router-introspection NAV guard to botsite and dashboard.** The
same page-route-vs-NAV drift the review service just closed exists in the two
sibling services with hand-maintained NAV lists — `botsite/app.py` (`NAV`,
line 49) and `dashboard/app.py` (`NAV`, line 55) — where a newly-built page
can likewise ship orphaned from the header with nothing failing. Worth having
because it generalises a proven guard to two more surfaces at near-zero cost
(the review test is ~60 lines, mostly reusable). Verified first that `app/`
does NOT need it: the control-plane already has `app/nav.py` as a single nav
manifest with `tests/test_nav_manifest.py` holding route coverage — so this
idea is scoped to botsite + dashboard, not all three. Deduped against
`docs/ideas/backlog.md`: the closest entry is the 2026-07-11 nav-scan-glob
guard (a different property — file-enumeration drift), not this route-vs-NAV
completeness check; no duplicate.

## ⟲ Previous-session review

`.sessions/2026-07-18-review-questions-nav.md` (R1) did the right thing by not
just fixing the orphaned `/questions` page but naming the systemic gap — a
hand-maintained NAV that fails silently on drift — as its session idea; this
session closes that idea. What R1 could not do inside its own scope was pin
the property, which is exactly what this guard now does.
