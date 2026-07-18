"""Guard: the hand-maintained review NAV must stay in sync with page routes.

The ``NAV`` list in ``review/app.py`` is maintained by hand, and nothing fails
at runtime when a new top-level page is added to the router but left out of NAV
(an orphaned page), or when a NAV entry points at a path with no route. These
tests derive the truth from the FastAPI router so either kind of drift fails
loudly, and force every new top-level GET route to be classified as a nav page
or an explicit non-page endpoint.
"""
from review.app import NAV, app

# Top-level GET routes that are intentionally NOT nav pages: JSON/data feeds,
# health/probe endpoints, static assets, machine-readable feeds. Adding a new
# one of these requires listing it here — that requirement is the guard.
NON_PAGE_PATHS = {
    "/healthz",
    "/version",
    "/favicon.ico",
    "/story.json",
    "/fleet.json",
    "/releases.json",
    "/reviews/feed.xml",
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


def test_page_routes_are_in_nav_or_classified():
    """Every top-level GET route is in NAV or explicitly a non-page endpoint."""
    unclassified = _top_level_get_paths() - NAV_PATHS - NON_PAGE_PATHS
    assert not unclassified, (
        "top-level GET routes are neither in NAV nor listed as a non-page — "
        f"orphaned pages? add them to NAV or NON_PAGE_PATHS: {sorted(unclassified)}"
    )


def test_non_page_paths_are_registered():
    """The non-page exclusion list has no stale entries (all still routed)."""
    stale = NON_PAGE_PATHS - _top_level_get_paths()
    assert not stale, f"NON_PAGE_PATHS lists unregistered paths: {sorted(stale)}"
