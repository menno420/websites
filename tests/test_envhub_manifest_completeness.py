"""Offline tests for the manifest completeness diff (the slice-2 card's
captured idea, promoted): each env-var schema row on the gated
``GET /owner/environments-hub/manifest/{group}`` page is badged
**set-live** / **missing-live** against the live Railway variable-NAME
read (``railway.live_overview``), with an honest **unknown** whenever the
live truth is not knowable — the manifest becomes the owner's "what's left
to finish this environment" checklist.

Held invariants:
- names present live → ``set live`` badge; absent → ``missing live``;
  Railway unreachable / token missing / per-service error → ``unknown``
  (visually distinct, NEVER a fabricated green/red) and the page still
  renders 200;
- a service absent from a SUCCESSFUL live project read is honestly
  missing-live (the service is not created yet — exactly the checklist);
- groups outside the project-scoped token's scope stay unknown, never
  assumed;
- NAMES NEVER VALUES: the client method used (``railway.live_overview`` →
  ``railway._names_only``) drops values at the client boundary — no Railway
  variable VALUE ever appears in the rendered HTML or in the annotated
  manifest data (pinned with a sentinel value in the mocked GraphQL layer);
- the route rides the exact /owner HTTP Basic gate (401 without creds /
  wrong password, 503 fail-closed when the password is unset);
- all tests are fully offline (``railway._graphql`` mocked, GitHub fetches
  canned).
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
MANIFEST_URL = "/owner/environments-hub/manifest/superbot-websites"

# Sentinel: the one value-shaped string in play — it exists ONLY inside the
# mocked GraphQL layer and must never survive past railway._names_only.
_SENTINEL_VALUE = "sekret-live-value-789"

SET_BADGE = '<span class="b ok">set live</span>'
MISSING_BADGE = '<span class="b bad">missing live</span>'
UNKNOWN_BADGE = '<span class="b unknown">unknown</span>'


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
    """All documented names across the four surfaces — derived from the
    registry so these pins track badge logic, not the inventory's size."""
    reg = envhub.load_registry()
    estate = next(g for g in reg["groups"] if g["id"] == "superbot-websites")
    return sum(len(s["variable_names"]) for s in estate["surfaces"])


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


def _mixed_live(monkeypatch):
    """Token set + mocked live read: control-plane fully set, botsite
    partially set (plus a live-only extra name), dashboard fully set,
    review ABSENT from the live project (not created yet)."""
    monkeypatch.setattr(config, "RAILWAY_TOKEN", "test-project-token")
    monkeypatch.setattr(
        railway,
        "_graphql",
        _fake_graphql(
            names_by_service_id={
                "s1": _committed_names("control-plane"),          # all 10 set
                "s2": ["SITE_JSON_URL", "PORT", "EXTRA_LIVE_ONLY"],  # 2 of 5
                "s3": _committed_names("dashboard"),               # all 6 set
            },
            service_nodes=[
                ("s1", "control-plane"), ("s2", "botsite"), ("s3", "dashboard"),
            ],
        ),
    )


# --- gate behavior (pinned here too — the diff must never widen exposure) ------


def test_gate_401_without_creds_and_wrong_password(client):
    assert client.get(MANIFEST_URL).status_code == 401
    assert client.get(MANIFEST_URL, headers=_basic("wrong")).status_code == 401


def test_gate_fails_closed_when_password_unset(client, monkeypatch):
    monkeypatch.setattr(config, "SITE_PASSWORD", "")
    assert client.get(MANIFEST_URL, headers=_basic()).status_code == 503


# --- badge correctness through the route ---------------------------------------


def test_all_names_present_renders_all_set_live(client, monkeypatch):
    monkeypatch.setattr(config, "RAILWAY_TOKEN", "test-project-token")
    all_names = {
        f"s{i}": _committed_names(sid)
        for i, sid in enumerate(
            ("control-plane", "botsite", "dashboard", "review"), start=1
        )
    }
    monkeypatch.setattr(
        railway,
        "_graphql",
        _fake_graphql(
            all_names,
            [("s1", "control-plane"), ("s2", "botsite"),
             ("s3", "dashboard"), ("s4", "review")],
        ),
    )
    r = client.get(MANIFEST_URL, headers=_basic())
    assert r.status_code == 200
    total = sum(len(v) for v in all_names.values())
    assert r.text.count(SET_BADGE) == total
    assert MISSING_BADGE not in r.text
    assert f"{total}/{total} set live" in r.text


