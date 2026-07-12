"""Offline unit tests for the category header nav (IA v2): the header shows
the ~5 MAIN CATEGORIES (not the old flat 12-item list), the current page's
CATEGORY highlights, and the no-JS server-rendered markup carries every
category link on every page.

(This file kept its historical name from the pre-IA "more ▾" overflow guard
it replaces — the guard's job, keeping the header short as pages accrue, is
now done by the 2-level category hierarchy itself.)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app import github, nav  # noqa: E402
from app.main import app  # noqa: E402


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


def test_header_nav_is_the_five_categories(monkeypatch):
    _offline(monkeypatch)
    with TestClient(app) as c:
        r = c.get("/fleet")
    assert r.status_code == 200
    assert len(nav.CATEGORIES) == 5  # overview · work · history · console · owner
    nav_html = r.text.split("<nav>", 1)[1].split("</nav>", 1)[0]
    for cat in nav.CATEGORIES:
        assert f'href="{cat["href"]}"' in nav_html, cat["key"]
    # the flat long tail is OUT of the header (categories carry it):
    # feature pages appear via their category landing, not as top-level links
    for href in ("/queue", "/orders", "/ideas", "/prompts", "/directory"):
        assert f'href="{href}"' not in nav_html, href
    # the pre-IA dropdown is gone
    assert "navmore" not in r.text
    assert "more ▾" not in r.text


def test_current_category_highlights(monkeypatch):
    _offline(monkeypatch)
    with TestClient(app) as c:
        # /fleet is an Overview item → the overview category link highlights
        r = c.get("/fleet")
        assert r.status_code == 200
        assert 'href="/" class="on"' in r.text
        assert 'href="/work" class="on"' not in r.text
        # /ideas is a Work item → the work category link highlights
        r = c.get("/ideas")
        assert r.status_code == 200
        assert 'href="/work" class="on"' in r.text
        assert 'href="/" class="on"' not in r.text
        # a landing page highlights its own category
        r = c.get("/console")
        assert r.status_code == 200
        assert 'href="/console" class="on"' in r.text
