"""Structural clarity-bar gate for botsite (ORDER 022 item 1
follow-through, 2026-07-13): every HTML-rendering GET route must open with a
real headline and a visible plain-words purpose lede.

Tonight's clarity bar was audited and fixed page-by-page (PR #231 for
botsite+dashboard, PR #229 for app/, PR #228 for review) — but per-page pins
protect existing pages only. This suite makes the bar STRUCTURAL, shaped
like ``review/tests/test_privacy_lint.py`` (PR #233): it introspects the
app's GET routes, expands parameterized routes to concrete URLs via
``PARAM_EXPANDERS`` (completeness guarded BOTH directions — a new
parameterized route with no expander fails; a stale expander entry fails),
and walks every resulting page asserting botsite's header idioms:

- hero pages: a ``section.sb-page-hero`` (or the home page's
  ``section.hero`` variant) containing an ``<h1>`` headline and a
  ``<p class="sb-lead">`` lede;
- detail pages (feature/command): a ``div.sb-detail-head`` containing the
  ``<h1>`` and a ``<p class="tagline">`` lede.

Structurally-different GET responses (JSON twins, the gated binary
screenshot endpoint) live in the explicit ``NON_PAGE_GET_ROUTES`` registry,
each with a one-line reason; a stale entry fails, and a brand-new non-HTML
route fails the page walk until classified — that is the gate. The 404
handler (``not_found.html``) is held to its own pinned shape: a real
``<h1>`` (PR #231's fix).

Registry entries are for structurally-different responses ONLY — never for
a page that misses the clarity bar. A walked page that misses the bar gets
FIXED (a lede in the site's own idiom), not exempted. This session fixed
three such misses: ``testing_task.html``, ``testing_submission.html`` and
``testing_guide.html`` gained ``p.sb-lead`` purpose ledes.

Zero network: the site data feed is primed from an in-file fixture (the
tests/test_botsite.py pattern) and the tester-program store points at a
per-test temp SQLite file (the tests/test_testing.py pattern). The
runtime-token routes (``/testing/s/{token}`` + ``/guide``) are walked by
creating a real claim offline inside the test and following its link.
"""

from __future__ import annotations

import re
from html.parser import HTMLParser
from typing import Callable
from urllib.parse import quote

import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from starlette.routing import Mount

from botsite import app as app_module
from botsite import data_source as ds
from botsite import testing, testing_catalog

PW = "owner-pass"
ORIGIN = {"Origin": "http://testserver"}

FIXTURE = {
    "meta": {"build": {"commit": "abcdef1234", "subject": "test build",
                       "committed_at": "2026-07-09T00:00:00Z"}},
    "counts": {"commands": 2, "features": 2, "games": 1},
    "catalogue": [
        {"key": "economy", "display_name": "Economy",
         "description": "Coins, shop, and daily rewards.", "emoji": "💰",
         "category": "economy", "tags": ["coins", "shop"],
         "badges": ["economy"], "is_game": False},
        {"key": "blackjack", "display_name": "Blackjack",
         "description": "Play blackjack in chat.", "emoji": "🃏",
         "category": "games", "tags": ["cards"], "badges": ["games"],
         "is_game": True},
    ],
    "commands": [
        {"name": "daily", "aliases": ["d"], "category": "economy",
         "permissions": "user", "usage": "Claim your daily coins.",
         "description": "Daily reward.", "examples": ["!daily"],
         "status": "finished", "linked_ideas": []},
        # A name with a URL-reserved char, mirroring superbot's real +prize.
        {"name": "+prize", "aliases": [], "category": "economy",
         "permissions": "moderator", "usage": "Grant a prize.",
         "description": "Grant a prize to a member.", "examples": [],
         "status": "finished", "linked_ideas": []},
    ],
    "bot_changelog": [
        {"date": "2026-06-19", "title": "New site", "kind": "improvement",
         "summary": "A new public site."},
    ],
}


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("TESTING_DB_PATH", str(tmp_path / "testing.sqlite3"))
    monkeypatch.setenv("SITE_PASSWORD", PW)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)  # AI guide: degraded, zero network
    testing.reset_rate_limits()
    ds.clear_cache()
    ds.prime_cache(FIXTURE)
    ds.set_client(ds.make_client())  # never actually hit (cache is warm)
    with TestClient(app_module.app) as c:
        yield c
    ds.clear_cache()


# --------------------------------------------------------------------------- #
# Classification registries
# --------------------------------------------------------------------------- #
NON_PAGE_GET_ROUTES: dict[str, str] = {
    "/healthz": "JSON health probe (Railway healthcheck) — no page shell",
    "/version": "JSON deployed-sha endpoint — machine twin, no page shell",
    "/favicon.ico": "the site icon at the browser-probed path — a file, not a page",
    "/palette.json": "JSON design-palette feed — machine data, no page shell",
    "/testing/owner/export.json": "gated JSON export of the tester-program "
                                  "store — machine data, no page shell",
    "/testing/owner/screenshots/{shot_id}": "gated BINARY image endpoint; ids "
                                            "are runtime submission artifacts, "
                                            "not enumerable from committed data",
}

MOUNT_EXEMPT: dict[str, str] = {
    "/static": "static asset mount (css/js/img) — files, not pages",
}


def _task_urls() -> list[str]:
    ids = [t["id"] for t in testing_catalog.load_tasks()]
    assert ids, "committed testing_tasks.json lists no tasks — expander is dead"
    return [f"/testing/tasks/{tid}" for tid in ids]


def _feature_urls() -> list[str]:
    keys = [e["key"] for e in FIXTURE["catalogue"]]
    assert keys, "fixture catalogue is empty — /features/{key} expander is dead"
    return [f"/features/{quote(k, safe='')}" for k in keys]


