"""Structural clarity-bar gate for the review service (ORDER 022 item 1
follow-through, 2026-07-13): every HTML-rendering GET route must open with a
real headline and a visible plain-words purpose lede.

Tonight's clarity bar was audited and fixed page-by-page (PR #228 for
review, PR #229 for app/, PR #231 for botsite+dashboard) — but per-page pins
protect existing pages only. This suite makes the bar STRUCTURAL, sharing
its shape with this directory's ``test_privacy_lint.py`` (PR #233): it
introspects ``app.routes`` for every GET route, expands parameterized routes
to concrete URLs via ``PARAM_EXPANDERS`` derived from the committed data
(completeness guarded BOTH directions — a new parameterized route with no
expander fails; a stale expander entry fails), and walks every resulting
page asserting the review header idiom: a ``section.sb-page-hero``
containing an ``<h1>`` headline and a ``<p class="sb-lead">`` purpose lede.

Structurally-different GET responses (JSON twins, the reviews Atom/XML
feed) live in the explicit ``NON_PAGE_GET_ROUTES`` registry, each with a
one-line reason; a stale entry fails, and a brand-new non-HTML route fails
the page walk until classified — that is the gate. The 404 page
(``not_found.html``) renders headline + lede WITHOUT the hero section — its
documented shape is pinned separately below, private-lane detail probes
included (referencing ``fleetdata.PRIVATE_LANES``, never a literal name —
the ORDER 017 D doctrine).

Registry entries are for structurally-different responses ONLY — never for
a page that misses the clarity bar. A walked page that misses the bar gets
FIXED in the site's own idiom instead.

Zero network (same doctrine as test_privacy_lint.py): the site renders from
committed review/data/** at runtime; the one outbound call (the AI
assistant's POST) is additionally monkeypatched to fail loudly if any
walked GET ever reaches for it.
"""

from __future__ import annotations

import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Callable

import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from starlette.routing import Mount

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from review import ai, editions, fleetdata  # noqa: E402
from review.app import app  # noqa: E402

client = TestClient(app)

STATIC_DIR = Path(__file__).resolve().parents[1] / "static"


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    """Belt-and-braces: the walk is GET-only and the site is network-free at
    runtime, but if any page ever reaches for the one outbound call, fail
    loudly instead of touching the network (same guard as test_ai.py)."""
    monkeypatch.setattr(
        ai, "_post_anthropic",
        lambda payload, api_key: (_ for _ in ()).throw(
            AssertionError("outbound model call attempted in a network-free test")
        ),
    )


# --------------------------------------------------------------------------- #
# Classification registries
# --------------------------------------------------------------------------- #
NON_PAGE_GET_ROUTES: dict[str, str] = {
    "/healthz": "JSON health probe (Railway healthcheck) — no page shell",
    "/version": "JSON deployed-sha endpoint — machine twin, no page shell",
    "/favicon.ico": "the site icon at the browser-probed path — a file, not a page",
    "/story.json": "JSON data feed for the front-page charts — machine data",
    "/fleet.json": "JSON twin of /fleet (the filtered committed mirror)",
    "/reviews/feed.xml": "Atom feed twin of /reviews — XML, not HTML",
}

MOUNT_EXEMPT: dict[str, str] = {
    "/static": "static asset mount (css/js/img) — files, not pages",
}


def _fleet_repo_urls() -> list[str]:
    fl = fleetdata.load_fleet()
    assert fl["ok"], f"fleet mirror failed to load: {fl['error']}"
    repos = [ln.get("repo") for ln in fl["data"].get("lanes", []) if ln.get("repo")]
    assert repos, "fleet mirror lists no repo-backed lanes — expander is dead"
    return [f"/fleet/{r}" for r in repos]


def _review_slug_urls() -> list[str]:
    slugs = [e["slug"] for e in editions.list_editions()]
    assert slugs, "no committed review editions — expander is dead"
    return [f"/reviews/{s}" for s in slugs]


PARAM_EXPANDERS: dict[str, Callable[[], list[str]]] = {
    "/fleet/{repo}": _fleet_repo_urls,
    "/reviews/{slug}": _review_slug_urls,
}


# --------------------------------------------------------------------------- #
# Route introspection (recursing through FastAPI's include_router wrapper —
# the ai router rides one; it carries no GET routes today, but a future GET
# on any included router must not dodge the walk).
# --------------------------------------------------------------------------- #
def _iter_get_routes(routes) -> list[APIRoute]:
    found: list[APIRoute] = []
    for r in routes:
        if isinstance(r, APIRoute):
            if "GET" in (r.methods or set()):
                found.append(r)
        elif hasattr(r, "original_router"):
            found.extend(_iter_get_routes(r.original_router.routes))
    return found


def _get_paths() -> set[str]:
    return {r.path for r in _iter_get_routes(app.routes)}


def html_page_urls() -> list[str]:
    urls: list[str] = []
    for path in sorted(_get_paths()):
        if path in NON_PAGE_GET_ROUTES:
            continue
        if "{" in path:
            expander = PARAM_EXPANDERS.get(path)
            assert expander is not None, (
                f"parameterized GET route {path!r} has no PARAM_EXPANDERS "
                "entry and no NON_PAGE_GET_ROUTES classification — register "
                "one so the clarity gate walks (or documented-skips) it"
            )
            urls.extend(expander())
        else:
            urls.append(path)
    return urls


