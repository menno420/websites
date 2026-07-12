"""Offline tests for the /owner board environments rollup chip (the #219
session's captured idea, promoted): ``envhub.board_rollup`` reduces the
EXISTING per-group completeness summaries (``envhub.group_summary``, PR #219
— itself pure reuse of PR #216's ``annotate_completeness``) to ONE chip on
the gated ``GET /owner`` readiness board, fed by the SAME TTL-cached
``railway.live_overview`` read the environments-hub makes — zero new network
surface, zero new routes (the #217 /fleet coverage-rollup promotion ladder).

Honesty ladder pinned here: every readable group complete → green
"environments: all complete"; N groups incomplete → amber with the groups
NAMED + the hub deep link; live read failed / token unset / registry broken
→ the honest unknown chip WITH the exact reason — never a fabricated green
or "incomplete: 0"; out-of-scope groups count as unknown, never assumed.
NAMES NEVER VALUES: no mocked Railway variable VALUE ever reaches the page.
All tests fully offline (``railway._graphql`` mocked, GitHub canned).
"""

import asyncio
import base64
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app import config, envhub, github, railway  # noqa: E402
from app.main import app  # noqa: E402

OWNER_PW = "test-owner-pw"
BOARD_URL = "/owner"

# Sentinel: the one value-shaped string in play — it exists ONLY inside the
# mocked GraphQL layer and must never survive past railway._names_only.
_SENTINEL_VALUE = "sekret-live-value-789"

GREEN_TEXT = "environments: all complete"
UNKNOWN_TEXT = "environments: live status unknown"


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
    """Offline authed-ready client: password set, no Railway token (the
    default degraded state — individual tests set a fake token + mocked
    GraphQL), GitHub fetches canned (same shape as
    tests/test_envhub_group_chips.py — readiness.board degrades honestly)."""
    monkeypatch.setattr(config, "SITE_PASSWORD", OWNER_PW)
    monkeypatch.setattr(config, "RAILWAY_TOKEN", "")

    async def fake_get(url, refresh=False, raw=False):
        return {
            "ok": False, "status": 0, "data": None,
            "error": "offline test", "fetched_at": "", "cached": False,
            "url": url,
        }

    monkeypatch.setattr(github, "_get", fake_get)
    with TestClient(app) as c:
        yield c


def _committed_names(surface_id: str) -> list[str]:
    reg = envhub.load_registry()
    estate = next(g for g in reg["groups"] if g["id"] == "superbot-websites")
    surface = next(s for s in estate["surfaces"] if s["id"] == surface_id)
    return list(surface["variable_names"])


def _group_count() -> int:
    return len(envhub.load_registry()["groups"])


def _fake_graphql(names_by_service_id: dict[str, list[str]],
                  service_nodes: list[tuple[str, str]]):
    """A mocked railway._graphql: projectToken scope, the given service
    nodes, and per-service variable maps whose VALUES are all the sentinel
    (they must be dropped at the client boundary, never rendered)."""
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
                                {"node": {"id": sid, "name": name}}
                                for sid, name in service_nodes
                            ]
                        },
                    }
                },
                "error": "",
            }
        sid = (variables or {}).get("serviceId", "")
        return {
            "ok": True,
            "data": {
                "variables": {
                    name: _SENTINEL_VALUE
                    for name in names_by_service_id.get(sid, [])
                }
            },
            "error": "",
        }

    return fake


def _all_set_live(monkeypatch):
    """Token set + mocked live read where every committed name is set."""
    monkeypatch.setattr(config, "RAILWAY_TOKEN", "test-project-token")
    monkeypatch.setattr(
        railway,
        "_graphql",
        _fake_graphql(
            {
                f"s{i}": _committed_names(sid)
                for i, sid in enumerate(
                    ("control-plane", "botsite", "dashboard", "review"), start=1
                )
            },
            [("s1", "control-plane"), ("s2", "botsite"),
             ("s3", "dashboard"), ("s4", "review")],
        ),
    )


def _partial_live(monkeypatch):
    """Token set + mocked live read: control-plane fully set, botsite
    partially set, dashboard fully set, review ABSENT from the live project
    (not created yet) — same mix as the hub group-chip tests."""
    monkeypatch.setattr(config, "RAILWAY_TOKEN", "test-project-token")
    monkeypatch.setattr(
        railway,
        "_graphql",
        _fake_graphql(
            names_by_service_id={
                "s1": _committed_names("control-plane"),
                "s2": ["SITE_JSON_URL", "PORT", "EXTRA_LIVE_ONLY"],
                "s3": _committed_names("dashboard"),
            },
            service_nodes=[
                ("s1", "control-plane"), ("s2", "botsite"), ("s3", "dashboard"),
            ],
        ),
    )


# --- gate behavior (pinned here too — the chip must never widen exposure) -------


def test_gate_401_without_creds_and_wrong_password(client):
    assert client.get(BOARD_URL).status_code == 401
    assert client.get(BOARD_URL, headers=_basic("wrong")).status_code == 401


# --- chip states through the route ----------------------------------------------


def test_all_complete_renders_green_chip(client, monkeypatch):
    _all_set_live(monkeypatch)
    r = client.get(BOARD_URL, headers=_basic())
    assert r.status_code == 200
    assert f"{GREEN_TEXT} (1 group)" in r.text
    assert "incomplete" not in r.text
    # the out-of-scope groups are counted honestly, never assumed complete.
    assert f"+{_group_count() - 1} unknown" in r.text


