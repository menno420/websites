"""Guard: the hand-maintained dashboard NAV must stay in sync with page routes.

The ``NAV`` list in ``dashboard/app.py`` is maintained by hand, and nothing
fails at runtime when a new top-level page is added to the router but left out
of NAV (an orphaned page), or when a NAV entry points at a path with no route.
This test derives the truth from the FastAPI router so either kind of drift
fails loudly, and forces every new top-level GET route to be classified as one
of: a nav page (NAV), a non-page endpoint (NON_PAGE_PATHS), or a real page that
is intentionally kept out of the top nav (PAGES_NOT_IN_NAV).
"""
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
