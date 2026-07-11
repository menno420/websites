"""Offline unit tests for the board-row conveyor chips: idea-lifecycle
counts render on the readiness board's repo rows (the owner's habit path),
reusing the /ideas fetch path; repos without a readable ideas dir show no
chip (the board stays a readiness surface — /ideas holds the honest
absence/error); /api/readiness.json is untouched.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app import github  # noqa: E402
from app.main import app  # noqa: E402

_FILES = [
    {"type": "file", "name": "idea-a.md", "path": "docs/ideas/idea-a.md",
     "html_url": ""},
    {"type": "file", "name": "idea-b.md", "path": "docs/ideas/idea-b.md",
     "html_url": ""},
]
_CONTENT = {
    "docs/ideas/idea-a.md": "---\nstate: captured\n---\n\n# A\n\none a\n",
    "docs/ideas/idea-b.md": "---\nstate: built\n---\n\n# B\n\none b\n",
}


def _res(ok=True, status=200, data=None, error=""):
    return {"ok": ok, "status": status, "data": data, "error": error,
            "fetched_at": "", "cached": False, "url": ""}


def _mock(monkeypatch):
    # Lowest-level fetch degrades offline (the test_app client-fixture
    # pattern) so readiness' direct github._get calls never hit the network;
    # the ideas path is mocked above it with real-looking data.
    async def fake_get(url, refresh=False, raw=False):
        return {"ok": False, "status": 0, "data": None,
                "error": "offline test", "fetched_at": "", "cached": False,
                "url": url}

    monkeypatch.setattr(github, "_get", fake_get)

    async def fake_api(repo, subpath="", refresh=False):
        if subpath.endswith("/contents/docs/ideas") and repo == "websites":
            return _res(data=_FILES)
        return _res(ok=False, status=404, data=None, error="nf")

    async def fake_fetch(repo, path, ref="main", refresh=False):
        if path in _CONTENT:
            return _res(data=_CONTENT[path])
        return _res(ok=False, status=404, data=None, error="nf")

    monkeypatch.setattr(github, "repo_api", fake_api)
    monkeypatch.setattr(github, "fetch_file", fake_fetch)


def test_board_renders_conveyor_chips_for_repo_with_ideas(monkeypatch):
    _mock(monkeypatch)
    with TestClient(app) as c:
        r = c.get("/")
    assert r.status_code == 200
    assert "ideas conveyor:" in r.text
    assert "1 captured" in r.text and "1 built" in r.text
    assert 'href="/ideas?state=built"' in r.text  # chip deep-links the filter
    # exactly ONE repo (websites) has ideas in this mock -> one chip line
    assert r.text.count("ideas conveyor:") == 1


def test_board_no_chip_when_ideas_unreadable(monkeypatch):
    async def all_fail(repo, subpath="", refresh=False):
        return _res(ok=False, status=503, data=None, error="offline")

    async def fetch_fail(repo, path, ref="main", refresh=False):
        return _res(ok=False, status=503, data=None, error="offline")

    async def fake_get(url, refresh=False, raw=False):
        return {"ok": False, "status": 0, "data": None,
                "error": "offline test", "fetched_at": "", "cached": False,
                "url": url}

    monkeypatch.setattr(github, "_get", fake_get)
    monkeypatch.setattr(github, "repo_api", all_fail)
    monkeypatch.setattr(github, "fetch_file", fetch_fail)
    with TestClient(app) as c:
        r = c.get("/")
    assert r.status_code == 200  # board itself never 500s on ideas trouble
    assert "ideas conveyor:" not in r.text  # no chip, no invented counts


def test_readiness_json_untouched_by_chips(monkeypatch):
    """The chips are an HTML-page nicety — /api/readiness.json keeps its
    shape (no ideas keys injected into the consumed payload)."""
    _mock(monkeypatch)
    with TestClient(app) as c:
        d = c.get("/api/readiness.json").json()
    assert isinstance(d, list) and d
    for row in d:
        assert "idea_chips" not in row and "state_counts" not in row
