"""Offline tests for the code-referenced-vs-declared env-var NAME drift check
on the gated /owner/environments page (app/codedrift.py, backlog item B6,
owner-decided Q1=a: a contained, names-only, static check).

Held invariants:
- ``compute_drift`` is a pure set-diff: referenced-but-undeclared and
  declared-but-unreferenced, both directions, and the empty/in-sync case;
- ``annotate`` applies the platform carve-outs consistently with
  app/envdrift.py — ``PORT`` (declared-but-unreferenced by design) and the
  Railway/build-injected ``GIT_SHA``/``RAILWAY_GIT_COMMIT_SHA``/other
  ``RAILWAY_*`` (referenced-but-undeclared by design) are INFORMATIONAL, never
  counted as drift; ``RAILWAY_TOKEN`` is the owner-set exception;
- a missing snapshot / a service absent from it is honest UNKNOWN with the
  reason, never a fabricated match;
- the page renders 200 behind the /owner gate with NAMES ONLY — no value-
  looking string leaks;
- against the REAL committed snapshot + manifest the feature honestly surfaces
  the current genuine finds and shows the in-sync services green.

No network: the live-Railway read is left not-configured (the code-drift half
is fully static and independent of it).
"""

import base64
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app import codedrift, config, github, railway  # noqa: E402
from app.main import app  # noqa: E402

OWNER_PW = "test-owner-pw"


