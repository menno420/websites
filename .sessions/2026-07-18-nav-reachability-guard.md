# 2026-07-18 — NAV off-nav-page reachability guard (botsite + dashboard)

> **Status:** `complete` — branch `claude/nav-reachability-guard`, PR #421. The
> born-red hold on this card kept the `quality` gate red until the two
> reachability tests landed green; this flip releases it.

- **📊 Model:** Claude Opus · medium · test writing

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

- Added `test_off_nav_pages_still_reachable` to
  `botsite/tests/test_nav_completeness.py` and
  `dashboard/tests/test_nav_completeness.py` (test-only; each builds its own
  `fastapi.testclient.TestClient` from its own `app`, no cross-service import).
  For every path in `PAGES_NOT_IN_NAV` it does a `GET`
  (`follow_redirects=False`) and asserts the status against an
  `OFF_NAV_EXPECTED_STATUS` map — an int pins an exact status, a set allows a
  documented range; any path not in the map must return 200. A 404/500 is never
  allowed, which is the route-rot the guard catches. The existing three guard
  tests per file are unchanged.
- Discovered real statuses first (own TestClient per service, no auth sent):
  - **botsite** — `/` 200, `/design` 200, `/submit` 200, `/products/catalog`
    200, `/testing/owner` **503**, `/testing/` 200. The 503 is the intentional
    fail-closed owner-auth gate (`botsite/testing.py::require_owner`, mirroring
    `app/owner.py`): 503 when `SITE_PASSWORD` is unset (tests/CI default), 401
    when it is set but no/wrong Basic auth is sent — both reachable, neither a
    broken route. Pinned as `{"/testing/owner": {401, 503}}` (a documented set
    because the status is genuinely env-dependent; other five pin to 200).
  - **dashboard** — all seven off-nav paths (`/`, `/status`, `/admin`,
    `/admin/cogs`, `/admin/help`, `/admin/login`, `/admin/audit`) return
    **200**. The `/admin*` pages are unauthenticated display panels (no
    `SITE_PASSWORD` gate; the wired admin surface lives in a separate service),
    so `OFF_NAV_EXPECTED_STATUS` is empty and every path pins to 200.
- **review needs no change** and was left untouched: it has no
  `PAGES_NOT_IN_NAV` bucket — `test_page_routes_are_in_nav_or_classified`
  already requires every page be in NAV or NON_PAGE_PATHS, and
  `test_nav_entries_resolve_to_routes` already resolves nav paths. No
  intentional off-nav page exists there to guard.
- No production code change — routes, templates, workflows, and triggers are
  untouched.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests review/tests -q`
  — **1928 passed, 1 warning** (the pre-existing Starlette/httpx testclient
  deprecation, not this work; +2 new tests, 1 per service);
  `python3 bootstrap.py check --strict` — the only red is the DESIGNED born-red
  hold on this card's in-progress Status, released by this flip; all other
  output is advisory (never exit-affecting) and pre-existing on other cards.

## 💡 Session idea

**Reachability guard for `app/` control-plane pages.** This session closed the
reachability gap for the two services with a `PAGES_NOT_IN_NAV` bucket
(botsite + dashboard); review had none. The remaining nav surface is `app/`'s
`tests/test_nav_manifest.py`, which classifies routes off `app/nav.py` but (per
the nav-guard-siblings card) does not GET them. A successor could add the same
`TestClient` reachability assertion over the control-plane's page routes so a
control-plane page can't silently 404/500 while the manifest still lists it —
completing the reachability property across all four services. Distinct from
this PR's scope (a different service + a manifest rather than a hand-nav list),
so no duplicate.

## ⟲ Previous-session review

`.sessions/2026-07-18-nav-guard-siblings.md` (PR #418, complete) did the right
thing by ending on a precisely-scoped session idea — "add a reachability
assertion to the NAV guards" — rather than stretching its classification PR to
also cover response behavior; this session executes that idea cleanly. Its one
unforeseeable wrinkle: the card assumed off-nav pages return 200, but
botsite's `/testing/owner` fail-closes to 503/401 — handled here with a
documented status set rather than a blunt 200 pin, keeping the guard exact.
