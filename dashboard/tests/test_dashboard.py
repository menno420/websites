"""Dashboard smoke tests. Network-free: the data feeds are primed from fixtures so
tests never depend on raw.githubusercontent.com. Auth is exercised end-to-end (the
Basic-auth gate is the whole reason this surface is private)."""

from __future__ import annotations

import base64
import os

import pytest
from fastapi.testclient import TestClient

# The auth gate reads SITE_PASSWORD at request time via config; set it before import.
os.environ["SITE_PASSWORD"] = "test-secret"

from dashboard import app as app_module  # noqa: E402
from dashboard import config  # noqa: E402
from dashboard import data_source as ds  # noqa: E402

AUTH = {"Authorization": "Basic " + base64.b64encode(b"any:test-secret").decode()}

DASHBOARD_FIXTURE = {
    "meta": {
        "generated_at": "2026-07-09T00:00:00Z",
        "build": {"commit": "abcdef1234", "subject": "test build", "committed_at": "2026-07-09T00:00:00Z"},
        "counts": {
            "functions": 2, "commands": 3, "setting_keys": 2, "setting_domains": 1,
            "env_vars": 1, "ideas": 1, "bugs": 1, "updates": 1, "synonyms": 1,
            "visible_subsystems": 2, "cogs": 1,
        },
    },
    "catalogue": [
        {"key": "economy", "display_name": "Economy", "description": "Coins & shop.", "emoji": "💰",
         "visibility_tier": "user", "visibility_mode": "normal", "category": "economy",
         "tags": ["coins"], "entry_points": ["economy"], "capabilities": ["economy.view"]},
        {"key": "ai", "display_name": "AI Platform", "description": "AI diagnostics.", "emoji": "🤖",
         "visibility_tier": "administrator", "visibility_mode": "normal", "category": "admin",
         "tags": ["ai"], "entry_points": ["ai"], "capabilities": ["ai.view"]},
    ],
    "cogs": [
        {"cog": "EconomyCog", "file": "disbot/cogs/economy.py", "subsystem": "economy", "is_cog": True,
         "commands": [
             {"name": "daily", "type": "prefix", "is_group": False, "parent": None, "aliases": ["d"],
              "brief": "Claim daily coins.", "button_backed": False},
             {"name": "shop", "type": "both", "is_group": True, "parent": None, "aliases": [],
              "brief": "Open the shop.", "button_backed": True},
             {"name": "buy", "type": "slash", "is_group": False, "parent": "shop", "aliases": [],
              "brief": "Buy an item.", "button_backed": False},
         ]},
    ],
    "settings": [
        {"domain": "economy", "purpose": "Economy settings.", "keys": [
            {"constant": "DAILY_AMOUNT", "key": "daily_amount", "type": "int", "hint": "Coins per daily.",
             "allowed_values": [], "default": 100},
            {"constant": "SHOP_ENABLED", "key": "shop_enabled", "type": "bool", "hint": "Master switch.",
             "allowed_values": [], "default": True},
        ]},
    ],
    "access": {
        "tiers": [
            {"tier": "user", "discord_permission": None, "subsystems": [
                {"key": "economy", "display_name": "Economy", "category": "economy", "emoji": "💰"}]},
            {"tier": "administrator", "discord_permission": "administrator", "subsystems": [
                {"key": "ai", "display_name": "AI Platform", "category": "admin", "emoji": "🤖"}]},
        ],
        "total_visible": 2, "internal_count": 0,
    },
    "env_usage": [
        {"name": "DATABASE_URL", "required": True, "usage_count": 1, "layers": ["utils"],
         "usages": [{"file": "disbot/utils/db/pool.py", "line": 41, "layer": "utils", "has_default": False}]},
    ],
    "ideas": [
        {"file": "some-idea-2026-07-08.md", "title": "A good idea", "status": "ideas",
         "date": "2026-07-08", "summary": "Do the thing.", "subsystems": None},
    ],
    "bugs": [
        {"id": "BUG-0001", "title": "Something broke", "status": "OPEN", "summary": "It broke."},
    ],
    "updates": [
        {"file": "2026-07-08-x.md", "date": "2026-07-08", "title": "Session X", "status": "complete",
         "run_type": "", "self_initiated": True},
    ],
    "synonyms": [{"canonical": "daily", "synonyms": ["dailies"]}],
    "bot_changelog": [{"date": "2026-06-19", "title": "New site", "kind": "improvement", "summary": "New."}],
}

