"""Bot-site smoke tests. Network-free: the site data feed is primed from a fixture
so tests never depend on raw.githubusercontent.com."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from botsite import app as app_module
from botsite import data_source as ds

FIXTURE = {
    "meta": {"build": {"commit": "abcdef1234", "subject": "test build", "committed_at": "2026-07-09T00:00:00Z"}},
    "counts": {"commands": 2, "features": 2, "games": 1},
    "catalogue": [
        {
            "key": "economy",
            "display_name": "Economy",
            "description": "Coins, shop, and daily rewards.",
            "emoji": "💰",
            "category": "economy",
            "tags": ["coins", "shop"],
            "badges": ["economy"],
            "is_game": False,
        },
        {
            "key": "blackjack",
            "display_name": "Blackjack",
            "description": "Play blackjack in chat.",
            "emoji": "🃏",
            "category": "games",
            "tags": ["cards"],
            "badges": ["games"],
            "is_game": True,
        },
    ],
    "commands": [
        {"name": "daily", "aliases": ["d"], "category": "economy", "permissions": "user",
         "usage": "Claim your daily coins.", "description": "Daily reward.", "examples": ["!daily", "!daily claim"],
         "status": "finished",
         "linked_ideas": [{"title": "Daily streak bonus idea", "status": "ideas"}]},
        {"name": "blackjack", "aliases": [], "category": "games", "permissions": "user",
         "usage": "Play blackjack.", "description": "Blackjack game.", "examples": ["!blackjack"],
         "status": "in-progress", "linked_ideas": []},
        # A name with a URL-reserved char, mirroring superbot's real ``+prize`` command.
        {"name": "+prize", "aliases": [], "category": "economy", "permissions": "moderator",
         "usage": "Grant a prize.", "description": "Grant a prize to a member.", "examples": [],
         "status": "finished", "linked_ideas": []},
    ],
    "bot_changelog": [
        {"date": "2026-06-19", "title": "New site", "kind": "improvement", "summary": "A new public site."},
        {"date": "2026-06-08", "title": "Alias suggestions", "kind": "feature", "summary": "Suggest an alias."},
    ],
}


@pytest.fixture()
def client():
    ds.clear_cache()
    ds.prime_cache(FIXTURE)
    ds.set_client(ds.make_client())  # never actually hit (cache is warm)
    with TestClient(app_module.app) as c:
        yield c
    ds.clear_cache()


def test_healthz(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_version_returns_env_sha(client, monkeypatch):
    """/version reports the deployed SHA from RAILWAY_GIT_COMMIT_SHA (primary)."""
    monkeypatch.setenv("RAILWAY_GIT_COMMIT_SHA", "deadbeef1234567890")
    r = client.get("/version")
    assert r.status_code == 200
    body = r.json()
    assert body == {"service": "botsite", "sha": "deadbeef1234567890", "short": "deadbeef"}


def test_favicon_ico_serves_site_icon(client):
    """/favicon.ico answers the browser's own probe (raw JSON views carry no
    <link rel="icon"> — the PR #321 fleet-wide 404 finding) with the same SVG
    the HTML pages declare."""
    r = client.get("/favicon.ico")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("image/svg+xml")
    assert b"<svg" in r.content


def test_version_falls_back_to_git_sha(client, monkeypatch):
    """GIT_SHA (baked at Docker build) is the fallback when Railway's var is absent."""
    monkeypatch.delenv("RAILWAY_GIT_COMMIT_SHA", raising=False)
    monkeypatch.setenv("GIT_SHA", "cafebabecafebabe")
    body = client.get("/version").json()
    assert body["sha"] == "cafebabecafebabe" and body["short"] == "cafebabe"


def test_version_unknown_when_unset(client, monkeypatch):
    """Neither env var set → honest 'unknown', never a crash or a faked value."""
    monkeypatch.delenv("RAILWAY_GIT_COMMIT_SHA", raising=False)
    monkeypatch.delenv("GIT_SHA", raising=False)
    body = client.get("/version").json()
    assert body == {"service": "botsite", "sha": "unknown", "short": "unknown"}


@pytest.mark.parametrize("path", ["/", "/features", "/commands", "/games", "/changelog", "/status", "/design", "/submit"])
def test_pages_render(client, path):
    r = client.get(path)
    assert r.status_code == 200
    assert "SuperBot" in r.text
    # data-driven content shows through
    assert "site.json" in r.text or "SuperBot" in r.text


def test_home_shows_real_counts(client):
    r = client.get("/")
    assert ">2<" in r.text  # commands/features count from the fixture
    assert "Add to Discord" in r.text


def test_commands_lists_real_commands(client):
    r = client.get("/commands")
    assert "!daily" in r.text
    assert "!blackjack" in r.text