# --------------------------------------------------------------------------- #
# The idiom check — tiny HTML parse, never attribute-order-sensitive.
# --------------------------------------------------------------------------- #
class _PageScan(HTMLParser):
    def __init__(self):
        super().__init__()
        self._stack: list[bool] = []  # open section/div: True if sb-page-hero
        self._capture: tuple[str, list[str], set[str]] | None = None
        self.hero_headlines: list[str] = []
        self.hero_ledes: list[str] = []
        self.headlines: list[str] = []  # anywhere (the 404 shape check)
        self.ledes: list[str] = []      # anywhere (the 404 shape check)

    def _in_hero(self) -> bool:
        return any(self._stack)

    def handle_starttag(self, tag, attrs):
        classes = set((dict(attrs).get("class") or "").split())
        if tag in ("div", "section"):
            self._stack.append(tag == "section" and "sb-page-hero" in classes)
        if self._capture is None and tag in ("h1", "h2", "p"):
            self._capture = (tag, [], classes)

    def handle_endtag(self, tag):
        if self._capture and tag == self._capture[0]:
            ctag, chunks, classes = self._capture
            text = re.sub(r"\s+", " ", "".join(chunks)).strip()
            if ctag in ("h1", "h2") and len(text) >= 3:
                self.headlines.append(text)
                if self._in_hero():
                    self.hero_headlines.append(text)
            elif ctag == "p" and "sb-lead" in classes and len(text) >= 10:
                self.ledes.append(text)
                if self._in_hero():
                    self.hero_ledes.append(text)
            self._capture = None
        if tag in ("div", "section") and self._stack:
            self._stack.pop()

    def handle_data(self, data):
        if self._capture:
            self._capture[1].append(data)


def page_problems(url: str, html: str) -> list[str]:
    scan = _PageScan()
    scan.feed(html)
    problems = []
    if not scan.hero_headlines:
        problems.append(
            f"CLARITY MISS — {url}: no <h1> headline inside section.sb-page-hero"
        )
    if not scan.hero_ledes:
        problems.append(
            f"CLARITY MISS — {url}: no visible <p class='sb-lead'> purpose "
            "lede inside section.sb-page-hero"
        )
    return problems


# --------------------------------------------------------------------------- #
# The gate
# --------------------------------------------------------------------------- #
def test_classification_matches_the_apps_routes_exactly():
    paths = _get_paths()
    param_paths = {p for p in paths if "{" in p}
    stale = [p for p in NON_PAGE_GET_ROUTES if p not in paths]
    stale += [p for p in PARAM_EXPANDERS if p not in param_paths]
    assert not stale, f"stale classification entries (route no longer exists): {stale}"
    overlap = set(PARAM_EXPANDERS) & set(NON_PAGE_GET_ROUTES)
    assert not overlap, f"routes classified BOTH page and non-page: {sorted(overlap)}"
    unclassified = [
        p for p in param_paths
        if p not in PARAM_EXPANDERS and p not in NON_PAGE_GET_ROUTES
    ]
    assert not unclassified, (
        f"parameterized GET routes with no classification: {unclassified}"
    )
    assert param_paths == (
        set(PARAM_EXPANDERS) | {p for p in NON_PAGE_GET_ROUTES if "{" in p}
    )
    mounts = {r.path for r in app.routes if isinstance(r, Mount)}
    assert mounts == set(MOUNT_EXEMPT), (
        f"mounts {sorted(mounts)} != exempted {sorted(MOUNT_EXEMPT)} — "
        "classify every mount with its reason"
    )


def test_every_html_page_carries_headline_and_lede():
    """Walk every concrete HTML GET URL over the real committed data and
    hold each to the sb-page-hero idiom."""
    problems: list[str] = []
    urls = html_page_urls()
    for url in urls:
        r = client.get(url)
        assert r.status_code == 200, f"GET {url} → {r.status_code}"
        problems.extend(page_problems(url, r.text))
    assert not problems, (
        "pages below the clarity bar (fix the page, never allowlist it):\n"
        + "\n".join(problems)
    )
    assert len(urls) >= 20, f"suspiciously small page walk: {sorted(urls)}"


def test_404_surface_keeps_headline_and_lede():
    """not_found.html renders a real <h1> + <p class='sb-lead'> without the
    hero section — the documented 404 shape (the bar's substance without
    the container). Probed on the catch-all path, an unknown edition, an
    unknown fleet repo, AND every private-lane detail URL (referenced via
    fleetdata.PRIVATE_LANES, never a literal — they must 404 like any
    unknown repo, per ORDER 017 D and the privacy lint)."""
    probes = ["/no-such-page", "/reviews/no-such-edition", "/fleet/no-such-repo"]
    probes += [f"/fleet/{lane}" for lane in sorted(fleetdata.PRIVATE_LANES)]
    for url in probes:
        r = client.get(url)
        assert r.status_code == 404, f"GET {url} → {r.status_code}"
        scan = _PageScan()
        scan.feed(r.text)
        assert scan.headlines, f"404 page {url} carries no real headline"
        assert scan.ledes, f"404 page {url} carries no sb-lead lede"


def test_static_mount_serves_a_real_file():
    files = [p for p in STATIC_DIR.rglob("*") if p.is_file()]
    assert files, "review/static is empty — the mount exemption is stale"
    rel = files[0].relative_to(STATIC_DIR).as_posix()
    assert client.get(f"/static/{rel}").status_code == 200