# Shaped per the pinned cross-repo contract (dashboard/console_data_contract.json,
# v1): ideas/bugs are counter DICTS, meta carries schema_version, telemetry exists.
CONSOLE_FIXTURE = {
    "meta": {"generated_at": "2026-07-08T16:20:05Z", "build": {"commit": "e9988b3b"},
             "schema_version": 1},
    "sessions": [{"file": "2026-07-08-x.md", "date": "2026-07-08", "title": "Session X",
                  "status": "complete", "run_type": "", "self_initiated": False}],
    "ideas": {"total": 221, "by_status": {"ideas": 200, "historical": 21}},
    "bugs": {"total": 30, "by_status": {"fixed": 27, "open": 3}, "open_count": 3,
             "open": [{"id": "BUG-0031", "title": "Something is off", "status": "open"}]},
    "bot_changelog": [{"date": "2026-06-19", "title": "New site", "kind": "improvement", "summary": "New."}],
    "telemetry": [{"session": "2026-07-08-x", "date": "2026-07-08", "model": "fable-5",
                   "effort": "high", "task_class": "docs-only", "tokens_out": None,
                   "outcome": {"ci_green_first_push": None, "checker_findings": None,
                               "merged_pr": None, "reverted_within_window": None}}],
}

READ_ONLY_PATHS = [
    "/", "/functions", "/commands", "/aliases", "/settings", "/access",
    "/env", "/ideas", "/bugs", "/updates", "/status", "/console", "/admin",
]


@pytest.fixture()
def client():
    ds.clear_cache()
    ds.prime_cache(ds.DASHBOARD_JSON_URL, DASHBOARD_FIXTURE)
    ds.prime_cache(ds.CONSOLE_JSON_URL, CONSOLE_FIXTURE)
    ds.set_client(ds.make_client())  # never actually hit (cache is warm)
    with TestClient(app_module.app) as c:
        yield c
    ds.clear_cache()


