"""Structural clarity-bar gate for the control-plane (ORDER 022 item 1
follow-through, 2026-07-13): every HTML-rendering GET route must open with a
real headline and a visible plain-words purpose lede.

Tonight's clarity bar was audited and fixed page-by-page (PR #229 for app/,
PR #231 for botsite+dashboard, PR #228 for review) and pinned page-by-page in
``tests/test_clarity_ledes.py`` — but per-page pins protect existing pages
only. This suite makes the bar STRUCTURAL, shaped like
``review/tests/test_privacy_lint.py`` (PR #233): it introspects
``app.routes`` for every GET route, expands parameterized routes to concrete
URLs via ``PARAM_EXPANDERS`` (with a completeness guard in BOTH directions —
a new parameterized route with no expander fails, and a stale expander entry
fails), and walks every resulting HTML page asserting the control-plane
header idiom: an ``<h2>`` headline inside the page's ``div.card`` plus a
``<p class="dim small">`` purpose lede (class ORDER not pinned — parsed, not
substring-matched).

Structurally-different GET responses (JSON twins, the Atom feed) live in the
explicit ``NON_PAGE_GET_ROUTES`` registry, each with a one-line reason; a
stale entry (naming a route that no longer exists) fails, and a brand-new
non-HTML route fails the page walk until it is classified there — that is
the gate. Mounts get the same treatment via ``MOUNT_EXEMPT``.

The control-plane has NO custom 404 page: an unknown path answers FastAPI's
default JSON ``{"detail": "Not Found"}`` — pinned below as the documented
404 shape (it is not an HTML surface, so the idiom does not apply).

Allowlist/registry entries are for structurally-different responses ONLY —
never for a page that misses the clarity bar. A walked page that misses the
bar gets FIXED (a lede in the page's own idiom), not exempted.

Zero network: every GitHub fetch is monkeypatched to the canned offline
degraded result (same fake as tests/test_app.py); pages render their honest
degraded 200s. The gated /owner pages are walked authenticated (HTTP Basic
vs SITE_PASSWORD, same pattern as tests/test_owner_security.py) and held to
the same idiom.
"""

from __future__ import annotations

import base64
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Callable

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.routing import APIRoute  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from starlette.routing import Mount  # noqa: E402

from app import config, envhub, github, roster  # noqa: E402
from app.main import app  # noqa: E402

OWNER_PW = "test-owner-pw"


