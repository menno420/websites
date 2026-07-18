"""Brute-force throttle on the /owner GET Basic-auth gate.

Security hardening: `app.owner.require_owner` — the dependency on EVERY gated
`/owner` GET — previously did only a constant-time password compare with no
rate-limiting, so failed HTTP-Basic guesses were unbounded (the caller only
ever saw 401, never a slowdown). It now records FAILED attempts against a
per-client-host sliding window (the SAME mechanism as the POST-action limiter,
`_sliding_window_hit`) and returns 429 with Retry-After once the ceiling is
crossed, instead of an endless 401 loop. A SUCCESSFUL auth is never throttled
and never consumes the failed-attempt budget; the same-origin/CSRF + rate-limit
floor on the state-changing POSTs is unchanged.
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
WRONG_PW = "not-the-password"
SAME_ORIGIN = "http://testserver"  # TestClient's own scheme+host


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


# --- (a) repeated FAILED /owner auth → eventually 429, not an endless 401 ----


def test_failed_get_auth_eventually_429_not_endless_401(client):
    """Wrong-password /owner GETs from one client are 401 up to the ceiling,
    then 429 — the loop is bounded, no longer an unlimited guessing gallery."""
    for i in range(owner.AUTH_FAIL_MAX_ATTEMPTS):
        r = client.get("/owner", headers=_basic(WRONG_PW))
        assert r.status_code == 401, f"attempt {i + 1} was {r.status_code}, expected 401"
    tripped = client.get("/owner", headers=_basic(WRONG_PW))
    assert tripped.status_code == 429
    # And it STAYS throttled — not a one-off that resets to 401 next call.
    again = client.get("/owner", headers=_basic(WRONG_PW))
    assert again.status_code == 429


def test_missing_credentials_also_throttled(client):
    """A no-Authorization GET is a failed attempt too and counts toward the
    same budget (an anonymous brute-forcer cannot evade by sending no header)."""
    for _ in range(owner.AUTH_FAIL_MAX_ATTEMPTS):
        assert client.get("/owner").status_code == 401
    assert client.get("/owner").status_code == 429


# --- (b) a correct-password auth still 200 and is NOT throttled --------------


def test_correct_password_not_throttled_after_failures(client):
    """Even after failures have tripped the throttle to 429 for wrong guesses,
    the CORRECT password still returns 200 — success is checked first and never
    consumes the failed-attempt budget."""
    for _ in range(owner.AUTH_FAIL_MAX_ATTEMPTS + 3):
        client.get("/owner", headers=_basic(WRONG_PW))
    # Wrong password is now throttled...
    assert client.get("/owner", headers=_basic(WRONG_PW)).status_code == 429
    # ...but the real owner still gets in.
    ok = client.get("/owner", headers=_basic(OWNER_PW))
    assert ok.status_code == 200


def test_many_successful_auths_never_throttled(client):
    """A legitimate owner browsing repeatedly is NEVER throttled — successful
    auths do not accumulate against the limiter at all."""
    for i in range(owner.AUTH_FAIL_MAX_ATTEMPTS * 2):
        r = client.get("/owner", headers=_basic(OWNER_PW))
        assert r.status_code == 200, f"successful GET {i + 1} was {r.status_code}"


# --- (c) the 429 carries the expected shape ---------------------------------


def test_get_auth_429_carries_retry_after(client):
    """The GET-gate 429 has a Retry-After header, like the POST-action 429."""
    for _ in range(owner.AUTH_FAIL_MAX_ATTEMPTS):
        client.get("/owner", headers=_basic(WRONG_PW))
    tripped = client.get("/owner", headers=_basic(WRONG_PW))
    assert tripped.status_code == 429
    assert "Retry-After" in tripped.headers
    assert int(tripped.headers["Retry-After"]) >= 1


# --- (d) the POST writeback floor is unchanged ------------------------------


def test_post_action_floor_unchanged(client):
    """The state-changing POST floor (auth → same-origin → per-route rate
    limit) is untouched: a same-origin authed POST runs, its own per-route
    limiter still trips at RATE_LIMIT_MAX_REQUESTS, and that budget is separate
    from the GET auth-fail budget (no cross-consumption)."""
    headers = {**_basic(), "Origin": SAME_ORIGIN}
    for i in range(owner.RATE_LIMIT_MAX_REQUESTS):
        r = client.post("/owner/actions/refresh", headers=headers)
        assert r.status_code == 200, f"POST {i + 1} was {r.status_code}"
    tripped = client.post("/owner/actions/refresh", headers=headers)
    assert tripped.status_code == 429
    assert "Retry-After" in tripped.headers


def test_get_failures_do_not_consume_post_budget(client):
    """Failed GET auth attempts fill the auth-fail bucket, NOT the POST route
    bucket — a separate namespace, so brute-forcing the GET gate cannot lock
    the owner out of the writeback POSTs (and vice-versa)."""
    for _ in range(owner.AUTH_FAIL_MAX_ATTEMPTS + 2):
        client.get("/owner", headers=_basic(WRONG_PW))
    # The GET gate is throttled for wrong guesses...
    assert client.get("/owner", headers=_basic(WRONG_PW)).status_code == 429
    # ...yet the authed same-origin POST still has its full per-route budget.
    r = client.post(
        "/owner/actions/refresh", headers={**_basic(), "Origin": SAME_ORIGIN}
    )
    assert r.status_code == 200
