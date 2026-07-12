"""Offline tests for the documented-vs-live variable NAME drift check on the
gated /owner/environments page (app/envdrift.py, the captured backlog bullet
"/owner/environments drift check: documented vs live variable names").

Held invariants:
- the page rides the same /owner gate as the rest of the area (401 without
  credentials / 503 while SITE_PASSWORD is unconfigured);
- all five drift states render honestly: no drift / documented-but-missing-
  live / live-but-undocumented / both at once / Railway-unreachable → drift
  UNKNOWN with the exact reason — a match is never fabricated;
- NAMES NEVER VALUES: variable values planted in the mocked Railway payload
  never appear in the annotated data structure or the rendered HTML;
- Railway-provided ``RAILWAY_*`` names and the runtime-injected ``PORT`` are
  informational, never counted as drift;
- a documented service absent from a SUCCESSFUL live read is honest drift
  (service not created yet), not unknown.

No network: the Railway GraphQL client is monkeypatched throughout.
"""

import asyncio
import base64
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app import config, envdrift, github, railway  # noqa: E402
from app.main import app  # noqa: E402

OWNER_PW = "test-owner-pw"
_SENTINEL_VALUE = "sekret-live-value-drift-999"


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


def _documented(service_name: str) -> list[str]:
    """The committed documented names for one service (the drift baseline)."""
    for svc in railway.SERVICES:
        if svc["name"] == service_name:
            return [var["name"] for var in svc["env_vars"]]
    raise AssertionError(f"unknown service {service_name!r}")


def _fake_graphql(varmaps: dict[str, dict], service_names: list[str] | None = None):
    """A healthy mocked Railway API: services from ``varmaps`` keys (or the
    explicit list), each answering its variables query with its map."""
    names = service_names if service_names is not None else sorted(varmaps)
    nodes = [{"node": {"id": f"id-{n}", "name": n}} for n in names]
    id_to_name = {f"id-{n}": n for n in names}

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
                        "services": {"edges": nodes},
                    }
                },
                "error": "",
            }
        svc_name = id_to_name.get((variables or {}).get("serviceId", ""), "")
        return {
            "ok": True,
            "data": {"variables": dict(varmaps.get(svc_name, {}))},
            "error": "",
        }

    return fake


def _full_live_maps(**overrides: dict) -> dict[str, dict]:
    """Live maps exactly matching every documented service's names (PORT
    excluded — Railway injects it at runtime, per the module's exemption),
    plus a Railway-provided name that must never count as drift."""
    maps: dict[str, dict] = {}
    for svc in railway.SERVICES:
        maps[svc["name"]] = {
            name: _SENTINEL_VALUE
            for name in _documented(svc["name"])
            if name not in envdrift.RUNTIME_INJECTED
        }
        maps[svc["name"]]["RAILWAY_PUBLIC_DOMAIN"] = _SENTINEL_VALUE
    for name, varmap in overrides.items():
        maps[name] = varmap
    return maps


def _page(client, monkeypatch, varmaps, service_names=None):
    monkeypatch.setattr(config, "RAILWAY_TOKEN", "test-project-token")
    monkeypatch.setattr(railway, "_graphql", _fake_graphql(varmaps, service_names))
    r = client.get("/owner/environments", headers=_basic())
    assert r.status_code == 200
    return r


# --- gate behavior (pinned for this page, same idiom as the rest of /owner) --


def test_requires_auth(client):
    """No/wrong credentials → 401."""
    assert client.get("/owner/environments").status_code == 401
    assert (
        client.get("/owner/environments", headers=_basic("wrong")).status_code
        == 401
    )


def test_fails_closed_when_password_unset(client, monkeypatch):
    """SITE_PASSWORD unset → 503 even with credentials supplied."""
    monkeypatch.setattr(config, "SITE_PASSWORD", "")
    assert client.get("/owner/environments", headers=_basic()).status_code == 503


# --- state 1: no drift --------------------------------------------------------


def test_no_drift_renders_clean_chip(client, monkeypatch):
    """Live names == documented names → the green no-drift chip; the
    Railway-provided RAILWAY_* extra and the runtime-injected PORT are
    informational, never drift."""
    r = _page(client, monkeypatch, _full_live_maps())
    assert "no name drift" in r.text
    assert '<span class="b warn">name drift</span>' not in r.text
    assert '<span class="b unknown">drift unknown</span>' not in r.text
    assert "documented-but-missing-live" not in r.text
    assert "live-but-undocumented" not in r.text
    # The informational classifications are visible, honestly labeled.
    assert "Railway-provided" in r.text
    assert "runtime-injected" in r.text


# --- state 2: documented-but-missing-live --------------------------------------


