"""Offline tests for the gated /owner/environments page (ORDER 015 slice 1,
docs/planning/live-env-visibility-plan-2026-07-11.md).

Held invariants:
- the page rides the same /owner gate as the rest of the area (401/503);
- with RAILWAY_TOKEN unset (the documented production state until the owner
  errand lands) the page renders 200 with an explicit owner-errand banner and
  the committed per-service facts — no fabricated liveness;
- with a token set, live variable NAMES render but variable VALUES never
  appear anywhere (plan option A), and fetch failures degrade to an honest
  ``unavailable`` banner, still 200;
- the control-plane's own runtime presence column shows set/unset only —
  never an env var's value.
"""

import base64
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app import config, github, railway  # noqa: E402
from app.main import app  # noqa: E402

OWNER_PW = "test-owner-pw"


def _basic(pw: str = OWNER_PW, user: str = "owner") -> dict:
    token = base64.b64encode(f"{user}:{pw}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


@pytest.fixture(autouse=True)
def _isolate_railway_cache():
    railway.clear_cache()
    yield
    railway.clear_cache()


@pytest.fixture()
def client(monkeypatch):
    """Offline authed-ready client: password set, GitHub fetches canned."""
    monkeypatch.setattr(config, "SITE_PASSWORD", OWNER_PW)

    async def fake_get(url, refresh=False, raw=False):
        return {
            "ok": False, "status": 0, "data": None,
            "error": "offline test", "fetched_at": "", "cached": False,
            "url": url,
        }

    monkeypatch.setattr(github, "_get", fake_get)
    with TestClient(app) as c:
        yield c


# --- gate behavior ----------------------------------------------------------


def test_requires_auth(client):
    """No/wrong credentials → 401, like every other /owner route."""
    assert client.get("/owner/environments").status_code == 401
    assert (
        client.get("/owner/environments", headers=_basic("wrong")).status_code
        == 401
    )


def test_fails_closed_when_password_unset(client, monkeypatch):
    """SITE_PASSWORD unset → 503 even with credentials supplied."""
    monkeypatch.setattr(config, "SITE_PASSWORD", "")
    r = client.get("/owner/environments", headers=_basic())
    assert r.status_code == 503


# --- degraded (no-token) state — the state production is in today -----------


def test_no_token_renders_owner_errand_banner(client, monkeypatch):
    """RAILWAY_TOKEN unset → 200, explicit owner-errand banner, no live data."""
    monkeypatch.setattr(config, "RAILWAY_TOKEN", "")
    r = client.get("/owner/environments", headers=_basic())
    assert r.status_code == 200
    assert "owner errand pending" in r.text
    assert "RAILWAY_TOKEN is not set" in r.text
    # Committed facts still render for all three services.
    for svc in ("control-plane", "botsite", "dashboard"):
        assert svc in r.text, f"{svc} card missing from degraded page"
    # The plan doc is cited so the owner can trace the pending decision.
    assert "live-env-visibility-plan-2026-07-11" in r.text


def test_no_token_shows_runtime_presence_not_values(client, monkeypatch):
    """The control-plane's own column is presence-only — never a value."""
    monkeypatch.setattr(config, "RAILWAY_TOKEN", "")
    monkeypatch.setenv("GITHUB_TOKEN", "tok-value-should-never-render")
    monkeypatch.delenv("SITE_JSON_URL", raising=False)
    r = client.get("/owner/environments", headers=_basic())
    assert r.status_code == 200
    assert "tok-value-should-never-render" not in r.text
    assert "set (this runtime)" in r.text
    # Sibling services' runtime state is unknowable without the live read.
    assert "needs live Railway read" in r.text


# --- live (token-set) paths, GraphQL mocked ---------------------------------

_SENTINEL_VALUE = "sekret-live-value-123"


def _fake_graphql_ok():
    async def fake(query, variables=None):
        if "projectToken" in query:
            return {
                "ok": True,
                "data": {"projectToken": {"projectId": "p1", "environmentId": "e1"}},
                "error": "",
            }
        if "services" in query:
            return {
                "ok": True,
                "data": {
                    "project": {
                        "name": "superbot-websites",
                        "services": {
                            "edges": [
                                {"node": {"id": "s1", "name": "control-plane"}},
                                {"node": {"id": "s2", "name": "botsite"}},
                            ]
                        },
                    }
                },
                "error": "",
            }
        return {
            "ok": True,
            "data": {
                "variables": {
                    "GITHUB_TOKEN": _SENTINEL_VALUE,
                    "DISCORD_CLIENT_ID": _SENTINEL_VALUE,
                }
            },
            "error": "",
        }

    return fake


def test_live_names_render_values_never(client, monkeypatch):
    """Token set + healthy API → names + manage links; values dropped at the
    client boundary (never in the overview dict, never in the HTML)."""
    monkeypatch.setattr(config, "RAILWAY_TOKEN", "test-project-token")
    monkeypatch.setattr(railway, "_graphql", _fake_graphql_ok())
    r = client.get("/owner/environments", headers=_basic())
    assert r.status_code == 200
    assert "GITHUB_TOKEN" in r.text and "DISCORD_CLIENT_ID" in r.text
    assert _SENTINEL_VALUE not in r.text
    assert "test-project-token" not in r.text  # the token itself never renders
    assert "manage →" in r.text


def test_live_overview_dict_carries_no_values(monkeypatch):
    """Defense in depth: the assembled snapshot itself holds names only."""
    import asyncio

    monkeypatch.setattr(config, "RAILWAY_TOKEN", "test-project-token")
    monkeypatch.setattr(railway, "_graphql", _fake_graphql_ok())
    data = asyncio.run(railway.live_overview(refresh=True))
    assert data["state"] == "ok"
    assert _SENTINEL_VALUE not in repr(data)
    names = {s["name"]: s["variable_names"] for s in data["services"]}
    assert names["control-plane"] == ["DISCORD_CLIENT_ID", "GITHUB_TOKEN"]


def test_live_fetch_failure_degrades_unavailable(client, monkeypatch):
    """Token set but the read fails → 200 with the exact reason, no 500."""
    monkeypatch.setattr(config, "RAILWAY_TOKEN", "test-project-token")

    async def fake(query, variables=None):
        return {"ok": False, "data": None, "error": "ConnectError: boom"}

    monkeypatch.setattr(railway, "_graphql", fake)
    r = client.get("/owner/environments", headers=_basic())
    assert r.status_code == 200
    assert "live Railway read failed" in r.text
    assert "ConnectError: boom" in r.text


# --- manage-link mapping ------------------------------------------------------


def test_manage_link_prefix_map():
    assert "discord.com/developers" in railway.manage_link("DISCORD_TOKEN")["url"]
    assert "github.com/settings/tokens" in railway.manage_link("GITHUB_TOKEN")["url"]
    assert "dashboard.stripe.com" in railway.manage_link("STRIPE_SECRET_KEY")["url"]
    # Unmatched names manage at the project's Railway console.
    assert railway.manage_link("DATABASE_URL")["url"] == railway.PROJECT_URL
