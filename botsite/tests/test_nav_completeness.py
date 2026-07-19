"""Guard: the hand-maintained botsite NAV must stay in sync with page routes.

The ``NAV`` list in ``botsite/app.py`` is maintained by hand, and nothing fails
at runtime when a new top-level page is added to the router but left out of NAV
(an orphaned page), or when a NAV entry points at a path with no route. This
test derives the truth from the FastAPI router so either kind of drift fails
loudly, and forces every new top-level GET route to be classified as one of:
a nav page (NAV), a non-page endpoint (NON_PAGE_PATHS), or a real page that is
intentionally kept out of the top nav (PAGES_NOT_IN_NAV).
"""
from fastapi.testclient import TestClient

from botsite.app import NAV, app

# GET routes that are not pages: health/probe endpoints, machine-readable
# feeds, and static assets. Adding a new one requires listing it here.
NON_PAGE_PATHS = {
    "/healthz",
    "/version",
    "/favicon.ico",
    "/palette.json",
    "/testing/owner/export.json",
    "/submit/queue.json",
    # Discord OAuth callback (ORDER 037) — a machine auth endpoint, not a page.
    "/owner/auth/callback",
}

# Real HTML pages that are reachable but deliberately NOT in the top nav
# (home, the design/submission surface, the gated owner queue, and the
# trailing-slash alias of /testing). Listed so the guard can tell an
# intentional off-nav page from an accidentally-orphaned one.
PAGES_NOT_IN_NAV = {
    "/",
    "/design",
    "/submit",
    "/products/catalog",
    "/testing/owner",
    "/testing/",
    # Discord owner login (ORDER 037): a real HTML page (the door), deliberately
    # off the top nav. Unconfigured it renders an honest HTTP-200 "not
    # configured" page — reachable, never a broken route.
    "/owner/login",
}

NAV_PATHS = {entry[2] for entry in NAV}

# Documented reachable status for any off-nav page that does NOT return a plain
# 200. Maps a PAGES_NOT_IN_NAV path to its expected status: an int pins an exact
# status, a set allows a small documented range where the status is genuinely
# environment-dependent. Every off-nav path absent from this dict must return
# 200. A 404 or 500 is never allowed here — that is the route-rot this guard
# exists to catch.
OFF_NAV_EXPECTED_STATUS = {
    # Gated owner queue, fail-closed auth (botsite/testing.py::require_owner,
    # mirroring app/owner.py): 503 when SITE_PASSWORD is unset (the default in
    # tests/CI), 401 when it is set but no/wrong Basic auth is sent. Both are
    # the intentional auth gate — the page is reachable, never a broken route.
    "/testing/owner": {401, 503},
}


def _iter_get_routes(router):
    """Yield every GET APIRoute reachable from ``router``, recursing includes."""
    for route in getattr(router, "routes", []):
        original = getattr(route, "original_router", None)
        if original is not None:
            yield from _iter_get_routes(original)
            continue
        methods = getattr(route, "methods", None)
        if methods and "GET" in methods:
            yield route


def _top_level_get_paths():
    """Paths of GET routes that are top-level (no path parameters)."""
    return {r.path for r in _iter_get_routes(app) if "{" not in r.path}


def test_nav_entries_resolve_to_routes():
    """Every NAV path corresponds to a registered top-level GET route."""
    missing = NAV_PATHS - _top_level_get_paths()
    assert not missing, f"NAV entries point at unregistered paths: {sorted(missing)}"


def test_every_page_route_is_classified():
    """No top-level GET route is left unclassified (orphaned-page guard)."""
    unclassified = _top_level_get_paths() - NAV_PATHS - NON_PAGE_PATHS - PAGES_NOT_IN_NAV
    assert not unclassified, (
        "top-level GET routes are unclassified — add each to NAV (a nav page), "
        "NON_PAGE_PATHS (a feed/probe/asset), or PAGES_NOT_IN_NAV (an intentional "
        f"off-nav page): {sorted(unclassified)}"
    )


def test_classification_lists_have_no_stale_entries():
    """NON_PAGE_PATHS and PAGES_NOT_IN_NAV only list still-registered routes."""
    paths = _top_level_get_paths()
    stale = (NON_PAGE_PATHS | PAGES_NOT_IN_NAV) - paths
    assert not stale, f"classification lists name unregistered paths: {sorted(stale)}"


def test_off_nav_pages_still_reachable():
    """Every intentional off-nav page still RESPONDS with its documented status.

    Classification (the tests above) proves a page's route is *registered*;
    this proves it still *responds*. A route can stay registered while throwing
    at request time, so an off-nav page (home, /design, the gated owner queue)
    could silently 404/500 while PAGES_NOT_IN_NAV still names it as a live page.
    This GETs each one and pins its documented reachable status, so that rot
    fails loudly. Redirects are not followed so a 3xx is observed as a 3xx.
    """
    with TestClient(app) as client:
        for path in sorted(PAGES_NOT_IN_NAV):
            resp = client.get(path, follow_redirects=False)
            expected = OFF_NAV_EXPECTED_STATUS.get(path, 200)
            allowed = {expected} if isinstance(expected, int) else set(expected)
            assert resp.status_code in allowed, (
                f"off-nav page {path!r} returned {resp.status_code}; expected "
                f"{sorted(allowed)} — a page listed in PAGES_NOT_IN_NAV must "
                "stay reachable (never a silent 404/500)"
            )