def _basic(pw: str = OWNER_PW, user: str = "owner") -> dict:
    token = base64.b64encode(f"{user}:{pw}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


@pytest.fixture()
def client(monkeypatch):
    """Offline authed-ready client: password set, GitHub + live Railway off."""
    monkeypatch.setattr(config, "SITE_PASSWORD", OWNER_PW)
    monkeypatch.setattr(config, "RAILWAY_TOKEN", "")  # live half not-configured

    async def fake_get(url, refresh=False, raw=False):
        return {
            "ok": False, "status": 0, "data": None,
            "error": "offline test", "fetched_at": "", "cached": False, "url": url,
        }

    monkeypatch.setattr(github, "_get", fake_get)
    with TestClient(app) as c:
        yield c


# --- (a)(b)(c) the pure drift function ---------------------------------------


def test_referenced_but_undeclared_is_flagged():
    """A name the code reads but the manifest omits → referenced-but-undeclared."""
    out = codedrift.compute_drift(
        referenced=["GITHUB_TOKEN", "NEW_SECRET"],
        declared=["GITHUB_TOKEN"],
    )
    assert out["referenced_but_undeclared"] == ["NEW_SECRET"]
    assert out["declared_but_unreferenced"] == []


def test_declared_but_unreferenced_is_flagged():
    """A name the manifest lists but no code reads → declared-but-unreferenced."""
    out = codedrift.compute_drift(
        referenced=["GITHUB_TOKEN"],
        declared=["GITHUB_TOKEN", "STALE_VAR"],
    )
    assert out["declared_but_unreferenced"] == ["STALE_VAR"]
    assert out["referenced_but_undeclared"] == []


def test_no_drift_is_empty_both_directions():
    """Identical sets → no drift (the in-sync case), order-independent."""
    out = codedrift.compute_drift(
        referenced=["B_VAR", "A_VAR"],
        declared=["A_VAR", "B_VAR"],
    )
    assert out == {"referenced_but_undeclared": [], "declared_but_unreferenced": []}


# --- annotate: classification + carve-outs -----------------------------------


def _overview(referenced_by_service, declared_by_service):
    """A minimal railway.overview()-shaped payload + a stubbed snapshot."""
    data = {
        "services": [
            {"name": name, "env_vars": [{"name": n} for n in declared]}
            for name, declared in declared_by_service.items()
        ]
    }
    return data, {"ok": True, "services": referenced_by_service, "error": ""}


def test_annotate_flags_genuine_drift_both_directions(monkeypatch):
    data, snap = _overview(
        referenced_by_service={"svc": ["READS_ONLY", "SHARED"]},
        declared_by_service={"svc": ["SHARED", "DECLARED_ONLY"]},
    )
    monkeypatch.setattr(codedrift, "load_coderefs", lambda: snap)
    codedrift.annotate(data)
    cd = data["services"][0]["code_drift"]
    assert cd["state"] == "drift"
    assert cd["referenced_but_undeclared"] == ["READS_ONLY"]
    assert cd["declared_but_unreferenced"] == ["DECLARED_ONLY"]
    assert data["code_drift"]["state"] == "drift"
    assert data["code_drift"]["drifted_services"] == ["svc"]


def test_annotate_platform_injected_referenced_is_informational(monkeypatch):
    """GIT_SHA / RAILWAY_GIT_COMMIT_SHA / RAILWAY_* the code reads but the owner
    never declares are informational, never drift (RAILWAY_TOKEN excepted)."""
    data, snap = _overview(
        referenced_by_service={
            "svc": ["GIT_SHA", "RAILWAY_GIT_COMMIT_SHA", "RAILWAY_REPLICA_ID", "SHARED"]
        },
        declared_by_service={"svc": ["SHARED"]},
    )
    monkeypatch.setattr(codedrift, "load_coderefs", lambda: snap)
    codedrift.annotate(data)
    cd = data["services"][0]["code_drift"]
    assert cd["state"] == "in-sync"
    assert cd["referenced_but_undeclared"] == []
    assert set(cd["informational_referenced"]) == {
        "GIT_SHA", "RAILWAY_GIT_COMMIT_SHA", "RAILWAY_REPLICA_ID",
    }


def test_annotate_railway_token_referenced_is_real_drift(monkeypatch):
    """RAILWAY_TOKEN is owner-set — referenced-but-undeclared RAILWAY_TOKEN IS
    drift, the deliberate prefix exception (mirrors envdrift)."""
    data, snap = _overview(
        referenced_by_service={"svc": ["RAILWAY_TOKEN"]},
        declared_by_service={"svc": []},
    )
    monkeypatch.setattr(codedrift, "load_coderefs", lambda: snap)
    codedrift.annotate(data)
    cd = data["services"][0]["code_drift"]
    assert cd["state"] == "drift"
    assert cd["referenced_but_undeclared"] == ["RAILWAY_TOKEN"]


def test_annotate_port_declared_is_informational(monkeypatch):
    """PORT is launch-command consumed, never a Python read — declared-but-
    unreferenced by design, so informational, not stale drift."""
    data, snap = _overview(
        referenced_by_service={"svc": ["SHARED"]},
        declared_by_service={"svc": ["SHARED", "PORT"]},
    )
    monkeypatch.setattr(codedrift, "load_coderefs", lambda: snap)
    codedrift.annotate(data)
    cd = data["services"][0]["code_drift"]
    assert cd["state"] == "in-sync"
    assert cd["declared_but_unreferenced"] == []
    assert cd["informational_declared"] == ["PORT"]


def test_annotate_missing_snapshot_is_unknown_with_reason(monkeypatch):
    """No committed snapshot → every service unknown WITH the reason, never a
    fabricated match (fail-soft)."""
    data, _ = _overview(
        referenced_by_service={},
        declared_by_service={"svc": ["A_VAR"]},
    )
    monkeypatch.setattr(
        codedrift, "load_coderefs",
        lambda: {"ok": False, "services": {}, "error": "boom"},
    )
    codedrift.annotate(data)
    assert data["services"][0]["code_drift"]["state"] == "unknown"
    assert "boom" in data["services"][0]["code_drift"]["reason"]
    assert data["code_drift"]["state"] == "unknown"
    assert data["code_drift"]["comparable"] is False


def test_annotate_service_absent_from_snapshot_is_unknown(monkeypatch):
    data, snap = _overview(
        referenced_by_service={"other": ["X"]},
        declared_by_service={"svc": ["A_VAR"]},
    )
    monkeypatch.setattr(codedrift, "load_coderefs", lambda: snap)
    codedrift.annotate(data)
    assert data["services"][0]["code_drift"]["state"] == "unknown"
    assert "no code-reference entry" in data["services"][0]["code_drift"]["reason"]


def test_load_coderefs_failsoft_on_missing_file(monkeypatch, tmp_path):
    monkeypatch.setattr(codedrift, "SNAPSHOT_PATH", tmp_path / "nope.json")
    out = codedrift.load_coderefs()
    assert out["ok"] is False
    assert out["services"] == {}
    assert "not found" in out["error"]


# --- (d) the route renders 200, names only -----------------------------------


def test_route_renders_code_drift_section(client):
    r = client.get("/owner/environments", headers=_basic())
    assert r.status_code == 200
    assert "code ↔ declared name drift" in r.text


def test_route_requires_auth(client):
    assert client.get("/owner/environments").status_code == 401


def test_route_leaks_no_value_looking_strings(client, monkeypatch):
    """The code-drift payload carries NAMES ONLY — a sentinel value planted in
    the environment must never reach the annotated payload or the HTML (the
    scan records name strings, never reads a value)."""
    sentinel = "sekret-code-drift-value-999"
    # Plant the sentinel as the *value* of a real referenced var; the static
    # snapshot holds only the NAME, so the value can never surface.
    monkeypatch.setenv("GITHUB_TOKEN", sentinel)
    monkeypatch.setenv("SITE_PASSWORD", sentinel)  # value, not config.SITE_PASSWORD
    r = client.get("/owner/environments", headers=_basic())
    assert r.status_code == 200
    assert sentinel not in r.text


def test_annotated_payload_holds_only_env_name_shaped_strings(monkeypatch):
    """Defense in depth: every string the code-drift annotation adds to the
    payload is an env-var NAME (upper-snake), never a value."""
    import re
    data, snap = _overview(
        referenced_by_service={"svc": ["A_VAR", "GIT_SHA", "B_VAR"]},
        declared_by_service={"svc": ["A_VAR", "PORT", "STALE_VAR"]},
    )
    monkeypatch.setattr(codedrift, "load_coderefs", lambda: snap)
    codedrift.annotate(data)
    cd = data["services"][0]["code_drift"]
    name_lists = (
        cd["referenced_but_undeclared"]
        + cd["declared_but_unreferenced"]
        + cd["informational_referenced"]
        + cd["informational_declared"]
    )
    assert name_lists  # non-empty for this fixture
    for name in name_lists:
        assert re.match(r"^[A-Z][A-Z0-9_]+$", name), name


# --- live-data sanity: the feature's real finds ------------------------------


def test_real_snapshot_surfaces_current_genuine_finds():
    """Against the REAL committed snapshot + manifest, the feature must flag the
    known genuine referenced-but-undeclared finds and leave the in-sync
    services green — a guard that the wiring works on live data, not just
    fixtures. Update this if the manifest is corrected."""
    import asyncio

    data = asyncio.run(railway.overview(refresh=True))
    # railway.overview may attempt the live half; force it not-configured so the
    # test is deterministic and offline.
    data["live"] = {"state": "not-configured", "reason": "offline test", "services": []}
    codedrift.annotate(data)
    by_name = {s["name"]: s["code_drift"] for s in data["services"]}

    assert "WRITEBACK_BRANCH_PREFIX" in by_name["control-plane"]["referenced_but_undeclared"]
    assert "ARCADE_JSON_URL" in by_name["dashboard"]["referenced_but_undeclared"]
    # botsite / review reference only declared + platform-injected names.
    assert by_name["botsite"]["state"] == "in-sync"
    assert by_name["review"]["state"] == "in-sync"
    # The injected metadata is classified informational, never counted.
    assert "GIT_SHA" in by_name["botsite"]["informational_referenced"]
    assert "PORT" in by_name["botsite"]["informational_declared"]
