"""Offline tests for the IA v2 category structure (owner-directed
2026-07-12): the 2-level hierarchy — ~5 main categories with subcategories —
replaces the flat 12-item console.

Pins: (a) the category nav renders all 5 categories; (b) every feature route
is reachable from its category landing page (each landing's HTML links its
subcategory routes as rows with a primary-action button); (c) every
pre-existing route in the manifest still responds non-404 (reachability over
the manifest, parametrized); (d) / renders the Overview dashboard (attention
summary + category map + the readiness board, not a bare table).
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app import github, nav  # noqa: E402
from app.main import app  # noqa: E402

LANDINGS = [c for c in nav.CATEGORIES if c["landing"]]


def _offline(monkeypatch):
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


# (a) the category nav ---------------------------------------------------- #


def test_category_nav_renders_all_five_categories(monkeypatch):
    _offline(monkeypatch)
    with TestClient(app) as c:
        r = c.get("/")
    assert r.status_code == 200
    assert [cat["key"] for cat in nav.CATEGORIES] == [
        "overview", "work", "history", "console", "owner",
    ]
    nav_html = r.text.split("<nav>", 1)[1].split("</nav>", 1)[0]
    for cat in nav.CATEGORIES:
        assert f'href="{cat["href"]}"' in nav_html, cat["key"]


def test_category_grouping_matches_the_brief():
    """The first-cut grouping the owner reacts to — a re-group is a data
    edit in app/nav.py and a conscious update here."""
    by_key = {c["key"]: [i["href"] for i in c["items"]] for c in nav.CATEGORIES}
    assert by_key["overview"] == ["/", "/fleet", "/freshness"]
    assert by_key["work"] == ["/queue", "/orders", "/ideas", "/reviews"]
    assert by_key["history"] == ["/activity", "/journal"]
    assert by_key["console"] == [
        "/projects", "/prompts", "/owner/environments-hub", "/directory",
    ]
    assert by_key["owner"][0] == "/owner"


# (b) landing pages link their subcategories as rows ----------------------- #


@pytest.mark.parametrize("cat", LANDINGS, ids=lambda c: c["key"])
def test_landing_page_links_every_subcategory(monkeypatch, cat):
    _offline(monkeypatch)
    with TestClient(app) as c:
        r = c.get(cat["href"])
    assert r.status_code == 200
    for it in cat["items"]:
        assert f'href="{it["href"]}"' in r.text, it["label"]
        assert it["desc"].split("—")[0].strip()[:40] in r.text or it["desc"] in r.text
        # the primary action renders as the row's right-aligned button
        assert f'class="btn" href="{it["action"]["href"]}"' in r.text
    # rows markup: one .catrow per item
    assert r.text.count('class="catrow"') == len(cat["items"])


def test_landing_pages_degrade_honestly_offline(monkeypatch):
    """Offline, counts either compute from honest empty overviews (0) or
    show the honest — placeholder; the page never 500s and never invents."""
    _offline(monkeypatch)
    with TestClient(app) as c:
        for cat in LANDINGS:
            r = c.get(cat["href"])
            assert r.status_code == 200


# (c) every manifest route still responds non-404 -------------------------- #


@pytest.mark.parametrize("href", nav.all_hrefs())
def test_every_manifest_route_responds(monkeypatch, href):
    """Reachability over the whole manifest: no dead links in the IA. Gated
    owner pages answer their gate (401/503 without credentials), never 404;
    public pages answer 200."""
    _offline(monkeypatch)
    with TestClient(app) as c:
        r = c.get(href)
    assert r.status_code != 404, href
    if not href.startswith("/owner"):
        assert r.status_code == 200, href


# (d) / renders the Overview dashboard ------------------------------------- #


def test_home_renders_the_overview_dashboard(monkeypatch):
    _offline(monkeypatch)
    with TestClient(app) as c:
        r = c.get("/")
    assert r.status_code == 200
    assert 'id="overview-dashboard"' in r.text
    # the what-needs-attention summary strip renders (honest all-quiet
    # offline: no broken checks / drift / stale heartbeats are fetchable)
    assert 'class="attn"' in r.text
    assert ("all quiet" in r.text) or ("needs attention:" in r.text)
    # the category → subcategory map: every category cell with its items
    assert '<div class="secmap">' in r.text
    for cat in nav.CATEGORIES:
        assert f'href="{cat["href"]}"' in r.text
        for it in cat["items"]:
            assert f'href="{it["href"]}"' in r.text, it["label"]
    # the live readiness board still renders below (added-to, not replaced)
    assert 'id="live-content"' in r.text


def test_home_attention_strip_flags_definite_bads(monkeypatch):
    """A broken check / deploy drift / stale heartbeat surfaces in the
    attention strip — derived from the same rows the board renders."""
    from app.main import _attention

    rows = [
        {"repo": "superbot", "broken_runs": [{"name": "quality"}],
         "deploy_state": {"any_drift": True}},
        {"repo": "websites", "broken_runs": [], "deploy_state": {}},
    ]
    chips = {"websites": {"stale": True, "age_human": "26h"}}
    items = _attention(rows, chips)
    texts = [i["text"] for i in items]
    assert "superbot: 1 broken check(s)" in texts
    assert "superbot: deploy DRIFT" in texts
    assert "websites: heartbeat stale (26h)" in texts
    assert all(i["state"] in ("bad", "warn") for i in items)
    assert _attention([], {}) == []
