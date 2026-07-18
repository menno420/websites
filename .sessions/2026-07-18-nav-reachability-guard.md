# 2026-07-18 — NAV off-nav-page reachability guard (botsite + dashboard)

> **Status:** `in-progress`

- **📊 Model:** [[fill:model]]

**What this session is about:** the three router-introspection NAV guards
(review + botsite + dashboard) plus `app/`'s `test_nav_manifest.py` prove every
top-level GET route is *classified* — a nav page, a non-page endpoint, or an
intentional off-nav page (`PAGES_NOT_IN_NAV`). None of them prove an
intentionally off-nav page still *responds*. A route can stay registered (so
classification passes) while throwing at request time — a silent 404/500 that
no test catches. This session closes that gap for the two services that carry a
`PAGES_NOT_IN_NAV` bucket: botsite and dashboard.

## Plan

- Add `test_off_nav_pages_still_reachable` to
  `botsite/tests/test_nav_completeness.py` and
  `dashboard/tests/test_nav_completeness.py` (test-only, self-contained per
  service — each builds its own `TestClient` from its own `app`, no
  cross-service import). For every path in `PAGES_NOT_IN_NAV`, a `TestClient`
  GET (`follow_redirects=False`) must return its documented reachable status.
  A 404 or 500 fails the guard loudly.
- An `OFF_NAV_EXPECTED_STATUS` dict pins the documented status for any path
  whose reachable status is not plain 200 (with an inline reason). Every other
  off-nav path is pinned to 200.
- review needs NO change: it has no `PAGES_NOT_IN_NAV` bucket — its test
  already requires every page be in NAV or NON_PAGE_PATHS, and
  `test_nav_entries_resolve_to_routes` already GET-resolves nav paths.
- Keep the existing three tests per file unchanged.

⚑ Self-initiated: no — coordinator-dispatched, promoting the
`2026-07-18-nav-guard-siblings.md` card's session idea ("add a reachability
assertion to the NAV guards") from a flagged gap into shipped tests.

## What was done

- [[fill:what-was-done]]

## 💡 Session idea

- [[fill:idea]]

## ⟲ Previous-session review

- [[fill:review]]
