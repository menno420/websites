"""Structural clarity-bar gate for the dashboard (ORDER 022 item 1
follow-through, 2026-07-13): every HTML-rendering GET route must open with a
real headline and a visible plain-words purpose lede.

Tonight's clarity bar was audited and fixed page-by-page (PR #231 for
botsite+dashboard, PR #229 for app/, PR #228 for review) — but per-page pins
protect existing pages only. This suite makes the bar STRUCTURAL, shaped
like ``review/tests/test_privacy_lint.py`` (PR #233): it introspects the
app's GET routes, expands parameterized routes to concrete URLs via
``PARAM_EXPANDERS`` (completeness guarded BOTH directions — a new
parameterized route with no expander fails; a stale expander entry fails),
and walks every resulting page asserting the dashboard header idiom: a
``section.sb-page-hero`` containing an ``<h1>`` headline and a
``<p class="sb-lead">`` purpose lede — the 404 page included
(``not_found.html`` carries the full idiom here).

Structurally-different GET responses (JSON twins) live in the explicit
``NON_PAGE_GET_ROUTES`` registry, each with a one-line reason; a stale entry
fails, and a brand-new non-HTML route fails the page walk until classified —
that is the gate. Registry entries are for structurally-different responses
ONLY, never for a page that misses the clarity bar (a miss gets FIXED in the
site's own idiom instead).

Zero network: both data feeds are primed from in-file fixtures (the
tests/test_dashboard.py pattern). The dashboard is PUBLIC ([D-0011]) — every
page, /admin included, is walked with no credentials.
"""

from __future__ import annotations

import re
from html.parser import HTMLParser
from typing import Callable

import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from starlette.routing import Mount

from dashboard import app as app_module
from dashboard import control_plane as cp
from dashboard import data_source as ds

DASHBOARD_FIXTURE = {
    "meta": {
        "generated_at": "2026-07-09T00:00:00Z",
        "build": {"commit": "abcdef1234", "subject": "test build",
                  "committed_at": "2026-07-09T00:00:00Z"},
        "schema_version": 1,
        "counts": {
            "functions": 2, "commands": 3, "setting_keys": 2,
            "setting_domains": 1, "env_vars": 1, "ideas": 1, "bugs": 1,
            "updates": 1, "synonyms": 1, "visible_subsystems": 2, "cogs": 1,
        },
    },
    "catalogue": [
        {"key": "economy", "display_name": "Economy",
         "description": "Coins & shop.", "emoji": "💰",
         "visibility_tier": "user", "visibility_mode": "normal",
         "category": "economy", "tags": ["coins"],
         "entry_points": ["economy"], "capabilities": ["economy.view"]},
        {"key": "ai", "display_name": "AI Platform",
         "description": "AI diagnostics.", "emoji": "🤖",
         "visibility_tier": "administrator", "visibility_mode": "normal",
         "category": "admin", "tags": ["ai"], "entry_points": ["ai"],
         "capabilities": ["ai.view"]},
    ],
    "cogs": [
        {"cog": "EconomyCog", "file": "disbot/cogs/economy.py",
         "subsystem": "economy", "is_cog": True,
         "commands": [
             {"name": "daily", "type": "prefix", "is_group": False,
              "parent": None, "aliases": ["d"], "brief": "Claim daily coins.",
              "button_backed": False},
             {"name": "shop", "type": "both", "is_group": True,
              "parent": None, "aliases": [], "brief": "Open the shop.",
              "button_backed": True},
         ]},
    ],
    "settings": [
        {"domain": "economy", "purpose": "Economy settings.", "keys": [
            {"constant": "DAILY_AMOUNT", "key": "daily_amount", "type": "int",
             "hint": "Coins per daily.", "allowed_values": [], "default": 100},
        ]},
    ],
    "access": {
        "tiers": [
            {"tier": "user", "discord_permission": None, "subsystems": [
                {"key": "economy", "display_name": "Economy",
                 "category": "economy", "emoji": "💰"}]},
            {"tier": "administrator", "discord_permission": "administrator",
             "subsystems": [
                {"key": "ai", "display_name": "AI Platform",
                 "category": "admin", "emoji": "🤖"}]},
        ],
        "total_visible": 2, "internal_count": 0,
    },
    "env_usage": [
        {"name": "DATABASE_URL", "required": True, "usage_count": 1,
         "layers": ["utils"],
         "usages": [{"file": "disbot/utils/db/pool.py", "line": 41,
                     "layer": "utils", "has_default": False}]},
    ],
    "ideas": [
        {"file": "some-idea-2026-07-08.md", "title": "A good idea",
         "status": "ideas", "date": "2026-07-08", "summary": "Do the thing.",
         "subsystems": None},
    ],
    "bugs": [
        {"id": "BUG-0001", "title": "Something broke", "status": "OPEN",
         "summary": "It broke."},
    ],
    "updates": [
        {"file": "2026-07-08-x.md", "date": "2026-07-08", "title": "Session X",
         "status": "complete", "run_type": "", "self_initiated": True},
    ],
    "synonyms": [{"canonical": "daily", "synonyms": ["dailies"]}],
    "bot_changelog": [
        {"date": "2026-06-19", "title": "New site", "kind": "improvement",
         "summary": "New."},
    ],
}