def test_documented_but_missing_live(client, monkeypatch):
    """A documented name absent from the live read is flagged BY NAME."""
    maps = _full_live_maps()
    del maps["control-plane"]["GITHUB_TOKEN"]
    r = _page(client, monkeypatch, maps)
    assert "name drift" in r.text
    assert "documented-but-missing-live" in r.text
    assert "GITHUB_TOKEN" in r.text
    assert "missing live" in r.text  # the per-variable column badge
    assert "live-but-undocumented" not in r.text


# --- state 3: live-but-undocumented --------------------------------------------


def test_live_but_undocumented(client, monkeypatch):
    """A live name the repo does not document is flagged BY NAME."""
    maps = _full_live_maps()
    maps["botsite"]["MYSTERY_VAR"] = _SENTINEL_VALUE
    r = _page(client, monkeypatch, maps)
    assert "name drift" in r.text
    assert "live-but-undocumented" in r.text
    assert "MYSTERY_VAR" in r.text
    assert "documented-but-missing-live" not in r.text


# --- state 4: both at once ------------------------------------------------------


def test_both_directions_at_once(client, monkeypatch):
    maps = _full_live_maps()
    del maps["dashboard"]["CONSOLE_JSON_URL"]
    maps["dashboard"]["EXTRA_UNDOCUMENTED"] = _SENTINEL_VALUE
    r = _page(client, monkeypatch, maps)
    assert "documented-but-missing-live" in r.text
    assert "CONSOLE_JSON_URL" in r.text
    assert "live-but-undocumented" in r.text
    assert "EXTRA_UNDOCUMENTED" in r.text


# --- state 5: Railway unreachable → unknown, with the reason --------------------


def test_unreachable_is_unknown_with_reason(client, monkeypatch):
    """Token set but the read fails → drift UNKNOWN carrying the exact
    error — never a fabricated match or mismatch."""
    monkeypatch.setattr(config, "RAILWAY_TOKEN", "test-project-token")

    async def fake(query, variables=None):
        return {"ok": False, "data": None, "error": "ConnectError: boom"}

    monkeypatch.setattr(railway, "_graphql", fake)
    r = client.get("/owner/environments", headers=_basic())
    assert r.status_code == 200
    assert "drift unknown" in r.text
    assert "ConnectError: boom" in r.text
    assert "no name drift" not in r.text
    assert "documented-but-missing-live" not in r.text


def test_no_token_is_unknown_with_owner_errand_reason(client, monkeypatch):
    """RAILWAY_TOKEN unset → drift UNKNOWN with the owner-errand reason."""
    monkeypatch.setattr(config, "RAILWAY_TOKEN", "")
    r = client.get("/owner/environments", headers=_basic())
    assert r.status_code == 200
    assert "drift unknown" in r.text
    assert "RAILWAY_TOKEN is not set" in r.text
    assert "no name drift" not in r.text


# --- absent service = honest drift, not unknown ---------------------------------


def test_service_absent_from_successful_read_is_drift(client, monkeypatch):
    """The live read SUCCEEDED but a documented service is not in it → the
    service is not created yet: honest drift (all documented names missing
    live), never unknown."""
    maps = _full_live_maps()
    del maps["review"]
    r = _page(client, monkeypatch, maps)
    assert "service not found in the live project" in r.text
    assert "ANTHROPIC_API_KEY" in r.text  # named as missing live
    assert "name drift" in r.text


def test_undocumented_live_service_is_drift(client, monkeypatch):
    """A live service the repo documents nothing about is service-level
    drift, surfaced by name on the rollup."""
    maps = _full_live_maps()
    maps["ghost-service"] = {"SOME_VAR": _SENTINEL_VALUE}
    r = _page(client, monkeypatch, maps)
    assert "ghost-service" in r.text
    assert "the repo does not document" in r.text


# --- per-service fetch error → that service unknown, others compared ------------


def test_per_service_error_is_partial_unknown(client, monkeypatch):
    maps = _full_live_maps()

    base = _fake_graphql(maps)

    async def fake(query, variables=None):
        if "variables(" in query and (variables or {}).get("serviceId") == "id-botsite":
            return {"ok": False, "data": None, "error": "HTTP 500"}
        return await base(query, variables)

    monkeypatch.setattr(config, "RAILWAY_TOKEN", "test-project-token")
    monkeypatch.setattr(railway, "_graphql", fake)
    r = client.get("/owner/environments", headers=_basic())
    assert r.status_code == 200
    # The broken service is unknown with its reason; the rest still compare.
    assert "live variables read failed for this service" in r.text
    assert "no name drift" in r.text
    assert "1 service unknown" in r.text


