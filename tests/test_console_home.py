"""Offline unit tests for the console-home discoverability finish (updated
for IA v2): the home page opens with the Overview dashboard whose category
map links EVERY feature page grouped under its category (the long tail the
5-category header deliberately does not carry), the gated owner console is
findable from the footer of every page, and the /fleet lane cards deep-link
each lane's files through the in-app /journal/{repo}/file renderer.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app import config, fleet, github, nav  # noqa: E402
from app.main import app  # noqa: E402

# Every page the home map must link, pinned by hand ON PURPOSE: if a route
# is removed or the category map loses an entry, this list is the tripwire
# (the manifest-derived loop below can't catch a page that falls out of the
# manifest itself).
ALL_FEATURE_ROUTES = [
    "/",
    "/fleet",
    "/freshness",
    "/work",
    "/queue",
    "/orders",
    "/ideas",
    "/reviews",
    "/history",
    "/activity",
    "/journal",
    "/console",
    "/projects",
    "/prompts",
    "/owner/environments-hub",
    "/environments",
    "/owner/environments",
    "/directory",
    "/owner",
    "/owner/briefing",
    "/owner/queue",
]


def _offline(monkeypatch):
    async def fake_get(url, refresh=False, raw=False):
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


def test_home_category_map_links_every_feature_page(monkeypatch):
    _offline(monkeypatch)
    with TestClient(app) as c:
        r = c.get("/")
    assert r.status_code == 200
    assert '<div class="secmap">' in r.text
    # manifest-derived: every category cell renders with its description and
    # every subcategory link inside it
    for cat in nav.CATEGORIES:
        assert f'href="{cat["href"]}"' in r.text
        assert cat["desc"] in r.text
        for it in cat["items"]:
            assert f'href="{it["href"]}"' in r.text, it["label"]
    # hand-pinned: the full route list, including the gated owner pages
    for href in ALL_FEATURE_ROUTES:
        assert f'href="{href}"' in r.text, href
    # the readiness board itself still renders below the map (not replaced)
    assert 'id="live-content"' in r.text


def test_home_keeps_readiness_board_and_shows_console_framing(monkeypatch):
    _offline(monkeypatch)
    with TestClient(app) as c:
        r = c.get("/")
    assert "superbot control plane" in r.text
    # the board table copy survives (the dashboard was ADDED, the board kept)
    assert "signals marked" in r.text


def test_map_covers_every_manifest_href():
    """A page added to the nav manifest cannot silently miss the home map:
    the map renders CATEGORIES directly, so covering the manifest covers the
    map — this pins the manifest against the hand-kept tripwire list."""
    manifest_hrefs = set(nav.all_hrefs())
    assert manifest_hrefs == set(ALL_FEATURE_ROUTES)


def test_header_stays_short():
    """The mobile guard the old more-dropdown provided now comes from the
    hierarchy itself: the header carries ONLY the ~5 categories."""
    assert len(nav.CATEGORIES) <= 6


def test_owner_console_linked_from_footer_on_every_page(monkeypatch):
    _offline(monkeypatch)
    with TestClient(app) as c:
        for path in ("/", "/fleet", "/journal", "/work"):
            r = c.get(path)
            assert r.status_code == 200
            assert 'href="/owner"' in r.text, f"no owner link on {path}"


def test_fleet_lane_cards_deep_link_the_in_app_file_view(monkeypatch):
    _offline(monkeypatch)
    with TestClient(app) as c:
        r = c.get("/fleet")
    assert r.status_code == 200
    # offline → the cached FLEET_LANES fallback set; every lane repo is in
    # the render allow-set, so each card header carries both deep-links
    lane_repo = next(l["repo"] for l in config.FLEET_LANES if l.get("repo"))
    assert f'href="/journal/{lane_repo}/file?path=control/status.md"' in r.text
    assert f'href="/journal/{lane_repo}/file?path=docs/current-state.md"' in r.text


def test_file_view_url_refuses_repos_outside_the_render_allow_set():
    assert fleet._file_view_url("not-a-known-repo", "control/status.md") is None
    known = next(iter(config.JOURNAL_RENDER_REPOS))
    url = fleet._file_view_url(known, "control/status.md")
    assert url == f"/journal/{known}/file?path=control/status.md"
