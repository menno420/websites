"""Offline tests for the IA v2 slice-2 row/button consistency pass
(owner feedback 2026-07-12: "clear rows and better placed buttons").

Pins the ONE idiom across the feature pages: every list row / item card
carries its primary action as a right-aligned ``class="btn"`` button (the
same .btn/.cr-action system the PR-#204 category landings introduced), with
a consistent "open <thing>" verb — internal navigation gets →, external
GitHub/site links get ↗. Secondary actions stay small links.

Fixture style mirrors tests/test_list_ia.py (offline TestClient,
monkeypatched github layer, frozen clock where ages matter).
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app import clock, config, github  # noqa: E402
from app.main import app  # noqa: E402

NOW = datetime(2026, 7, 10, 12, 0, 0, tzinfo=timezone.utc)


def _res(ok=True, status=200, data=None, error=""):
    return {"ok": ok, "status": status, "data": data, "error": error,
            "fetched_at": "", "cached": False, "url": ""}


def _offline(monkeypatch):
    async def fake_get(url, refresh=False, raw=False, follow_redirects=False):
        return {"ok": False, "status": 0, "data": None, "error": "offline",
                "fetched_at": "", "cached": False, "url": url}

    async def fake_fetch(repo, path, ref="main", refresh=False):
        return _res(ok=False, status=404, data=None, error="nf")

    async def fake_api(repo, subpath="", refresh=False):
        return _res(ok=False, status=404, data=None, error="nf")

    monkeypatch.setattr(github, "_get", fake_get)
    monkeypatch.setattr(github, "fetch_file", fake_fetch)
    monkeypatch.setattr(github, "repo_api", fake_api)


# --------------------------------------------------------------------------- #
# /queue — each ask card's title row carries "open source ↗"
# --------------------------------------------------------------------------- #

_Q_STATUS = (
    "# websites · status\n"
    "updated: 2026-07-10T02:00Z\n"
    "health: green (ok)\n"
    "⚑ needs-owner: decide the thing\n"
    "notes: n\n"
)


def test_queue_ask_rows_carry_open_source_button(monkeypatch):
    monkeypatch.setattr(clock, "NOW_OVERRIDE", NOW)

    async def fake_fetch(repo, path, ref="main", refresh=False):
        if repo == "websites" and path == "control/status.md":
            return _res(data=_Q_STATUS)
        return _res(ok=False, status=404, data=None, error="nf")

    async def fake_api(repo, subpath="", refresh=False):
        return _res(ok=False, status=404, data=None, error="nf")

    monkeypatch.setattr(github, "fetch_file", fake_fetch)
    monkeypatch.setattr(github, "repo_api", fake_api)
    with TestClient(app) as c:
        r = c.get("/queue")
    assert r.status_code == 200
    assert "decide the thing" in r.text
    assert ">open source ↗</a>" in r.text
    assert 'class="btn"' in r.text


# --------------------------------------------------------------------------- #
# /orders — the repo card header carries "open inbox ↗" to the inbox file
# --------------------------------------------------------------------------- #

_O_INBOX = """# websites · inbox

## ORDER 001 · 2026-07-09T12:07Z · status: new
priority: P1
do: Build the thing.
"""


def test_orders_repo_row_carries_open_inbox_button(monkeypatch):
    monkeypatch.setattr(clock, "NOW_OVERRIDE", NOW)

    async def fake_fetch(repo, path, ref="main", refresh=False):
        if path == "control/inbox.md" and repo == "websites":
            return _res(data=_O_INBOX)
        return _res(ok=False, status=404, data=None, error="nf")

    monkeypatch.setattr(github, "fetch_file", fake_fetch)
    with TestClient(app) as c:
        r = c.get("/orders")
    assert r.status_code == 200
    assert ">open inbox ↗</a>" in r.text
    # the button deep-links the repo's committed inbox file
    assert "/websites/blob/main/control/inbox.md" in r.text


# --------------------------------------------------------------------------- #
# /ideas — every idea renders as a .catrow with "open idea →" + GitHub link
# --------------------------------------------------------------------------- #

_IDEA_FILES = [
    {"type": "file", "name": "idea-a.md", "path": "docs/ideas/idea-a.md",
     "html_url": ""},
]
_IDEA_CONTENT = {
    "docs/ideas/idea-a.md": "---\nstate: captured\n---\n\n# A\n\none a\n",
}


def test_idea_rows_are_catrows_with_open_idea_button(monkeypatch):
    async def fake_api(repo, subpath="", refresh=False):
        if subpath.endswith("/contents/docs/ideas") and repo == "websites":
            return _res(data=_IDEA_FILES)
        return _res(ok=False, status=404, data=None, error="nf")

    async def fake_fetch(repo, path, ref="main", refresh=False):
        if path in _IDEA_CONTENT:
            return _res(data=_IDEA_CONTENT[path])
        return _res(ok=False, status=404, data=None, error="nf")

    monkeypatch.setattr(github, "repo_api", fake_api)
    monkeypatch.setattr(github, "fetch_file", fake_fetch)
    with TestClient(app) as c:
        r = c.get("/ideas")
    assert r.status_code == 200
    assert 'class="catrow"' in r.text
    assert ">open idea →</a>" in r.text
    # GitHub deep-link demoted to the small secondary link on the row
    assert ">GitHub ↗</a>" in r.text


# --------------------------------------------------------------------------- #
# /reviews — each open review card carries "open PR ↗"
# --------------------------------------------------------------------------- #

_REVIEW_LEDGER = """# Review queue