# --- NAMES NEVER VALUES ----------------------------------------------------------


def test_values_never_render(client, monkeypatch):
    """The sentinel value planted in every mocked live map must never reach
    the HTML, in any drift state."""
    maps = _full_live_maps()
    del maps["control-plane"]["GITHUB_TOKEN"]
    maps["botsite"]["MYSTERY_VAR"] = _SENTINEL_VALUE
    r = _page(client, monkeypatch, maps)
    assert _SENTINEL_VALUE not in r.text
    assert "test-project-token" not in r.text


def test_annotated_data_carries_no_values(monkeypatch):
    """Defense in depth: the annotated overview payload itself holds names
    only — the values were dropped at the client boundary and the annotate
    pass cannot resurrect what does not exist."""
    monkeypatch.setattr(config, "RAILWAY_TOKEN", "test-project-token")
    monkeypatch.setattr(railway, "_graphql", _fake_graphql(_full_live_maps()))
    data = asyncio.run(railway.overview(refresh=True))
    envdrift.annotate(data)
    assert _SENTINEL_VALUE not in repr(data)
    assert data["drift"]["state"] == "ok"


# --- unit: annotate honesty rules -------------------------------------------------


def test_annotate_unknown_reason_is_carried():
    data = {
        "services": [
            {"name": "control-plane", "env_vars": [{"name": "GITHUB_TOKEN"}]},
        ],
        "live": {"state": "unavailable", "reason": "exact reason here"},
    }
    envdrift.annotate(data)
    assert data["drift"]["state"] == "unknown"
    assert data["drift"]["comparable"] is False
    assert data["drift"]["reason"] == "exact reason here"
    svc = data["services"][0]
    assert svc["drift"]["state"] == "unknown"
    assert svc["drift"]["reason"] == "exact reason here"
    assert svc["env_vars"][0]["live_state"] == "unknown"


def test_annotate_railway_provided_never_counts_as_drift():
    data = {
        "services": [
            {"name": "botsite", "env_vars": [{"name": "SITE_JSON_URL"}]},
        ],
        "live": {
            "state": "ok",
            "services": [
                {
                    "name": "botsite",
                    "variable_names": [
                        "RAILWAY_PUBLIC_DOMAIN",
                        "RAILWAY_SERVICE_ID",
                        "SITE_JSON_URL",
                    ],
                    "error": None,
                }
            ],
        },
    }
    envdrift.annotate(data)
    svc = data["services"][0]
    assert svc["drift"]["state"] == "ok"
    assert svc["drift"]["undocumented"] == []
    assert svc["drift"]["railway_provided"] == [
        "RAILWAY_PUBLIC_DOMAIN",
        "RAILWAY_SERVICE_ID",
    ]
    assert data["drift"]["state"] == "ok"


def test_annotate_railway_token_is_real_drift():
    """RAILWAY_TOKEN is owner-set, not Railway-managed — undocumented live
    RAILWAY_TOKEN on a service IS drift (the deliberate prefix exception)."""
    data = {
        "services": [
            {"name": "botsite", "env_vars": [{"name": "SITE_JSON_URL"}]},
        ],
        "live": {
            "state": "ok",
            "services": [
                {
                    "name": "botsite",
                    "variable_names": ["RAILWAY_TOKEN", "SITE_JSON_URL"],
                    "error": None,
                }
            ],
        },
    }
    envdrift.annotate(data)
    assert data["services"][0]["drift"]["undocumented"] == ["RAILWAY_TOKEN"]
    assert data["drift"]["state"] == "drift"


def test_annotate_port_is_runtime_injected_not_drift():
    data = {
        "services": [
            {"name": "botsite", "env_vars": [{"name": "PORT"}, {"name": "A_VAR"}]},
        ],
        "live": {
            "state": "ok",
            "services": [
                {"name": "botsite", "variable_names": ["A_VAR"], "error": None}
            ],
        },
    }
    envdrift.annotate(data)
    svc = data["services"][0]
    assert svc["drift"]["state"] == "ok"
    assert svc["env_vars"][0]["live_state"] == "runtime-injected"
    assert svc["env_vars"][1]["live_state"] == "set-live"


def test_annotate_all_services_errored_is_unknown_overall():
    data = {
        "services": [
            {"name": "botsite", "env_vars": [{"name": "A_VAR"}]},
        ],
        "live": {
            "state": "ok",
            "services": [
                {"name": "botsite", "variable_names": [], "error": "HTTP 500"}
            ],
        },
    }
    envdrift.annotate(data)
    assert data["drift"]["state"] == "unknown"
    assert data["drift"]["comparable"] is False
    assert data["drift"]["services_unknown"] == 1
