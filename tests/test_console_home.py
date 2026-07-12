"""Offline unit tests for the console-home discoverability finish: the home
page opens with a section map linking EVERY feature page (the long tail the
short header nav deliberately does not carry), the gated owner console is
findable from the footer of every page, and the /fleet lane cards deep-link
each lane's files through the in-app /journal/{repo}/file renderer.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app import config, fleet, github, nav  # noqa: E402
from app.main import app  # noqa: E402

# Every feature page the console serves, pinned by hand ON PURPOSE: if a
# route is removed or the section map loses a card, this list is the
# tripwire (the manifest-derived loop below can't catch a page that falls
# out of the manifest itself).
ALL_FEATURE_ROUTES = [
    "/",
    "/fleet",
    "/queue",
    "/activity",
    "/journal",
    "/environments",
    "/projects",
    "/prompts",
    "/reviews",
    "/orders",
    "/ideas",
    "/directory",
    "/owner",
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


def test_home_section_map_links_every_feature_page(monkeypatch):
    _offline(monkeypatch)
    with TestClient(app) as c:
        r = c.get("/")
    assert r.status_code == 200
    assert '<div class="secmap">' in r.text
    # manifest-derived: every section-map card renders with its description
    for item in nav.section_map():
        assert f'href="{item["href"]}"' in r.text
        assert item["desc"] in r.text
    # hand-pinned: the full route list, including the gated owner console
    for href in ALL_FEATURE_ROUTES:
        assert f'href="{href}"' in r.text
    # the readiness board itself still renders below the map (not replaced)
    assert 'id="live-content"' in r.text


def test_home_keeps_readiness_board_and_shows_console_framing(monkeypatch):
    _offline(monkeypatch)
    with TestClient(app) as c:
        r = c.get("/")
    assert "superbot control plane" in r.text
    # the board table copy survives (the map was ADDED, the board kept)
    assert "signals marked" in r.text


def test_section_map_covers_every_nav_key():
    """A page added to the nav manifest cannot silently miss the home map."""
    assert set(nav.DESCRIPTIONS) == nav.keys()
    hrefs = [s["href"] for s in nav.section_map()]
    assert hrefs == [i["href"] for i in nav.PRIMARY + nav.GROUPED] + ["/owner"]
    assert sorted(hrefs) == sorted(ALL_FEATURE_ROUTES)


def test_projects_and_orders_are_primary_nav():
    """The console-home PR promoted the dispatch + orders surfaces out of
    the more ▾ dropdown; the header stays ~7 items (mobile overflow guard)."""
    primary_hrefs = [i["href"] for i in nav.PRIMARY]
    assert "/projects" in primary_hrefs
    assert "/orders" in primary_hrefs
    assert len(nav.PRIMARY) <= 7


def test_owner_console_linked_from_footer_on_every_page(monkeypatch):
    _offline(monkeypatch)
    with TestClient(app) as c:
        for path in ("/", "/fleet", "/journal"):
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
