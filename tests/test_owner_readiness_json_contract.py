"""Authed `/owner/api/readiness.json` shape contract — pinned key sets for
machine consumers (the #217 `/fleet.json` contract-pin precedent,
`tests/test_fleet_json_contract.py`).

The authed readiness JSON is the machine twin of the `/owner` board — the
surface a scheduled healthcheck or fleet-manager session reads when the
owner is not looking. Since the environments rollup landed (backlog
promotion of the #223 board chip), the payload is an object: the board rows
under ``rows`` plus the SAME ``envhub.board_rollup`` dict the HTML chip
renders under ``environments``. An accidental key rename would break those
consumers SILENTLY — this file pins the exact shape so the contract is
changed consciously: update these sets in the SAME PR that changes the
payload, and say so in the PR body.

Also pinned, because this route is the authed one: the honesty ladder
(no live Railway truth → ``state: "unknown"`` WITH the reason, never a
fabricated green) and the never-values (no live variable VALUE, no token,
no password ever in the body — NAMES ONLY survives `railway._names_only`).
All tests fully offline.
"""

import base64
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app import config, envhub, github, railway  # noqa: E402
from app.main import app  # noqa: E402

OWNER_PW = "test-owner-pw"
URL = "/owner/api/readiness.json"

# Sentinel: the one value-shaped string in play — it exists ONLY inside the
# mocked live layer and must never reach the JSON body.
_SENTINEL_VALUE = "sekret-live-value-789"

# --- the pinned contract ---------------------------------------------------

# environments added 2026-07-13 (this PR): the board chip's env-completeness
# rollup (envhub.board_rollup, PR #223) attached for machine consumers —
# the same promotion the /fleet chip got in #217 (payload["coverage"]).
TOP_KEYS = {"rows", "environments"}

# envhub.board_rollup() output, verbatim — one honesty ladder, zero forked
# semantics (see its docstring in app/envhub.py).
ENVIRONMENTS_KEYS = {
    "state", "reason", "groups",
    "complete", "complete_names",
    "incomplete", "incomplete_names",
    "unknown", "unknown_names",
}

# The full states enum. "unknown" is a first-class honest state (registry
# unreadable / RAILWAY_TOKEN unset / live read failed), never an error.
ENVIRONMENTS_STATES = {"ok", "unknown"}