def test_incomplete_renders_amber_chip_with_group_named(client, monkeypatch):
    _partial_live(monkeypatch)
    r = client.get(BOARD_URL, headers=_basic())
    assert r.status_code == 200
    assert "environments: 1 group incomplete" in r.text
    assert "<code>superbot-websites</code>" in r.text  # the group is NAMED
    assert "/owner/environments-hub" in r.text  # the checklist deep link
    assert GREEN_TEXT not in r.text


def test_live_read_failure_renders_unknown_with_reason(client, monkeypatch):
    monkeypatch.setattr(config, "RAILWAY_TOKEN", "test-project-token")

    async def fake(query, variables=None):
        return {"ok": False, "data": None, "error": "ConnectError: boom"}

    monkeypatch.setattr(railway, "_graphql", fake)
    r = client.get(BOARD_URL, headers=_basic())
    assert r.status_code == 200  # the board still renders
    assert UNKNOWN_TEXT in r.text
    assert "ConnectError: boom" in r.text  # the exact reason is surfaced
    assert GREEN_TEXT not in r.text
    assert "group incomplete" not in r.text


def test_token_missing_renders_unknown_with_reason(client):
    # fixture default: RAILWAY_TOKEN unset → not-configured, never a green.
    r = client.get(BOARD_URL, headers=_basic())
    assert r.status_code == 200
    assert UNKNOWN_TEXT in r.text
    assert "RAILWAY_TOKEN is not set" in r.text
    assert GREEN_TEXT not in r.text


def test_broken_registry_renders_unknown_not_a_verdict(client, monkeypatch):
    """A broken/empty registry (load_registry raises) degrades to the honest
    unknown chip WITH the reason — the board itself still renders 200."""
    _all_set_live(monkeypatch)

    def broken():
        raise ValueError("registry has no groups")

    monkeypatch.setattr(envhub, "load_registry", broken)
    r = client.get(BOARD_URL, headers=_basic())
    assert r.status_code == 200
    assert UNKNOWN_TEXT in r.text
    assert "registry has no groups" in r.text
    assert GREEN_TEXT not in r.text
    assert "group incomplete" not in r.text


# --- board_rollup unit precision --------------------------------------------------


def _live_ok(services):
    return {
        "state": "ok", "reason": "", "token_set": True, "services": services,
        "fetched_at": "12:00:00 UTC", "cached": False,
        "project_name": "superbot-websites",
    }


def _patch_live(monkeypatch, live):
    async def fake(refresh=False):
        return live

    monkeypatch.setattr(railway, "live_overview", fake)


def test_rollup_incomplete_names_the_group(monkeypatch):
    _patch_live(monkeypatch, _live_ok([
        {"name": "control-plane",
         "variable_names": ["GITHUB_TOKEN", "SITE_PASSWORD"], "count": 2,
         "error": None},
    ]))
    out = asyncio.run(envhub.board_rollup())
    assert out["state"] == "ok"
    assert out["groups"] == _group_count()
    assert out["incomplete"] == 1
    assert out["incomplete_names"] == ["superbot-websites"]
    assert out["complete"] == 0
    # every other group is out of the token's scope → unknown, never assumed.
    assert out["unknown"] == _group_count() - 1
    assert "superbot-websites" not in out["unknown_names"]


def test_rollup_no_live_truth_is_unknown_with_reason(monkeypatch):
    _patch_live(monkeypatch, {
        "state": "unavailable", "reason": "ConnectError: boom",
        "token_set": True, "services": [],
    })
    out = asyncio.run(envhub.board_rollup())
    assert out["state"] == "unknown"
    assert "ConnectError: boom" in out["reason"]
    assert out["complete"] == 0 and out["incomplete"] == 0


def test_rollup_broken_registry_is_unknown_never_raises(monkeypatch):
    def broken():
        raise ValueError("registry has no groups")

    monkeypatch.setattr(envhub, "load_registry", broken)
    out = asyncio.run(envhub.board_rollup())
    assert out["state"] == "unknown"
    assert "registry has no groups" in out["reason"]
    assert out["groups"] == 0
    assert out["incomplete"] == 0 and out["complete"] == 0


def test_rollup_green_only_when_strictly_complete(monkeypatch):
    """set_count == total is the #219 chip rule — a partially unreadable
    group is incomplete/amber, never a false all-clear."""
    reg = envhub.load_registry()
    estate = next(g for g in reg["groups"] if g["id"] == "superbot-websites")
    _patch_live(monkeypatch, _live_ok([
        {"name": s["name"], "variable_names": list(s["variable_names"]),
         "count": len(s["variable_names"]), "error": None}
        for s in estate["surfaces"]
    ]))
    out = asyncio.run(envhub.board_rollup())
    assert out["state"] == "ok"
    assert out["complete"] == 1
    assert out["complete_names"] == ["superbot-websites"]
    assert out["incomplete"] == 0


# --- NAMES NEVER VALUES (the hard rail) -----------------------------------------


def test_no_live_value_ever_reaches_the_board(client, monkeypatch):
    _partial_live(monkeypatch)
    r = client.get(BOARD_URL, headers=_basic())
    assert r.status_code == 200
    assert _SENTINEL_VALUE not in r.text
    assert "test-project-token" not in r.text
    assert OWNER_PW not in r.text