def test_mixed_present_absent_and_missing_service(client, monkeypatch):
    _mixed_live(monkeypatch)
    r = client.get(MANIFEST_URL, headers=_basic())
    assert r.status_code == 200
    # control-plane + dashboard fully set, botsite 2 set (SITE_JSON_URL, PORT).
    set_count = (
        len(_committed_names("control-plane"))
        + 2
        + len(_committed_names("dashboard"))
    )
    assert r.text.count(SET_BADGE) == set_count
    # botsite's remaining names missing + ALL review names (not created yet).
    missing_count = (
        len(_committed_names("botsite")) - 2 + len(_committed_names("review"))
    )
    assert r.text.count(MISSING_BADGE) == missing_count
    assert f"{set_count}/{_estate_total()} set live" in r.text
    # the absent service carries the honest not-created-yet note.
    assert "not created yet" in r.text
    # live-only extra names are the hub's business, not a schema row here.
    assert "EXTRA_LIVE_ONLY" not in r.text


def test_unreachable_railway_renders_honest_unknown(client, monkeypatch):
    monkeypatch.setattr(config, "RAILWAY_TOKEN", "test-project-token")

    async def fake(query, variables=None):
        return {"ok": False, "data": None, "error": "ConnectError: boom"}

    monkeypatch.setattr(railway, "_graphql", fake)
    r = client.get(MANIFEST_URL, headers=_basic())
    assert r.status_code == 200  # the page still renders
    assert SET_BADGE not in r.text and MISSING_BADGE not in r.text
    assert UNKNOWN_BADGE in r.text
    assert "live status unknown" in r.text
    assert "ConnectError: boom" in r.text  # the exact reason, surfaced


def test_token_missing_renders_honest_unknown(client):
    # fixture default: RAILWAY_TOKEN unset → not-configured, never red/green.
    r = client.get(MANIFEST_URL, headers=_basic())
    assert r.status_code == 200
    assert SET_BADGE not in r.text and MISSING_BADGE not in r.text
    assert "live status unknown" in r.text
    assert "RAILWAY_TOKEN is not set" in r.text


def test_out_of_scope_group_stays_unknown_never_assumed(client, monkeypatch):
    # A perfectly healthy live read must not paint OTHER groups green/red —
    # the project-scoped token sees superbot-websites only.
    _mixed_live(monkeypatch)
    for gid in ("reliable-grace", "github-actions", "claude-cloud",
                "superbot-mineverse"):
        r = client.get(
            f"/owner/environments-hub/manifest/{gid}", headers=_basic()
        )
        assert r.status_code == 200
        assert SET_BADGE not in r.text and MISSING_BADGE not in r.text


# --- annotate_completeness unit precision --------------------------------------


def _manifest_with(live):
    m = envhub.manifest("superbot-websites")
    envhub.annotate_completeness(m, live)
    return m


def _live_ok(services):
    return {
        "state": "ok", "reason": "", "token_set": True, "services": services,
        "fetched_at": "12:00:00 UTC", "cached": False,
        "project_name": "superbot-websites",
    }