# ---------------------------------------------------------------------------


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
    default degraded state — individual tests patch the live read), GitHub
    fetches canned (same shape as tests/test_owner_readiness_env_chip.py —
    readiness.board degrades honestly)."""
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


def _patch_live_ok(monkeypatch):
    """A live Railway read where the superbot-websites group is fully set —
    every committed name present, values already dropped at the client
    boundary (names only, the railway._names_only shape)."""
    monkeypatch.setattr(config, "RAILWAY_TOKEN", "test-project-token")
    reg = envhub.load_registry()
    estate = next(g for g in reg["groups"] if g["id"] == "superbot-websites")

    async def fake(refresh=False):
        return {
            "state": "ok", "reason": "", "token_set": True,
            "services": [
                {"name": s["name"],
                 "variable_names": list(s["variable_names"]),
                 "count": len(s["variable_names"]), "error": None}
                for s in estate["surfaces"]
            ],
            "fetched_at": "12:00:00 UTC", "cached": False,
            "project_name": "superbot-websites",
        }

    monkeypatch.setattr(railway, "live_overview", fake)


def _payload(client):
    r = client.get(URL, headers=_basic())
    assert r.status_code == 200
    return r.json()


# --- gate behavior (pinned here too — the JSON must never widen exposure) ---


def test_gate_401_without_creds_and_wrong_password(client):
    assert client.get(URL).status_code == 401
    assert client.get(URL, headers=_basic("wrong")).status_code == 401


def test_route_is_get_only(client):
    assert client.post(URL, headers=_basic()).status_code == 405


# --- the pinned shape --------------------------------------------------------


def test_top_level_and_environments_shape(client):
    d = _payload(client)
    assert set(d.keys()) == TOP_KEYS, (
        f"top-level contract drift: {sorted(set(d) ^ TOP_KEYS)}"
    )
    assert isinstance(d["rows"], list)  # the board rows, unchanged shape
    env = d["environments"]
    assert set(env.keys()) == ENVIRONMENTS_KEYS, (
        f"environments contract drift: "
        f"{sorted(set(env) ^ ENVIRONMENTS_KEYS)}"
    )
    assert env["state"] in ENVIRONMENTS_STATES
    for key in ("groups", "complete", "incomplete", "unknown"):
        assert isinstance(env[key], int) and env[key] >= 0
    for key in ("complete_names", "incomplete_names", "unknown_names"):
        assert isinstance(env[key], list)
        assert all(isinstance(n, str) for n in env[key])
    assert isinstance(env["reason"], str)


def test_no_live_truth_is_honest_unknown_with_reason(client):
    # fixture default: RAILWAY_TOKEN unset → the rollup must be an honest
    # unknown WITH the reason, never a fabricated green or "incomplete: 0".
    env = _payload(client)["environments"]
    assert env["state"] == "unknown"
    assert env["reason"], "unknown state must carry its reason"
    assert "RAILWAY_TOKEN is not set" in env["reason"]
    assert env["complete"] == 0 and env["incomplete"] == 0
    assert env["complete_names"] == [] and env["incomplete_names"] == []


def test_live_read_failure_is_honest_unknown_with_reason(client, monkeypatch):
    monkeypatch.setattr(config, "RAILWAY_TOKEN", "test-project-token")

    async def fake(refresh=False):
        return {"state": "unavailable", "reason": "ConnectError: boom",
                "token_set": True, "services": []}

    monkeypatch.setattr(railway, "live_overview", fake)
    env = _payload(client)["environments"]
    assert env["state"] == "unknown"
    assert "ConnectError: boom" in env["reason"]
    assert env["complete"] == 0 and env["incomplete"] == 0


def test_ok_state_counts_are_exhaustive(client, monkeypatch):
    """Under an ok read every registry group lands in exactly one bucket —
    complete + incomplete + unknown == groups (out-of-scope groups count as
    unknown, never assumed complete OR incomplete — the #219 chip rule)."""
    _patch_live_ok(monkeypatch)
    env = _payload(client)["environments"]
    assert env["state"] == "ok"
    assert env["reason"] == ""
    assert env["groups"] == len(envhub.load_registry()["groups"])
    assert env["complete"] + env["incomplete"] + env["unknown"] == env["groups"]
    assert env["complete_names"] == ["superbot-websites"]
    assert len(env["complete_names"]) == env["complete"]
    assert len(env["incomplete_names"]) == env["incomplete"]
    assert len(env["unknown_names"]) == env["unknown"]


# --- never-values (the hard rail) --------------------------------------------


def test_never_values_in_the_json_body(client, monkeypatch):
    """NAMES ONLY: no live variable VALUE, no Railway token, no owner
    password ever appears in the authed JSON body — same rail the /owner
    HTML pins (tests/test_owner_readiness_env_chip.py)."""
    monkeypatch.setattr(config, "RAILWAY_TOKEN", "test-project-token")

    async def fake(refresh=False):
        # A value-shaped sentinel in the live layer's non-name fields: the
        # contract is that only NAMES survive into the rollup.
        return {
            "state": "ok", "reason": "", "token_set": True,
            "services": [
                {"name": "control-plane",
                 "variable_names": ["GITHUB_TOKEN", "SITE_PASSWORD"],
                 "count": 2, "error": None},
            ],
            "fetched_at": "12:00:00 UTC", "cached": False,
            "project_name": _SENTINEL_VALUE,
        }

    monkeypatch.setattr(railway, "live_overview", fake)
    r = client.get(URL, headers=_basic())
    assert r.status_code == 200
    assert _SENTINEL_VALUE not in r.text
    assert "test-project-token" not in r.text
    assert OWNER_PW not in r.text