def _basic(pw: str = OWNER_PW, user: str = "owner") -> dict:
    token = base64.b64encode(f"{user}:{pw}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


@pytest.fixture()
def client(monkeypatch):
    """Offline authed-ready client: every GitHub fetch canned degraded, the
    owner gate armed with a known password, no Railway token."""
    monkeypatch.setattr(config, "SITE_PASSWORD", OWNER_PW)
    monkeypatch.setattr(config, "RAILWAY_TOKEN", "")

    async def fake_get(url, refresh=False, raw=False, follow_redirects=False):
        return {"ok": False, "status": 0, "data": None, "error": "offline test",
                "fetched_at": "", "cached": False, "url": url}

    monkeypatch.setattr(github, "_get", fake_get)
    with TestClient(app) as c:
        yield c


# --------------------------------------------------------------------------- #
# Classification registries — every GET route is either walked as an HTML
# page (idiom asserted) or listed here with its structural reason.
# --------------------------------------------------------------------------- #
NON_PAGE_GET_ROUTES: dict[str, str] = {
    "/healthz": "JSON health probe (Railway healthcheck) — no page shell",
    "/version": "JSON deployed-sha endpoint — machine twin, no page shell",
    "/favicon.ico": "the site icon at the browser-probed path — a file, not a page",
    "/api/readiness.json": "JSON twin of the / board",
    "/activity.json": "JSON twin of /activity",
    "/activity.xml": "Atom feed twin of /activity — XML, not HTML",
    "/fleet.json": "JSON twin of /fleet",
    "/freshness.json": "JSON twin of /freshness",
    "/queue.json": "JSON twin of /queue",
    "/projects.json": "JSON twin of /projects",
    "/reviews.json": "JSON twin of /reviews",
    "/orders.json": "JSON twin of /orders",
    "/ideas.json": "JSON twin of /ideas",
    "/journal/search.json": "JSON twin of /journal/search",
    "/owner/api/readiness.json": "gated JSON twin of the /owner board",
    "/owner/auth/callback": (
        "Discord OAuth callback — an auth-flow endpoint that redirects "
        "(302 to /owner) or errors (503/400/403), never a page shell"
    ),
}

# Mounts are file servers, not pages — exempt with reason (the #233
# MOUNT_EXPANDERS idea reduced to an existence-checked exemption).
MOUNT_EXEMPT: dict[str, str] = {
    "/static": "static asset mount (auto-refresh JS etc.) — files, not pages",
}


def _projects_urls() -> list[str]:
    seats = list(roster.SEATS)
    assert seats, "roster.SEATS is empty — /projects/{package} expander is dead"
    # Offline, the registry listing fails and each detail renders its honest
    # degraded 200 banner page — still held to the header idiom.
    return [f"/projects/{s}" for s in seats]


def _prompt_history_urls() -> list[str]:
    seats = list(roster.SEATS)
    assert seats, "roster.SEATS is empty — /prompts/history/{seat} expander is dead"
    # Seat values derive from the same roster app/prompt_history.py validates
    # against — programmatic, never hardcoded (/prompts collision note: only
    # the shared idiom is asserted, no copy pins).
    return [f"/prompts/history/{s}" for s in seats]


def _journal_repo_urls() -> list[str]:
    repos = sorted(config.REPOS)
    assert repos, "config.REPOS is empty — /journal/{repo} expander is dead"
    return [f"/journal/{r}" for r in repos]


def _journal_file_urls() -> list[str]:
    repos = sorted(config.REPOS)
    assert repos, "config.REPOS is empty — /journal/{repo}/file expander is dead"
    # ?path= is a required query param; offline the fetch degrades honestly
    # on a 200 page that still carries the idiom.
    return [f"/journal/{repos[0]}/file?path=docs/current-state.md"]


def _envhub_manifest_urls() -> list[str]:
    registry = json.loads(envhub.REGISTRY_PATH.read_text(encoding="utf-8"))
    ids = [g["id"] for g in registry.get("groups", []) if g.get("id")]
    assert ids, "environments registry lists no groups — manifest expander is dead"
    return [f"/owner/environments-hub/manifest/{gid}" for gid in ids]


# Every parameterized HTML GET route needs exactly one entry here; the
# completeness test fails a new parameterized route without one AND a stale
# entry whose route was removed.
PARAM_EXPANDERS: dict[str, Callable[[], list[str]]] = {
    "/projects/{package}": _projects_urls,
    "/prompts/history/{seat}": _prompt_history_urls,
    "/journal/{repo}": _journal_repo_urls,
    "/journal/{repo}/file": _journal_file_urls,
    "/owner/environments-hub/manifest/{group_id}": _envhub_manifest_urls,
}


# --------------------------------------------------------------------------- #
# Route introspection. FastAPI (>= 0.139) keeps include_router()-ed routes
# inside a wrapper object exposing ``original_router`` instead of flattening
# them into app.routes — recurse through it so the gated /owner router is
# walked too (its APIRoute paths already carry the /owner prefix).
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
    paths = {r.path for r in _iter_get_routes(app.routes)}
    # If the include_router wrapper ever stops exposing the owner routes,
    # this trips before a silent hole opens in the walk.
    assert any(p.startswith("/owner") for p in paths), (
        "no /owner routes found — route introspection lost the included router"
    )
    return paths


def html_page_urls() -> list[str]:
    """Every concrete HTML-page URL the walk covers; fails on an
    unclassified parameterized route rather than silently skipping it."""
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
# The idiom check — a tiny HTML parse (never attribute-order-sensitive):
# an <h2> with real text inside div.card, and a <p> whose class set contains
# BOTH "dim" and "small" (any order) with real text inside div.card.
# --------------------------------------------------------------------------- #
class _PageScan(HTMLParser):
    def __init__(self):
        super().__init__()
        self._stack: list[bool] = []  # open section/div: True if div.card
        self._capture: tuple[str, list[str], set[str]] | None = None
        self.card_headlines: list[str] = []
        self.card_ledes: list[str] = []

    def _in_card(self) -> bool:
        return any(self._stack)

    def handle_starttag(self, tag, attrs):
        classes = set((dict(attrs).get("class") or "").split())
        if tag in ("div", "section"):
            self._stack.append(tag == "div" and "card" in classes)
        if self._capture is None and tag in ("h2", "p"):
            self._capture = (tag, [], classes)

    def handle_endtag(self, tag):
        if self._capture and tag == self._capture[0]:
            ctag, chunks, classes = self._capture
            text = re.sub(r"\s+", " ", "".join(chunks)).strip()
            if self._in_card():
                if ctag == "h2" and len(text) >= 3:
                    self.card_headlines.append(text)
                elif ctag == "p" and {"dim", "small"} <= classes and len(text) >= 10:
                    self.card_ledes.append(text)
            self._capture = None
        if tag in ("div", "section") and self._stack:
            self._stack.pop()

    def handle_data(self, data):
        if self._capture:
            self._capture[1].append(data)


def assert_page_meets_bar(url: str, html: str) -> list[str]:
    scan = _PageScan()
    scan.feed(html)
    problems = []
    if not scan.card_headlines:
        problems.append(f"CLARITY MISS — {url}: no <h2> headline inside div.card")
    if not scan.card_ledes:
        problems.append(
            f"CLARITY MISS — {url}: no visible <p class='dim small'> purpose "
            "lede inside div.card"
        )
    return problems


# --------------------------------------------------------------------------- #
# The gate
# --------------------------------------------------------------------------- #
def test_classification_matches_the_apps_routes_exactly():
    """Completeness both ways: every registry entry names a live route (a
    stale entry pre-excuses the NEXT route at that path — fail it), every
    parameterized route is classified, and no route is double-classified."""
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


def test_every_html_page_carries_headline_and_lede(client):
    """Walk every concrete HTML GET URL (owner pages authenticated) and hold
    each to the header idiom. Offline degraded pages still answer 200 with
    the idiom intact — honest degradation happens under the lede, not
    instead of it."""
    problems: list[str] = []
    urls = html_page_urls()
    for url in urls:
        headers = _basic() if url.startswith("/owner") else {}
        r = client.get(url, headers=headers)
        assert r.status_code == 200, f"GET {url} → {r.status_code}"
        problems.extend(assert_page_meets_bar(url, r.text))
    assert not problems, (
        "pages below the clarity bar (fix the page, never allowlist it):\n"
        + "\n".join(problems)
    )
    assert len(urls) >= 30, f"suspiciously small page walk: {sorted(urls)}"


def test_owner_pages_stay_gated_without_credentials(client):
    """The walk authenticates — make sure that is genuinely required, so the
    gate never silently starts asserting the idiom on a 401 body."""
    r = client.get("/owner")
    assert r.status_code == 401


def test_unknown_path_answers_the_documented_json_404(client):
    """No custom HTML 404 exists on the control-plane (documented shape):
    unknown paths answer FastAPI's default JSON detail. If someone ships an
    HTML 404 later, this pin fails and the new page joins the walked set."""
    r = client.get("/no-such-page")
    assert r.status_code == 404
    assert r.json() == {"detail": "Not Found"}


def test_static_mount_serves_a_real_file(client):
    """The /static exemption stays honest: the mount exists AND serves."""
    static_dir = Path(__file__).resolve().parents[1] / "app" / "static"
    files = [p for p in static_dir.rglob("*") if p.is_file()]
    assert files, "app/static is empty — the mount exemption is stale"
    rel = files[0].relative_to(static_dir).as_posix()
    assert client.get(f"/static/{rel}").status_code == 200