def _command_urls() -> list[str]:
    names = [c["name"] for c in FIXTURE["commands"]]
    assert names, "fixture commands are empty — /commands/{name} expander is dead"
    return [f"/commands/{quote(n, safe='')}" for n in names]


def _token_urls(client: TestClient) -> list[str]:
    """The runtime-token pages, reached the honest way: claim a guided task
    offline (the walkthrough task carries a ``steps`` script, so BOTH the
    submission page and the guide page exist for its token)."""
    guided = [t["id"] for t in testing_catalog.load_tasks()
              if t.get("steps") and t.get("status") == "open"]
    assert guided, "no open guided task in testing_tasks.json — expander is dead"
    r = client.post(
        f"/testing/tasks/{guided[0]}/claim",
        data={"name": "Gate Walker", "email": "gate@example.com",
              "paypal_email": ""},
        headers=ORIGIN,
    )
    assert r.status_code == 200, f"claim failed: {r.status_code}"
    m = re.search(r"/testing/s/([A-Za-z0-9_-]+)", r.text)
    assert m, "claim response must show the private submission link"
    token = m.group(1)
    return [f"/testing/s/{token}", f"/testing/s/{token}/guide"]


# Every parameterized HTML GET route needs exactly one entry; expanders take
# the live client because the token routes must create their claim first.
PARAM_EXPANDERS: dict[str, Callable[[TestClient], list[str]]] = {
    "/testing/tasks/{task_id}": lambda client: _task_urls(),
    "/features/{key}": lambda client: _feature_urls(),
    "/commands/{name}": lambda client: _command_urls(),
    "/testing/s/{token}": lambda client: _token_urls(client),
    # the guide rides the same claim token — expanded together above, but the
    # route still needs its own registered (and non-stale) entry:
    "/testing/s/{token}/guide": lambda client: [],
}


# --------------------------------------------------------------------------- #
# Route introspection (recursing through FastAPI's include_router wrapper,
# which keeps the /testing router's routes behind ``original_router``).
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
    paths = {r.path for r in _iter_get_routes(app_module.app.routes)}
    assert any(p.startswith("/testing") for p in paths), (
        "no /testing routes found — route introspection lost the included router"
    )
    return paths


def html_page_urls(client: TestClient) -> list[str]:
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
            urls.extend(expander(client))
        else:
            urls.append(path)
    return urls


# --------------------------------------------------------------------------- #
# The idiom check — tiny HTML parse, never attribute-order-sensitive.
# --------------------------------------------------------------------------- #
_HERO_KINDS = {"sb-page-hero", "hero", "sb-detail-head"}


class _PageScan(HTMLParser):
    def __init__(self):
        super().__init__()
        self._stack: list[bool] = []  # open section/div: True if a hero container
        self._capture: tuple[str, list[str], set[str]] | None = None
        self.hero_headlines: list[str] = []
        self.hero_ledes: list[str] = []
        self.headlines: list[str] = []  # anywhere (the 404 shape check)

    def _in_hero(self) -> bool:
        return any(self._stack)

    def handle_starttag(self, tag, attrs):
        classes = set((dict(attrs).get("class") or "").split())
        if tag in ("div", "section"):
            self._stack.append(tag == "section" and bool(classes & {"sb-page-hero", "hero"})
                               or tag == "div" and "sb-detail-head" in classes)
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
            elif (ctag == "p" and classes & {"sb-lead", "tagline"}
                  and len(text) >= 10 and self._in_hero()):
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
            f"CLARITY MISS — {url}: no <h1>/<h2> headline inside a hero "
            "container (section.sb-page-hero / section.hero / div.sb-detail-head)"
        )
    if not scan.hero_ledes:
        problems.append(
            f"CLARITY MISS — {url}: no visible <p class='sb-lead'> (or "
            "detail-page <p class='tagline'>) purpose lede in the hero"
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
    """Walk every concrete HTML GET URL — the owner queue authenticated,
    the token pages via a real offline claim — and hold each to the idiom."""
    problems: list[str] = []
    urls = html_page_urls(client)
    for url in urls:
        auth = ("owner", PW) if url.startswith("/testing/owner") else None
        r = client.get(url, auth=auth)
        assert r.status_code == 200, f"GET {url} → {r.status_code}"
        problems.extend(page_problems(url, r.text))
    assert not problems, (
        "pages below the clarity bar (fix the page, never allowlist it):\n"
        + "\n".join(problems)
    )
    assert len(urls) >= 20, f"suspiciously small page walk: {sorted(urls)}"


def test_owner_queue_stays_gated_without_credentials(client):
    """The walk authenticates /testing/owner — make sure that is genuinely
    required, so the gate never asserts the idiom on a 401 body."""
    assert client.get("/testing/owner").status_code == 401


def test_404_renders_not_found_page_with_real_headline(client):
    """The 404 handler renders not_found.html with a real <h1> (the PR #231
    fix) — the one page allowed to skip the hero container."""
    r = client.get("/no-such-page")
    assert r.status_code == 404
    scan = _PageScan()
    scan.feed(r.text)
    assert scan.headlines, "404 page carries no real <h1> headline"


def test_static_mount_serves_a_real_file(client):
    from pathlib import Path

    static_dir = Path(app_module.__file__).resolve().parent / "static"
    files = [p for p in static_dir.rglob("*") if p.is_file()]
    assert files, "botsite/static is empty — the mount exemption is stale"
    rel = files[0].relative_to(static_dir).as_posix()
    assert client.get(f"/static/{rel}").status_code == 200