| PR | What to re-check | Why-risky | Drain path · status |
|---|---|---|---|
| superbot#1920 | The checker semantics change | Enforcement surface | codex · **open** |
"""


def test_open_review_rows_carry_open_pr_button(monkeypatch):
    monkeypatch.setattr(config, "GITHUB_TOKEN", "tok")

    async def fake_fetch(repo, path, ref="main", refresh=False):
        return _res(data=_REVIEW_LEDGER)

    monkeypatch.setattr(github, "fetch_file", fake_fetch)
    with TestClient(app) as c:
        r = c.get("/reviews")
    assert r.status_code == 200
    assert ">open PR ↗</a>" in r.text


# --------------------------------------------------------------------------- #
# /journal — one row per repo, "open journal →" right-aligned
# --------------------------------------------------------------------------- #


def test_journal_repo_rows_carry_open_journal_button(monkeypatch):
    _offline(monkeypatch)
    with TestClient(app) as c:
        r = c.get("/journal")
    assert r.status_code == 200
    for repo in config.REPOS:
        assert f'class="btn" href="/journal/{repo}"' in r.text
    assert r.text.count(">open journal →</a>") == len(config.REPOS)


# --------------------------------------------------------------------------- #
# /projects — each seat card's header row carries "open dispatch →"
# --------------------------------------------------------------------------- #

_P_ROOT = [{"type": "dir", "name": "websites", "path": "projects/websites"}]


def test_seat_cards_carry_open_dispatch_button(monkeypatch):
    async def fake_api(repo, subpath="", refresh=False):
        if subpath.endswith("/contents/projects"):
            return _res(data=_P_ROOT)
        if subpath.endswith("/contents/projects/websites"):
            return _res(data=[{"type": "file",
                               "path": "projects/websites/meta.md"}])
        return _res(ok=False, status=404, data=None, error="nf")

    async def fake_fetch(repo, path, ref="main", refresh=False):
        if path == "projects/websites/meta.md":
            return _res(data="deployed: live\n")
        return _res(ok=False, status=404, data=None, error="nf")

    monkeypatch.setattr(github, "repo_api", fake_api)
    monkeypatch.setattr(github, "fetch_file", fake_fetch)
    with TestClient(app) as c:
        r = c.get("/projects")
    assert r.status_code == 200
    assert 'class="btn" href="/projects/websites"' in r.text
    assert ">open dispatch →</a>" in r.text


# --------------------------------------------------------------------------- #
# /fleet — every lane card header carries "open status", even offline
# --------------------------------------------------------------------------- #


def test_fleet_lane_rows_carry_open_status_button(monkeypatch):
    _offline(monkeypatch)
    with TestClient(app) as c:
        r = c.get("/fleet")
    assert r.status_code == 200
    # one primary-action button per lane header (offline: fallback lane set
    # still renders every lane card, fetch errors and all)
    assert "open status" in r.text
    assert r.text.count('<span class="cr-action">') >= 1


# --------------------------------------------------------------------------- #
# /directory — a recorded URL renders as the row's button, never a dead one
# --------------------------------------------------------------------------- #


def test_directory_url_rows_render_button_urlless_rows_do_not(monkeypatch):
    _offline(monkeypatch)
    with TestClient(app) as c:
        r = c.get("/directory")
    assert r.status_code == 200
    # committed registry rows with a URL get a .btn link to that URL
    assert 'class="btn" href="https://' in r.text
    # URL-less rows keep their honest dash — no dead buttons invented
    assert "no URL recorded" in r.text
