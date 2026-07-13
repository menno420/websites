"""Offline pins for the clarity-bar pass (control-plane UX, 2026-07-13):
every page opens with a VISIBLE one-line purpose lede (not one collapsed
inside details.pagehelp), /journal/{repo} gets a real header (purpose h2,
lede, jump pills, back-link) instead of a bare repo name, the file renderer
says what it is, and the pages with machine feeds surface their JSON link
in headright the way /activity always has.

Fixture style mirrors tests/test_list_ia.py (offline TestClient,
monkeypatched github layer). Pins are distinctive substrings, not full
sentences, so copyedits don't shatter them.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app import github  # noqa: E402
from app.main import app  # noqa: E402


def _res(ok=True, status=200, data=None, error=""):
    return {"ok": ok, "status": status, "data": data, "error": error,
            "fetched_at": "", "cached": False, "url": ""}


def _offline(monkeypatch):
    async def fake_get(url, refresh=False, raw=False):
        return {"ok": False, "status": 0, "data": None, "error": "offline",
                "fetched_at": "", "cached": False, "url": url}

    monkeypatch.setattr(github, "_get", fake_get)


# --------------------------------------------------------------------------- #
# visible ledes — one line of plain purpose directly under each page's h2
# --------------------------------------------------------------------------- #


def test_activity_lede_is_visible_not_collapsed(monkeypatch):
    _offline(monkeypatch)
    with TestClient(app) as c:
        r = c.get("/activity")
    assert r.status_code == 200
    # the purpose line sits in the flow of the card, not only inside pagehelp
    assert "filter by repo, subscribe by Atom" in r.text


def test_reviews_lede_is_visible_not_collapsed(monkeypatch):
    _offline(monkeypatch)
    with TestClient(app) as c:
        r = c.get("/reviews")
    assert r.status_code == 200
    assert "post-merge second eyes — read-only from fleet-manager" in r.text
    assert "a veto means revert" in r.text


def test_journal_search_lede_states_scope_and_link_targets(monkeypatch):
    _offline(monkeypatch)
    with TestClient(app) as c:
        r = c.get("/journal/search")
    assert r.status_code == 200
    assert "search the journal" in r.text  # h2 unchanged
    assert "hits link to the in-app render" in r.text


def test_orders_h2_uses_plain_words(monkeypatch):
    _offline(monkeypatch)
    with TestClient(app) as c:
        r = c.get("/orders")
    assert r.status_code == 200
    assert "open work on top" in r.text
    assert "cross-referenced with its heartbeat" not in r.text


# --------------------------------------------------------------------------- #
# /journal/{repo} — purpose h2, lede, back-link, jump pills + section ids
# --------------------------------------------------------------------------- #


def test_journal_repo_header_states_purpose_and_links_back(monkeypatch):
    _offline(monkeypatch)
    with TestClient(app) as c:
        r = c.get("/journal/websites")
    assert r.status_code == 200
    # h2 fuses name + purpose; the github span survives
    assert "websites journal — session logs, ledgers, PRs &amp; commits" in r.text
    assert 'href="/journal"' in r.text  # back to the journal browser
    # visible lede; the repo-trivia note is demoted below it, not dropped
    assert "read live from GitHub" in r.text


def test_journal_repo_jump_pills_target_anchored_sections(monkeypatch):
    _offline(monkeypatch)
    with TestClient(app) as c:
        r = c.get("/journal/websites")
    assert r.status_code == 200
    assert "jump to:" in r.text
    for anchor in ("sessions", "docs", "prs", "commits"):
        assert f'href="#{anchor}"' in r.text
        assert f'id="{anchor}"' in r.text


def test_journal_repo_pills_honest_when_repo_has_no_sessions(monkeypatch):
    """substrate-kit has no .sessions/ and no docs by config — its pills
    must not point at anchors that don't render."""
    _offline(monkeypatch)
    with TestClient(app) as c:
        r = c.get("/journal/substrate-kit")
    assert r.status_code == 200
    assert 'href="#sessions"' not in r.text and 'href="#docs"' not in r.text
    assert 'href="#prs"' in r.text and 'href="#commits"' in r.text


# --------------------------------------------------------------------------- #
# /journal/{repo}/file — the renderer says what it is
# --------------------------------------------------------------------------- #


def test_file_page_lede_names_github_as_source_of_truth(monkeypatch):
    async def fake_fetch(repo, path, ref="main", refresh=False):
        return _res(data="# hello\n\nbody\n")

    monkeypatch.setattr(github, "fetch_file", fake_fetch)
    with TestClient(app) as c:
        r = c.get("/journal/websites/file", params={"path": "docs/x.md"})
    assert r.status_code == 200
    assert "rendered read-only from GitHub" in r.text
    assert "source of truth" in r.text
    assert "(main)" in r.text  # the ref is stated


# --------------------------------------------------------------------------- #
# headright machine-feed links + the board tab title
# --------------------------------------------------------------------------- #


def test_headright_surfaces_json_feeds(monkeypatch):
    _offline(monkeypatch)
    feeds = {
        "/fleet": "/fleet.json",
        "/queue": "/queue.json",
        "/projects": "/projects.json",
        "/": "/api/readiness.json",
    }
    with TestClient(app) as c:
        for page, feed in feeds.items():
            r = c.get(page)
            assert r.status_code == 200, page
            assert f'<a href="{feed}">json</a>' in r.text, page


def test_board_tab_title_matches_overview_framing(monkeypatch):
    _offline(monkeypatch)
    with TestClient(app) as c:
        r = c.get("/")
    assert r.status_code == 200
    assert "readiness board</title>" not in r.text
    assert "control plane — overview" in r.text
