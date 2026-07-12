"""Offline tests for the hub-index group completeness chips (the captured
backlog bullet "Completeness chip on the environments-hub group headers",
promoted): each group header on the gated ``GET /owner/environments-hub``
index carries a chip beside its create-complete-environment manifest link —
"X/Y set live" (green when X==Y, amber otherwise) computed by
``envhub.group_summary`` (pure reuse of PR #216's ``annotate_completeness``
over the SAME cached ``railway.live_overview`` read the page already makes),
or the honest "live status unknown" WITH the reason whenever the live truth
is not knowable — never a fabricated 0/Y.

Held invariants:
- every expected variable set live → green "Y/Y set live" chip; anything
  unfinished → amber "X/Y set live" chip;
- Railway unreachable / token missing → the unknown chip carrying the exact
  reason on EVERY group (never a fake 0/Y), and the page still renders 200;
- mixed groups on one page: the in-scope group gets its numeric chip while
  every out-of-scope group stays honestly unknown, never assumed;
- NAMES NEVER VALUES: no mocked Railway variable VALUE ever appears in the
  rendered HTML (pinned with a sentinel value in the mocked GraphQL layer);
- the index rides the exact /owner HTTP Basic gate (401 without creds);
- all tests fully offline (``railway._graphql`` mocked, GitHub canned).
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
HUB_URL = "/owner/environments-hub"

# Sentinel: the one value-shaped string in play — it exists ONLY inside the
# mocked GraphQL layer and must never survive past railway._names_only.
_SENTINEL_VALUE = "sekret-live-value-789"

UNKNOWN_CHIP = '<span class="b unknown">live status unknown</span>'


def _green_chip(x: int, y: int) -> str:
    return f'<span class="b ok">{x}/{y} set live</span>'


def _amber_chip(x: int, y: int) -> str:
    return f'<span class="b warn">{x}/{y} set live</span>'


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
    GraphQL), GitHub fetches canned (same shape as tests/test_envhub.py)."""
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


