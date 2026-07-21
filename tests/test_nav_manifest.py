"""Nav-manifest membership guard: a page cannot be added outside the IA.

The whole information architecture is driven by ONE structure
(``app/nav.py`` ``CATEGORIES`` — the 2-level category → subcategory
hierarchy): the header renders the categories, the landing pages render the
rows, the home map renders both. This module closes the loop: every
``active`` key a control-plane route actually passes to a template must
appear in the manifest, so adding a page without deciding its category
fails the suite instead of silently rendering an un-highlighted page.
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app import github, nav  # noqa: E402
from app.main import app  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
# Every module in the app package is scanned (glob, not a hand-kept list —
# the guard against hand-kept nav lists must not contain one: with the old
# ROUTE_SOURCES = [main.py, owner.py] list, splitting routes into a new
# module silently exited the scan). Source-text based on purpose; a module
# with no `active` keys (owner.py today) simply contributes nothing.
ROUTE_SOURCES = sorted((REPO_ROOT / "app").glob("*.py"))

# `"active": "board"` (context dicts) and `active="board"` (kwargs).
_ACTIVE_RE = re.compile(r'(?:"active"\s*:\s*|\bactive\s*=\s*)"([a-z_]+)"')


def _route_active_keys() -> set[str]:
    keys: set[str] = set()
    for src in ROUTE_SOURCES:
        if src.exists():
            keys.update(_ACTIVE_RE.findall(src.read_text(encoding="utf-8")))
    return keys


def test_every_route_active_key_is_in_the_manifest():
    route_keys = _route_active_keys()
    assert route_keys, "no active keys found — the scan regex rotted"
    missing = route_keys - nav.keys()
    assert not missing, (
        f"route(s) pass active key(s) {sorted(missing)} that are not in the "
        "app/nav.py manifest — place the page in a category (the IA "
        "decision), don't leave it outside the hierarchy"
    )


def test_manifest_keys_are_unique_and_entries_complete():
    cat_keys = [c["key"] for c in nav.CATEGORIES]
    assert len(cat_keys) == len(set(cat_keys)), "duplicate category key"
    item_keys = [
        it["key"] for c in nav.CATEGORIES for it in c["items"] if it["key"]
    ]
    assert len(item_keys) == len(set(item_keys)), "duplicate item key"
    assert not set(item_keys) & set(cat_keys), (
        "an item key shadows a category key — category_for would be ambiguous"
    )
    for cat in nav.CATEGORIES:
        for field in ("key", "label", "href", "desc", "items"):
            assert cat.get(field), f"category entry incomplete: {cat['key']!r}"
        assert isinstance(cat["landing"], bool) and isinstance(
            cat["gated"], bool
        )
        for it in cat["items"]:
            assert it.get("label") and it.get("href") and it.get("desc"), (
                f"item entry incomplete under {cat['key']!r}: {it!r}"
            )
            action = it.get("action")
            assert action and action.get("label") and action.get("href"), (
                f"item missing its primary action: {it.get('label')!r}"
            )


def test_manifest_covers_no_stale_keys():
    """The manifest carries no key NO route uses (dead nav entries rot too)."""
    stale = nav.keys() - _route_active_keys()
    assert not stale, (
        f"manifest key(s) {sorted(stale)} are passed by no route — remove "
        "the dead entry or wire the page"
    )


def test_category_for_maps_every_key_and_rejects_unknowns():
    for cat in nav.CATEGORIES:
        if cat["landing"]:
            assert nav.category_for(cat["key"]) == cat["key"]
        for it in cat["items"]:
            if it["key"]:
                assert nav.category_for(it["key"]) == cat["key"]
    assert nav.category_for(None) is None
    assert nav.category_for("") is None
    assert nav.category_for("no-such-page") is None


def test_lookup_helpers():
    assert nav.category("work")["href"] == "/work"
    assert nav.item("prompts")["href"] == "/prompts"
    hrefs = nav.all_hrefs()
    assert len(hrefs) == len(set(hrefs)), "all_hrefs must be deduped"
    for expected in ("/", "/work", "/history", "/console", "/owner",
                     "/queue", "/prompts", "/owner/environments-hub"):
        assert expected in hrefs


# --- Reachability guard --------------------------------------------------- #
#
# The tests above prove every route is *classified* (its `active` key is in the
# manifest). Classification proves a route is *registered*, not that it still
# *responds* — a route can stay registered while throwing at request time, a
# silent 5xx no classification test catches. The sibling services close this
# with a `TestClient` GET guard (botsite/dashboard/review, PRs #416/#418/#421);
# this is `app/`'s. It derives its truth from the FastAPI router (not the
# hand-maintained manifest) so it also probes the top-level GET routes the
# manifest omits — the JSON/XML feeds, `/journal/search`, `/owner/login`, and
# the gated `/owner/*` twins that `tests/test_category_ia.py`'s manifest walk
# never GETs.

# Gated `/owner/*` pages answer `require_owner` (app/owner.py), which fails
# closed: 503 when NEITHER `SITE_PASSWORD` nor Discord OAuth is configured (the
# tests/CI default), 401 when a password IS set but no/wrong Basic auth is
# sent. Both are the intentional auth gate — the page is reachable, never a
# broken route.
GATED_ALLOWED_STATUS = {401, 503}

# `/owner`-prefixed paths that are NOT behind `require_owner`: the login door
# renders its own page (HTTP 200) before the gate, so an unauthenticated GET
# gets the door, not the gate.
GATED_STATUS_OVERRIDES = {
    "/owner/login": {200},
}


def _offline(monkeypatch):
    """Stub app.github so the reachability GETs never touch the network — the
    same offline seam tests/test_category_ia.py uses. Every fetch reports a
    miss; page routes must degrade honestly to a rendered page, never 5xx."""

    async def fake_get(url, refresh=False, raw=False, follow_redirects=False):
        return {"ok": False, "status": 0, "data": None, "error": "offline test",
                "fetched_at": "", "cached": False, "url": url}

    async def fake_fetch(repo, path, ref="main", refresh=False):
        return {"ok": False, "status": 404, "data": None, "error": "nf",
                "fetched_at": "", "cached": False, "url": ""}

    async def fake_api(repo, subpath="", refresh=False):
        return {"ok": False, "status": 404, "data": None, "error": "nf",
                "fetched_at": "", "cached": False, "url": ""}

    monkeypatch.setattr(github, "_get", fake_get)
    monkeypatch.setattr(github, "fetch_file", fake_fetch)
    monkeypatch.setattr(github, "repo_api", fake_api)


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


def test_every_top_level_get_route_is_reachable(monkeypatch):
    """Every top-level control-plane GET route still RESPONDS non-5xx.

    Derived from the router, so this covers the public pages, the JSON/XML
    feeds, and the gated `/owner/*` twins alike — including the routes the
    `app/nav.py` manifest does not carry (which `tests/test_category_ia.py`'s
    manifest walk never GETs). A route that 500s at request time fails here
    instead of slipping past CI. Redirects are not followed so a 3xx is
    observed as a 3xx, never chased into a 5xx elsewhere.

    Gated `/owner/*` pages must additionally answer their documented auth
    status (`{401, 503}`) — the gate is reachable behaviour, but a 200 there
    (an accidentally-ungated owner page) or a 5xx (a throwing gate) is not.
    """
    _offline(monkeypatch)
    paths = _top_level_get_paths()
    assert paths, "no top-level GET routes found — the router introspection rotted"
    with TestClient(app) as client:
        for path in sorted(paths):
            resp = client.get(path, follow_redirects=False)
            if path in GATED_STATUS_OVERRIDES:
                # An `/owner`-prefixed path that renders BEFORE the gate (the
                # login door): pinned to its documented public status.
                allowed = GATED_STATUS_OVERRIDES[path]
                assert resp.status_code in allowed, (
                    f"route {path!r} returned {resp.status_code}; expected one "
                    f"of {sorted(allowed)} — this owner-prefixed path is "
                    "documented as a public page that renders before the gate"
                )
            elif path.startswith("/owner"):
                # Behind require_owner: 503 (unconfigured — the CI default) is a
                # documented fail-closed status, so these are checked for exact
                # gate membership rather than the plain non-5xx floor below.
                assert resp.status_code in GATED_ALLOWED_STATUS, (
                    f"gated owner route {path!r} returned {resp.status_code}; "
                    f"expected one of {sorted(GATED_ALLOWED_STATUS)} — the "
                    "require_owner gate fails closed (503 unconfigured / 401 on "
                    "bad creds); anything else means the gate changed (a 200 = "
                    "an accidentally-ungated owner page)"
                )
            else:
                # Every public route must respond non-5xx even offline — a
                # registered route that 5xxes at request time is the route-rot
                # this guard catches.
                assert resp.status_code < 500, (
                    f"route {path!r} returned {resp.status_code} — a registered "
                    "route that 5xxes at request time is the route-rot this "
                    "guard catches (it must respond, even offline)"
                )