# --- auth ----------------------------------------------------------------
def test_healthz_unauthenticated(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_unauthenticated_is_401(client):
    r = client.get("/")
    assert r.status_code == 401
    assert "www-authenticate" in {k.lower() for k in r.headers}


def test_bad_password_is_401(client):
    bad = {"Authorization": "Basic " + base64.b64encode(b"any:wrong").decode()}
    assert client.get("/", headers=bad).status_code == 401


def test_authenticated_is_200(client):
    assert client.get("/", headers=AUTH).status_code == 200


def test_fail_closed_when_password_unset(client, monkeypatch):
    monkeypatch.setattr(config, "SITE_PASSWORD", "")
    r = client.get("/", headers=AUTH)
    assert r.status_code == 503  # never open when unset


# --- read-only pages -----------------------------------------------------
@pytest.mark.parametrize("path", READ_ONLY_PATHS)
def test_pages_render(client, path):
    r = client.get(path, headers=AUTH)
    assert r.status_code == 200
    assert "SuperBot" in r.text


def test_overview_shows_real_counts(client):
    r = client.get("/", headers=AUTH)
    assert ">2<" in r.text  # subsystem count from the fixture
    assert "Economy" in r.text


def test_commands_lists_real_commands(client):
    r = client.get("/commands", headers=AUTH)
    assert "!daily" in r.text
    assert "!shop buy" in r.text  # subcommand rendered with parent


def test_env_map_shows_names_not_values(client):
    r = client.get("/env", headers=AUTH)
    assert "DATABASE_URL" in r.text
    assert "disbot/utils/db/pool.py:41" in r.text
    assert "never a value" in r.text.lower() or "never a secret" in r.text.lower()


def test_settings_render(client):
    r = client.get("/settings", headers=AUTH)
    assert "daily_amount" in r.text
    assert "Coins per daily." in r.text


def test_access_ladder(client):
    r = client.get("/access", headers=AUTH)
    assert "AI Platform" in r.text
    assert "administrator" in r.text


def test_aliases_taken_map_embedded(client):
    r = client.get("/aliases", headers=AUTH)
    assert "dailies" in r.text  # existing synonym shown
    assert "taken-map" in r.text  # collision map embedded for the client checker


# --- the deliberate control-panel stub -----------------------------------
def test_admin_is_a_labeled_stub(client):
    r = client.get("/admin", headers=AUTH)
    assert r.status_code == 200
    assert "requires owner wiring" in r.text.lower()
    assert "not connected to the live bot" in r.text.lower()
    assert "stub-action" in r.text  # disabled placeholder styling present


def test_no_control_api_token_or_url_anywhere():
    """Hard guarantee: this service references no production bot control-API URL/token —
    not in Python source and not in any served template. The literal env-var identifiers
    a live-write control panel would need never appear anywhere in this service."""
    import pathlib

    root = pathlib.Path(app_module.__file__).resolve().parent
    forbidden = ["CONTROL_API_TOKEN", "CONTROL_API_URL", "worker.railway.internal", "DISCORD_OAUTH_CLIENT_SECRET"]
    for f in list(root.rglob("*.py")) + list(root.rglob("*.html")):
        if "tests" in f.parts:
            continue
        text = f.read_text(encoding="utf-8")
        for needle in forbidden:
            assert needle not in text, f"{needle} must not appear in {f}"


# --- honest degradation --------------------------------------------------
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
        r = c.get("/", headers=AUTH)
        assert r.status_code == 200
        assert "temporarily unavailable" in r.text.lower()
    ds.clear_cache()


def test_palette_index(client):
    r = client.get("/palette.json", headers=AUTH)
    assert r.status_code == 200
    labels = [i.get("label") for i in r.json()]
    assert "Overview" in labels
    assert "Economy" in labels  # subsystem indexed


# --- console feed shape contract (cross-repo pin) --------------------------
def test_console_renders_contracted_counter_dicts(client):
    """ideas/bugs are contracted counter DICTS; the tiles show total/open_count
    (the dict-vs-list defect the contract surfaced), and no drift banner shows."""
    r = client.get("/console", headers=AUTH)
    assert r.status_code == 200
    assert "221" in r.text  # ideas.total, not len(dict)==2
    assert "Open bugs" in r.text and "BUG-0031" in r.text
    assert "schema drift" not in r.text.lower()


def test_console_schema_version_mismatch_shows_banner():
    drifted = {**CONSOLE_FIXTURE, "meta": {**CONSOLE_FIXTURE["meta"], "schema_version": 99}}
    ds.clear_cache()
    ds.prime_cache(ds.DASHBOARD_JSON_URL, DASHBOARD_FIXTURE)
    ds.prime_cache(ds.CONSOLE_JSON_URL, drifted)
    ds.set_client(ds.make_client())
    with TestClient(app_module.app) as c:
        r = c.get("/console", headers=AUTH)
        assert r.status_code == 200
        assert "schema drift" in r.text.lower()
        assert "schema_version=99" in r.text
    ds.clear_cache()


def test_console_missing_family_shows_banner():
    shrunk = {k: v for k, v in CONSOLE_FIXTURE.items() if k != "telemetry"}
    ds.clear_cache()
    ds.prime_cache(ds.DASHBOARD_JSON_URL, DASHBOARD_FIXTURE)
    ds.prime_cache(ds.CONSOLE_JSON_URL, shrunk)
    ds.set_client(ds.make_client())
    with TestClient(app_module.app) as c:
        r = c.get("/console", headers=AUTH)
        assert r.status_code == 200
        assert "schema drift" in r.text.lower()
        assert "telemetry" in r.text
    ds.clear_cache()


def test_pinned_contract_matches_what_this_consumer_reads():
    """The pinned copy must cover everything the console route/template reads,
    and the fixture must satisfy it (so tests exercise the real shape)."""
    contract = ds.load_console_contract()
    assert isinstance(contract["version"], int)
    # Every family the route reads is contracted.
    for family in ("meta", "sessions", "ideas", "bugs", "bot_changelog"):
        assert family in contract["top_level"]
    # The fixture IS the contracted shape (version + families + counter dicts).
    assert ds.console_contract_issue(CONSOLE_FIXTURE) == ""
    assert set(CONSOLE_FIXTURE) == set(contract["top_level"])
    assert set(CONSOLE_FIXTURE["ideas"]) <= set(contract["ideas"])
    assert set(CONSOLE_FIXTURE["bugs"]) <= set(contract["bugs"])
    for row in CONSOLE_FIXTURE["sessions"]:
        assert set(row) == set(contract["session"])
    for row in CONSOLE_FIXTURE["telemetry"]:
        assert set(row) == set(contract["telemetry"])