def _estate_total() -> int:
    reg = envhub.load_registry()
    estate = next(g for g in reg["groups"] if g["id"] == "superbot-websites")
    return sum(len(s["variable_names"]) for s in estate["surfaces"])


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
    (not created yet) — same mix as the manifest completeness tests."""
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


# --- gate behavior (pinned here too — the chips must never widen exposure) ------


def test_gate_401_without_creds_and_wrong_password(client):
    assert client.get(HUB_URL).status_code == 401
    assert client.get(HUB_URL, headers=_basic("wrong")).status_code == 401


# --- chip states through the route ----------------------------------------------


def test_all_set_group_renders_green_chip(client, monkeypatch):
    _all_set_live(monkeypatch)
    r = client.get(HUB_URL, headers=_basic())
    assert r.status_code == 200
    total = _estate_total()
    assert _green_chip(total, total) in r.text
    # complete means complete: no amber "set live" chip anywhere.
    assert 'class="b warn"' not in r.text


def test_partial_group_renders_amber_chip(client, monkeypatch):
    _partial_live(monkeypatch)
    r = client.get(HUB_URL, headers=_basic())
    assert r.status_code == 200
    # 10 (control-plane) + 2 (botsite) + 6 (dashboard) = 18 of 25 —
    # review's absence from a SUCCESSFUL read is honest missing, not unknown.
    assert _amber_chip(18, _estate_total()) in r.text
    assert _green_chip(_estate_total(), _estate_total()) not in r.text


def test_live_read_failure_renders_unknown_with_reason(client, monkeypatch):
    monkeypatch.setattr(config, "RAILWAY_TOKEN", "test-project-token")

    async def fake(query, variables=None):
        return {"ok": False, "data": None, "error": "ConnectError: boom"}

    monkeypatch.setattr(railway, "_graphql", fake)
    r = client.get(HUB_URL, headers=_basic())
    assert r.status_code == 200  # the page still renders
    # NEVER a fabricated 0/Y — every group's chip is honestly unknown...
    assert "set live</span>" not in r.text
    assert r.text.count(UNKNOWN_CHIP) == _group_count()
    # ...and the exact reason is surfaced next to it.
    assert "ConnectError: boom" in r.text


def test_token_missing_renders_unknown_with_reason(client):
    # fixture default: RAILWAY_TOKEN unset → not-configured, never a 0/Y.
    r = client.get(HUB_URL, headers=_basic())
    assert r.status_code == 200
    assert "set live</span>" not in r.text
    assert r.text.count(UNKNOWN_CHIP) == _group_count()
    assert "RAILWAY_TOKEN is not set" in r.text


def test_mixed_groups_on_one_page(client, monkeypatch):
    # A healthy live read paints ONLY the in-scope group's chip numeric;
    # every other group on the same page stays honestly unknown.
    _partial_live(monkeypatch)
    r = client.get(HUB_URL, headers=_basic())
    assert r.status_code == 200
    assert _amber_chip(18, _estate_total()) in r.text
    assert r.text.count("set live</span>") == 1
    assert r.text.count(UNKNOWN_CHIP) == _group_count() - 1
    # the out-of-scope chips carry the scope reason, never an assumption.
    assert "superbot-websites only" in r.text


# --- group_summary unit precision -------------------------------------------------


def _live_ok(services):
    return {
        "state": "ok", "reason": "", "token_set": True, "services": services,
        "fetched_at": "12:00:00 UTC", "cached": False,
        "project_name": "superbot-websites",
    }


def _estate_group():
    reg = envhub.load_registry()
    return next(g for g in reg["groups"] if g["id"] == "superbot-websites")


def test_group_summary_counts_set_vs_expected():
    cs = envhub.group_summary(_estate_group(), _live_ok([
        {"name": "control-plane",
         "variable_names": ["GITHUB_TOKEN", "SITE_PASSWORD"], "count": 2,
         "error": None},
    ]))
    assert cs["comparable"] is True
    assert cs["set_count"] == 2
    assert cs["total"] == _estate_total()
    assert cs["unknown_count"] == 0  # absent services are missing, known


def test_group_summary_per_service_error_counts_unknown_with_reason():
    cs = envhub.group_summary(_estate_group(), _live_ok([
        {"name": "control-plane", "variable_names": [], "count": 0,
         "error": "HTTP 500"},
    ]))
    assert cs["comparable"] is True  # the other services still compared
    assert cs["unknown_count"] == len(_committed_names("control-plane"))
    assert "could not be read" in cs["reason"]


def test_group_summary_out_of_scope_group_not_comparable():
    reg = envhub.load_registry()
    other = next(g for g in reg["groups"] if g["id"] != "superbot-websites")
    cs = envhub.group_summary(other, _live_ok([
        {"name": "control-plane", "variable_names": ["A"], "count": 1,
         "error": None},
    ]))
    assert cs["comparable"] is False
    assert "superbot-websites only" in cs["reason"]


@pytest.mark.parametrize("live", [
    None,
    {"state": "not-configured", "reason": "RAILWAY_TOKEN is not set", "services": []},
    {"state": "unavailable", "reason": "ConnectError: boom", "services": []},
])
def test_group_summary_no_live_truth_not_comparable(live):
    cs = envhub.group_summary(_estate_group(), live)
    assert cs["comparable"] is False
    assert cs["set_count"] == 0 and cs["known_total"] == 0
    assert cs["unknown_count"] == cs["total"] == _estate_total()


# --- NAMES NEVER VALUES (the hard rail) -----------------------------------------


def test_no_live_value_ever_reaches_the_page(client, monkeypatch):
    _partial_live(monkeypatch)
    r = client.get(HUB_URL, headers=_basic())
    assert r.status_code == 200
    assert _SENTINEL_VALUE not in r.text
    assert "test-project-token" not in r.text
    assert OWNER_PW not in r.text
