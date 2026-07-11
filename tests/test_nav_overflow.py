"""Offline unit tests for the nav overflow guard: secondary pages live under
a no-JS <details> "more" dropdown; every page stays reachable; a grouped
page's active state opens the group and highlights the summary.
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


# Sourced from the SAME manifest the template renders (app/nav.py) — these
# used to be hand-kept tuples that could silently drift from the markup.
GROUPED = tuple(item["href"] for item in nav.GROUPED)
PRIMARY = tuple(item["href"] for item in nav.PRIMARY)


def test_nav_groups_secondary_pages_and_keeps_all_reachable(monkeypatch):
    _offline(monkeypatch)
    with TestClient(app) as c:
        r = c.get("/fleet")
    assert r.status_code == 200
    assert '<details class="navmore"' in r.text
    assert ">more ▾</summary>" in r.text
    # every grouped page keeps its link (inside the panel)
    for href in GROUPED:
        assert f'href="{href}"' in r.text
    # primary links stay top-level (present) too
    for href in PRIMARY:
        assert f'href="{href}"' in r.text
    # a non-grouped page leaves the dropdown CLOSED
    assert '<details class="navmore" open' not in r.text


def test_grouped_page_opens_dropdown_and_highlights_summary(monkeypatch):
    _offline(monkeypatch)
    with TestClient(app) as c:
        r = c.get("/orders")
    assert r.status_code == 200
    assert '<details class="navmore" open' in r.text
    assert 'summary class="on"' in r.text  # the group shows as active