CONSOLE_FIXTURE = {
    "meta": {"generated_at": "2026-07-08T16:20:05Z",
             "build": {"commit": "e9988b3b"}, "schema_version": 1},
    "sessions": [{"file": "2026-07-08-x.md", "date": "2026-07-08",
                  "title": "Session X", "status": "complete", "run_type": "",
                  "self_initiated": False}],
    "ideas": {"total": 221, "by_status": {"ideas": 200, "historical": 21}},
    "bugs": {"total": 30, "by_status": {"fixed": 27, "open": 3},
             "open_count": 3,
             "open": [{"id": "BUG-0031", "title": "Something is off",
                       "status": "open"}]},
    "bot_changelog": [{"date": "2026-06-19", "title": "New site",
                       "kind": "improvement", "summary": "New."}],
    "telemetry": [],
}


@pytest.fixture()
def client():
    ds.clear_cache()
    cp.controller.clear()
    ds.prime_cache(ds.DASHBOARD_JSON_URL, DASHBOARD_FIXTURE)
    ds.prime_cache(ds.CONSOLE_JSON_URL, CONSOLE_FIXTURE)
    ds.set_client(ds.make_client())  # never actually hit (cache is warm)
    with TestClient(app_module.app) as c:
        yield c
    ds.clear_cache()
    cp.controller.clear()


# --------------------------------------------------------------------------- #
# Classification registries
# --------------------------------------------------------------------------- #
NON_PAGE_GET_ROUTES: dict[str, str] = {
    "/healthz": "JSON health probe (Railway healthcheck) — no page shell",
    "/version": "JSON deployed-sha endpoint — machine twin, no page shell",
    "/palette.json": "JSON design-palette feed — machine data, no page shell",
}

MOUNT_EXEMPT: dict[str, str] = {
    "/static": "static asset mount (css/js/img) — files, not pages",
}


def _settings_domain_urls() -> list[str]:
    domains = [s["domain"] for s in DASHBOARD_FIXTURE["settings"]]
    assert domains, "fixture settings are empty — /admin/settings/{domain} expander is dead"
    return [f"/admin/settings/{d}" for d in domains]


PARAM_EXPANDERS: dict[str, Callable[[], list[str]]] = {
    "/admin/settings/{domain}": _settings_domain_urls,
}


# --------------------------------------------------------------------------- #
# Route introspection (recursing through FastAPI's include_router wrapper,
# should the dashboard ever grow one — today all routes sit on the app).
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
    return {r.path for r in _iter_get_routes(app_module.app.routes)}


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
            if self._in_hero():
                if ctag in ("h1", "h2") and len(text) >= 3:
                    self.hero_headlines.append(text)
                elif ctag == "p" and "sb-lead" in classes and len(text) >= 10:
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
    mounts = {r.path for r in app_module.app.routes if isinstance(r, Mount)}
    assert mounts == set(MOUNT_EXEMPT), (
        f"mounts {sorted(mounts)} != exempted {sorted(MOUNT_EXEMPT)} — "
        "classify every mount with its reason"
    )


def test_every_html_page_carries_headline_and_lede(client):
    """Walk every concrete HTML GET URL — the dashboard is public, so no
    credentials anywhere — and hold each to the sb-page-hero idiom."""
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
    assert len(urls) >= 15, f"suspiciously small page walk: {sorted(urls)}"


def test_404_page_carries_the_full_idiom_too(client):
    """The dashboard's not_found.html carries the complete hero idiom — the
    404 surface is held to the same bar as every walked page."""
    r = client.get("/no-such-page")
    assert r.status_code == 404
    assert page_problems("/no-such-page", r.text) == []


def test_static_mount_serves_a_real_file(client):
    from pathlib import Path

    static_dir = Path(app_module.__file__).resolve().parent / "static"
    files = [p for p in static_dir.rglob("*") if p.is_file()]
    assert files, "dashboard/static is empty — the mount exemption is stale"
    rel = files[0].relative_to(static_dir).as_posix()
    assert client.get(f"/static/{rel}").status_code == 200