def test_commands_rows_link_to_detail(client):
    r = client.get("/commands")
    assert 'href="/commands/daily"' in r.text
    # URL-reserved names are percent-encoded in the link
    assert 'href="/commands/%2Bprize"' in r.text


def test_command_detail_renders_real_fields(client):
    r = client.get("/commands/daily")
    assert r.status_code == 200
    assert "!daily" in r.text  # invocation signature
    assert "Daily reward." in r.text  # real description
    assert "!daily claim" in r.text  # real example
    assert "!d" in r.text  # real alias
    assert "Economy" in r.text  # category label
    assert "Daily streak bonus idea" in r.text  # linked idea surfaced


def test_command_detail_states_discord_context(client):
    """Clarity: the page says up front these are Discord chat commands."""
    r = client.get("/commands/daily")
    assert r.status_code == 200
    assert "A SuperBot chat command" in r.text
    assert "default prefix" in r.text
    assert "Daily reward." in r.text  # the per-command description stays


def test_command_detail_url_safe_name(client):
    # ``+prize`` must resolve via its percent-encoded path
    r = client.get("/commands/%2Bprize")
    assert r.status_code == 200
    assert "Grant a prize" in r.text


def test_command_detail_unknown_404(client):
    r = client.get("/commands/does-not-exist")
    assert r.status_code == 404
    assert "not found" in r.text.lower()
    assert "does-not-exist" in r.text


def test_not_found_page_has_real_h1(client):
    """Clarity: the 404 page carries an h1-level heading, not just a card h4."""
    r = client.get("/commands/does-not-exist")
    assert r.status_code == 404
    assert ">Page not found</h1>" in r.text
    assert "Back home" in r.text  # the escape hatch stays


def test_command_detail_omits_absent_fields(client):
    # blackjack has no aliases and no linked ideas — those sections must not appear
    r = client.get("/commands/blackjack")
    assert r.status_code == 200
    assert "Related ideas" not in r.text
    assert "Aliases" not in r.text


def test_changelog_enriched(client):
    r = client.get("/changelog")
    assert r.status_code == 200
    # real build context panel (from meta.build + counts)
    assert "Latest build" in r.text
    assert "abcdef12" in r.text  # short commit
    # grouped-by-kind sections render real entries
    assert "New site" in r.text
    assert "Alias suggestions" in r.text
    # honest sourcing note, no invented version history
    assert "bot_changelog" in r.text


def test_changelog_degrades_when_feed_unavailable():
    """No fake data: the changelog shows the honest banner when the feed is down."""
    ds.clear_cache()

    class _Boom:
        async def get(self, *a, **k):
            raise RuntimeError("network down")

        async def aclose(self):
            pass

    ds.set_client(_Boom())  # type: ignore[arg-type]
    with TestClient(app_module.app) as c:
        r = c.get("/changelog")
        assert r.status_code == 200
        assert "temporarily unavailable" in r.text.lower()
    ds.clear_cache()


def test_feature_detail_ok_and_404(client):
    assert client.get("/features/economy").status_code == 200
    r = client.get("/features/nope-nope")
    assert r.status_code == 404
    assert "not found" in r.text.lower()


def test_feature_detail_framing_lede(client):
    """Clarity: /features/{key} frames itself as one of SuperBot's feature areas,
    with the real command count, while the fragment descriptor stays."""
    r = client.get("/features/economy")
    assert r.status_code == 200
    assert "One of SuperBot's 2 feature areas" in r.text  # counts.features
    assert "the 2 commands it ships" in r.text  # daily + +prize
    assert "Coins, shop, and daily rewards." in r.text  # existing descriptor stays


def test_games_only_games(client):
    r = client.get("/games")
    assert "Blackjack" in r.text


def test_submit_stub_is_honest(client, monkeypatch):
    # With no DATABASE_URL the intake is not live: the guarded POST (same-origin)
    # must honestly report that nothing was stored.
    monkeypatch.delenv("DATABASE_URL", raising=False)
    r = client.post("/submit", headers={"Origin": "http://testserver"})
    assert r.status_code == 200
    assert "not live yet" in r.text.lower() or "not yet provisioned" in r.text.lower()


def test_palette_index(client):
    r = client.get("/palette.json")
    assert r.status_code == 200
    labels = [i.get("label") for i in r.json()]
    assert "Home" in labels


def test_degrades_when_feed_unavailable():
    """No fake data: a failed feed shows the honest error banner, still 200."""
    ds.clear_cache()

    class _Boom:
        async def get(self, *a, **k):
            raise RuntimeError("network down")

        async def aclose(self):
            pass

    ds.set_client(_Boom())  # type: ignore[arg-type]
    with TestClient(app_module.app) as c:
        # lifespan warm-fetch fails silently; page still renders the honest banner
        r = c.get("/")
        assert r.status_code == 200
        assert "temporarily unavailable" in r.text.lower()
    ds.clear_cache()
