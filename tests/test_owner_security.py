"""CSRF (strict same-origin) + rate-limit tests for the /owner POST actions.

ORDER 013 (control/inbox.md): the state-changing /owner routes previously rode
HTTP Basic alone. `app.owner.require_owner_action` now layers, in order:
auth (401/503) → strict same-origin Origin/Referer check (403) → in-process
sliding-window rate limit (429). Documented strict choice: a POST carrying
NEITHER Origin NOR Referer is rejected 403 — browsers always send Origin on
POST, so only header-less non-browser callers are affected.
"""

import base64
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app import config, github, owner  # noqa: E402
from app.main import app  # noqa: E402

OWNER_PW = "test-owner-pw"
SAME_ORIGIN = "http://testserver"  # TestClient's own scheme+host
CROSS_ORIGIN = "https://evil.example"


def _basic(pw: str = OWNER_PW, user: str = "owner") -> dict:
    token = base64.b64encode(f"{user}:{pw}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


@pytest.fixture(autouse=True)
def _reset_rate_limits():
    """Isolate the module-level limiter state so the suite is deterministic."""
    owner.reset_rate_limits()
    yield
    owner.reset_rate_limits()


@pytest.fixture()
def client(monkeypatch):
    """Authed-ready offline client: password set, GitHub + cache calls mocked."""
    monkeypatch.setattr(config, "SITE_PASSWORD", OWNER_PW)
    monkeypatch.setattr(github, "clear_cache", lambda: 0)

    async def fake_get(url, refresh=False, raw=False):
        return {
            "ok": False, "status": 0, "data": None,
            "error": "offline test", "fetched_at": "", "cached": False,
            "url": url,
        }

    monkeypatch.setattr(github, "_get", fake_get)
    with TestClient(app) as c:
        yield c


def test_same_origin_post_accepted(client):
    """Correct Origin header → the action runs (no 403, no 429)."""
    r = client.post(
        "/owner/actions/refresh",
        headers={**_basic(), "Origin": SAME_ORIGIN},
    )
    assert r.status_code == 200


def test_cross_origin_post_rejected(client):
    """Origin from another host → 403, for every state-changing route."""
    r = client.post(
        "/owner/actions/refresh",
        headers={**_basic(), "Origin": CROSS_ORIGIN},
    )
    assert r.status_code == 403
    r2 = client.post(
        "/owner/actions/rerun-ci",
        data={"repo": "superbot"},
        headers={**_basic(), "Origin": CROSS_ORIGIN},
    )
    assert r2.status_code == 403


def test_missing_origin_and_referer_rejected(client):
    """Neither Origin nor Referer → 403 (documented strict choice)."""
    r = client.post("/owner/actions/refresh", headers=_basic())
    assert r.status_code == 403
    assert "missing Origin/Referer" in r.text


def test_missing_origin_same_origin_referer_accepted(client):
    """No Origin, but a same-origin Referer → accepted."""
    r = client.post(
        "/owner/actions/refresh",
        headers={**_basic(), "Referer": f"{SAME_ORIGIN}/owner"},
    )
    assert r.status_code == 200


def test_cross_origin_referer_rejected(client):
    """No Origin, cross-origin Referer → 403."""
    r = client.post(
        "/owner/actions/refresh",
        headers={**_basic(), "Referer": f"{CROSS_ORIGIN}/owner"},
    )
    assert r.status_code == 403


def test_origin_wins_over_referer(client):
    """A cross-origin Origin is rejected even if the Referer looks same-origin."""
    r = client.post(
        "/owner/actions/refresh",
        headers={
            **_basic(),
            "Origin": CROSS_ORIGIN,
            "Referer": f"{SAME_ORIGIN}/owner",
        },
    )
    assert r.status_code == 403


def test_rate_limit_trips_with_429(client):
    """Request N+1 inside the window → 429 with Retry-After; auth/CSRF-passing."""
    headers = {**_basic(), "Origin": SAME_ORIGIN}
    for i in range(owner.RATE_LIMIT_MAX_REQUESTS):
        r = client.post("/owner/actions/refresh", headers=headers)
        assert r.status_code == 200, f"request {i + 1} unexpectedly {r.status_code}"
    tripped = client.post("/owner/actions/refresh", headers=headers)
    assert tripped.status_code == 429
    assert "Retry-After" in tripped.headers


def test_rate_limit_is_per_route(client, monkeypatch):
    """Tripping /refresh does not exhaust /rerun-ci (keyed per route path)."""

    async def fake_rerun(repo, branch="main"):
        return {"ok": True, "url": None, "message": "mocked"}

    monkeypatch.setattr(github, "rerun_latest_failed", fake_rerun)
    headers = {**_basic(), "Origin": SAME_ORIGIN}
    for _ in range(owner.RATE_LIMIT_MAX_REQUESTS):
        assert client.post(
            "/owner/actions/refresh", headers=headers
        ).status_code == 200
    assert client.post(
        "/owner/actions/refresh", headers=headers
    ).status_code == 429
    r = client.post(
        "/owner/actions/rerun-ci", data={"repo": "superbot"}, headers=headers
    )
    assert r.status_code == 200


def test_unauthed_cross_origin_still_401(client):
    """Auth precedes CSRF: no credentials → 401 even with a bad Origin."""
    r = client.post(
        "/owner/actions/refresh", headers={"Origin": CROSS_ORIGIN}
    )
    assert r.status_code == 401


def test_rejected_requests_do_not_consume_rate_budget(client):
    """403 cross-origin spam does not exhaust the limiter for the real owner."""
    for _ in range(owner.RATE_LIMIT_MAX_REQUESTS + 2):
        assert client.post(
            "/owner/actions/refresh",
            headers={**_basic(), "Origin": CROSS_ORIGIN},
        ).status_code == 403
    r = client.post(
        "/owner/actions/refresh",
        headers={**_basic(), "Origin": SAME_ORIGIN},
    )
    assert r.status_code == 200
