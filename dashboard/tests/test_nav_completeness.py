"""Guard: the hand-maintained dashboard NAV must stay in sync with page routes.

The ``NAV`` list in ``dashboard/app.py`` is maintained by hand, and nothing
fails at runtime when a new top-level page is added to the router but left out
of NAV (an orphaned page), or when a NAV entry points at a path with no route.
This test derives the truth from the FastAPI router so either kind of drift
fails loudly, and forces every new top-level GET route to be classified as one
of: a nav page (NAV), a non-page endpoint (NON_PAGE_PATHS), or a real page that
is intentionally kept out of the top nav (PAGES_NOT_IN_NAV).
"""
from fastapi.testclient import TestClient

from dashboard.app import NAV, app

# GET routes that are not pages: health/probe endpoints, machine-readable
# feeds, static assets, and cross-service redirects. Adding a new one
# requires listing it here.
NON_PAGE_PATHS = {
    "/healthz",
    "/version",
    "/favicon.ico",
    "/palette.json",
    "/games",    # 302 redirect to the botsite games page
    "/reviews",  # 302 redirect to the review service
}

# Real HTML pages that are reachable but deliberately NOT in the top nav
# (home, the status page, and the gated /admin surface). Note /status is
# intentionally off-nav here — unlike botsite, where it is a nav entry — so a
# future maintainer should not "fix" its absence from the dashboard NAV.
PAGES_NOT_IN_NAV = {
    "/",
    "/status",
    "/admin",
    "/admin/cogs",
    "/admin/help",
    "/admin/login",
    "/admin/audit",
}

NAV_PATHS = {entry[2] for entry in NAV}

# Documented reachable status for any off-nav page that does NOT return a plain
# 200. Maps a PAGES_NOT_IN_NAV path to its expected status: an int pins an exact
# status, a set allows a small documented range. Every off-nav path absent from
# this dict must return 200. A 404 or 500 is never allowed here — that is the
# route-rot this guard exists to catch. Dashboard's /admin* pages are
# unauthenticated display panels (dashboard/app.py — no SITE_PASSWORD gate; the
# wired admin surface lives in a separate service), so every off-nav page here
# renders 200 and this dict is empty.
OFF_NAV_EXPECTED_STATUS: dict[str, object] = {}


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
        "NON_PAGE_PATHS (a feed/probe/asset/redirect), or PAGES_NOT_IN_NAV (an "
        f"intentional off-nav page): {sorted(unclassified)}"
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
    at request time, so an off-nav page (home, /status, the /admin panels)
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