def test_annotate_rows_set_and_missing_per_name():
    m = _manifest_with(_live_ok([
        {"name": "control-plane",
         "variable_names": ["GITHUB_TOKEN", "SITE_PASSWORD"], "count": 2,
         "error": None},
    ]))
    cp = next(s for s in m["services"] if s["surface"]["id"] == "control-plane")
    assert cp["live"]["by_name"]["GITHUB_TOKEN"] == envhub.LIVE_SET
    assert cp["live"]["by_name"]["SITE_PASSWORD"] == envhub.LIVE_SET
    assert cp["live"]["by_name"]["RAILWAY_TOKEN"] == envhub.LIVE_MISSING
    assert cp["live"]["set_count"] == 2
    # botsite/dashboard/review absent from the live read → missing, known.
    review = next(s for s in m["services"] if s["surface"]["id"] == "review")
    assert set(review["live"]["by_name"].values()) == {envhub.LIVE_MISSING}
    assert "not created yet" in review["live"]["note"]
    assert m["completeness"]["comparable"] is True
    assert m["completeness"]["set_count"] == 2
    assert m["completeness"]["total"] == _estate_total()
    assert m["completeness"]["unknown_count"] == 0


def test_annotate_per_service_error_stays_unknown():
    m = _manifest_with(_live_ok([
        {"name": "control-plane", "variable_names": [], "count": 0,
         "error": "HTTP 500"},
    ]))
    cp = next(s for s in m["services"] if s["surface"]["id"] == "control-plane")
    assert set(cp["live"]["by_name"].values()) == {envhub.LIVE_UNKNOWN}
    assert "HTTP 500" in cp["live"]["note"]
    # the errored service's rows are excluded from the known totals.
    c = m["completeness"]
    assert c["unknown_count"] == len(cp["schema"])
    assert c["known_total"] == c["total"] - len(cp["schema"])


@pytest.mark.parametrize("live", [
    None,
    {"state": "not-configured", "reason": "RAILWAY_TOKEN is not set", "services": []},
    {"state": "unavailable", "reason": "ConnectError: boom", "services": []},
])
def test_annotate_no_live_truth_means_all_unknown(live):
    m = _manifest_with(live)
    for svc in m["services"]:
        assert set(svc["live"]["by_name"].values()) <= {envhub.LIVE_UNKNOWN}
    c = m["completeness"]
    assert c["comparable"] is False
    assert c["set_count"] == 0 and c["known_total"] == 0
    assert c["unknown_count"] == c["total"] == _estate_total()


def test_annotate_other_group_unknown_even_on_healthy_read():
    m = envhub.manifest("reliable-grace")
    envhub.annotate_completeness(
        m, _live_ok([{"name": "control-plane",
                      "variable_names": ["A"], "count": 1, "error": None}])
    )
    assert m["completeness"]["comparable"] is False
    assert "superbot-websites only" in m["completeness"]["reason"]


def test_annotate_leaves_the_copyable_plan_untouched():
    """The plan artifacts stay pure committed-registry output — completeness
    is a page annotation, never part of the copyable plan."""
    plain = envhub.manifest("superbot-websites")
    annotated = _manifest_with(_live_ok([
        {"name": "control-plane", "variable_names": ["GITHUB_TOKEN"],
         "count": 1, "error": None},
    ]))
    assert annotated["commands_text"] == plain["commands_text"]
    assert annotated["manifest_json"] == plain["manifest_json"]
    assert "set-live" not in annotated["manifest_json"]


# --- NAMES NEVER VALUES (the hard rail) -----------------------------------------


def test_client_boundary_drops_values_names_only():
    """Pin the client method the diff consumes: railway._names_only strips
    Railway's name→value map down to sorted NAMES at the client boundary."""
    assert railway._names_only({"B": _SENTINEL_VALUE, "A": _SENTINEL_VALUE}) == ["A", "B"]
    assert railway._names_only(None) == []
    assert railway._names_only("not-a-map") == []


def test_no_live_value_ever_reaches_the_page_or_the_data(client, monkeypatch):
    _mixed_live(monkeypatch)
    r = client.get(MANIFEST_URL, headers=_basic())
    assert r.status_code == 200
    assert _SENTINEL_VALUE not in r.text
    assert "test-project-token" not in r.text
    assert OWNER_PW not in r.text
    # ... and never into the annotated manifest structure either.
    async def _data():
        live = await railway.live_overview(refresh=True)
        m = envhub.manifest("superbot-websites")
        envhub.annotate_completeness(m, live)
        return m
    m = asyncio.run(_data())
    assert _SENTINEL_VALUE not in repr(m)
