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


# --- verified live-API shapes (ORDER 022, checked 2026-07-12) ----------------
#
# The three query strings below were run verbatim against the live
# backboard.railway.app/graphql/v2 schema on 2026-07-12; the fixture mirrors
# the REAL response structure observed (structure only — fake ids/values):
# ``projectToken`` → {projectId, environmentId}; ``project(id:)`` →
# {name, services.edges[].node{id,name}} (four services);
# ``variables(...)`` → a flat name→value JSON map that includes the
# Railway-injected ``RAILWAY_*`` names alongside the owner-set ones.


def _fake_graphql_real_shape(seen: list):
    async def fake(query, variables=None):
        seen.append((query, variables or {}))
        if "projectToken" in query:
            return {
                "ok": True,
                "data": {
                    "projectToken": {
                        "projectId": "proj-fake-1",
                        "environmentId": "env-fake-1",
                    }
                },
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
                                {"node": {"id": "svc-1", "name": "control-plane"}},
                                {"node": {"id": "svc-2", "name": "dashboard"}},
                                {"node": {"id": "svc-3", "name": "botsite"}},
                                {"node": {"id": "svc-4", "name": "review"}},
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
                    "GITHUB_TOKEN": "fake-value",
                    "SITE_PASSWORD": "fake-value",
                    "RAILWAY_PROJECT_ID": "fake-value",
                    "RAILWAY_ENVIRONMENT_NAME": "fake-value",
                }
            },
            "error": "",
        }

    return fake


def test_query_shapes_match_verified_live_schema(monkeypatch):
    """The exact queries issued match the shapes verified live on 2026-07-12,
    and the parse handles the real four-service, RAILWAY_*-bearing response."""
    import asyncio

    monkeypatch.setattr(config, "RAILWAY_TOKEN", "test-project-token")
    seen: list = []
    monkeypatch.setattr(railway, "_graphql", _fake_graphql_real_shape(seen))
    data = asyncio.run(railway.live_overview(refresh=True))

    assert data["state"] == "ok"
    queries = " || ".join(q for q, _ in seen)
    # q1 — token scope (ProjectToken exposes projectId/environmentId).
    assert "projectToken { projectId environmentId }" in queries
    # q2 — project services (project(id: String!) → name + edges/node id,name).
    assert "project(id: $id)" in queries
    assert "services { edges { node { id name } } }" in queries
    # q3 — variables(projectId:, environmentId:, serviceId:) with the ids
    # threaded through from q1/q2, one call per service.
    var_calls = [v for q, v in seen if "variables(" in q]
    assert len(var_calls) == 4
    assert {v["serviceId"] for v in var_calls} == {"svc-1", "svc-2", "svc-3", "svc-4"}
    assert all(
        v["projectId"] == "proj-fake-1" and v["environmentId"] == "env-fake-1"
        for v in var_calls
    )
    # Parse: names only, sorted, values never kept.
    names = {s["name"]: s["variable_names"] for s in data["services"]}
    assert set(names) == {"control-plane", "dashboard", "botsite", "review"}
    assert names["control-plane"] == sorted(
        ["GITHUB_TOKEN", "SITE_PASSWORD", "RAILWAY_PROJECT_ID", "RAILWAY_ENVIRONMENT_NAME"]
    )
    assert "fake-value" not in repr(data)


# --- manage-link mapping ------------------------------------------------------


def test_manage_link_prefix_map():
    assert "discord.com/developers" in railway.manage_link("DISCORD_TOKEN")["url"]
    assert "github.com/settings/tokens" in railway.manage_link("GITHUB_TOKEN")["url"]
    assert "dashboard.stripe.com" in railway.manage_link("STRIPE_SECRET_KEY")["url"]
    # Unmatched names manage at the project's Railway console.
    assert railway.manage_link("DATABASE_URL")["url"] == railway.PROJECT_URL
