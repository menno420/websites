"""Offline unit tests for the ?repo= filter on the activity views
(/activity, /activity.json, /activity.xml): single-repo narrowing (fewer
fetches, per-lane Atom subscription with the repo named in the feed title)
and the honest unknown-repo empty state — never a guess, never a 500.
"""

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app import activity, config, github  # noqa: E402
from app.main import app  # noqa: E402


def _pr(repo, num, title):
    return {
        "number": num,
        "title": title,
        "state": "closed",
        "merged_at": f"2026-07-10T1{num % 10}:00:00Z",
        "updated_at": None,
        "created_at": None,
        "draft": False,
        "user": {"login": "menno420"},
        "html_url": f"https://github.com/menno420/{repo}/pull/{num}",
    }


def _mock(monkeypatch, calls):
    async def fake_api(repo, subpath="", refresh=False):
        calls.append(repo)
        if subpath.startswith("/pulls"):
            return {"ok": True, "status": 200,
                    "data": [_pr(repo, 1, f"{repo} change")],
                    "error": "", "fetched_at": "", "cached": False, "url": ""}
        return {"ok": False, "status": 404, "data": None, "error": "nf",
                "fetched_at": "", "cached": False, "url": ""}

    monkeypatch.setattr(github, "repo_api", fake_api)


def test_timeline_filtered_fetches_one_repo_only(monkeypatch):
    calls: list = []
    _mock(monkeypatch, calls)
    import asyncio

    out = asyncio.run(activity.timeline(repo="websites"))
    assert calls == ["websites"]  # fewer fetches, not a post-filter
    assert out["repo_filter"] == "websites" and out["unknown_repo"] is False
    assert all(i["repo"] == "websites" for i in out["items"])
    assert out["known_repos"] == list(config.REPOS)


def test_timeline_unknown_repo_is_honest_empty(monkeypatch):
    calls: list = []
    _mock(monkeypatch, calls)
    import asyncio

    out = asyncio.run(activity.timeline(repo="not-a-fleet-repo"))
    assert calls == []  # nothing fetched for a repo we don't know
    assert out["unknown_repo"] is True and out["items"] == []
    assert out["repo_filter"] == "not-a-fleet-repo"


def test_timeline_unfiltered_keeps_full_fleet_and_new_keys(monkeypatch):
    calls: list = []
    _mock(monkeypatch, calls)
    import asyncio

    out = asyncio.run(activity.timeline())
    assert sorted(calls) == sorted(config.REPOS)
    assert out["repo_filter"] is None and out["unknown_repo"] is False


def test_activity_page_filter_links_and_banner(monkeypatch):
    _mock(monkeypatch, [])
    client = TestClient(app)

    r = client.get("/activity?repo=websites")
    assert r.status_code == 200
    assert "cross-repo activity — websites" in r.text
    assert "/activity.xml?repo=websites" in r.text  # per-lane subscribe link
    assert 'href="/activity"' in r.text  # all-repos escape hatch

    r = client.get("/activity?repo=nope")
    assert r.status_code == 200
    assert "unknown repo" in r.text and "nope" in r.text


def test_activity_json_carries_filter_keys(monkeypatch):
    _mock(monkeypatch, [])
    client = TestClient(app)
    d = client.get("/activity.json?repo=websites").json()
    assert d["repo_filter"] == "websites"
    assert all(i["repo"] == "websites" for i in d["items"])


def test_activity_xml_filtered_feed_names_the_repo(monkeypatch):
    _mock(monkeypatch, [])
    client = TestClient(app)
    r = client.get("/activity.xml?repo=websites")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/atom+xml")
    root = ET.fromstring(r.content)
    ns = {"a": activity.ATOM_NS}
    title = root.find("a:title", ns).text
    assert title == f"{activity.FEED_TITLE} — websites"
    self_href = root.find("a:link[@rel='self']", ns).get("href")
    assert self_href.endswith("/activity.xml?repo=websites")
    for entry_title in root.findall("a:entry/a:title", ns):
        assert entry_title.text.startswith("websites #")

    # unfiltered feed keeps the plain fleet title (no accidental suffix)
    r = client.get("/activity.xml")
    root = ET.fromstring(r.content)
    assert root.find("a:title", ns).text == activity.FEED_TITLE
