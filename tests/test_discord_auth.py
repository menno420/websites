"""Discord OAuth owner login flow (ASK-0001 / ORDER 035).

Covers the NON-gated login half built on the control-plane: `oauth_configured`,
the stdlib signed session + CSRF-state helpers, and the three routes
(`/owner/login`, `/owner/auth/callback`, `/owner/logout`) — all without live
Discord (the `exchange_code`/`fetch_user` seams are monkeypatched). Also pins
the fail-closed gate wiring: env-unset keeps `/owner` locked (503) and names the
opening owner action; a valid session authorizes `/owner`; the existing
HTTP-Basic SITE_PASSWORD path still works (regression).
"""

import base64
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app import config, discord_auth, github, owner  # noqa: E402
from app.main import app  # noqa: E402

OWNER_ID = "123456789012345678"
NON_OWNER_ID = "999888777666555444"
CLIENT_ID = "test-client-id"

_DISCORD_ENV = {
    "DISCORD_CLIENT_ID": CLIENT_ID,
    "DISCORD_CLIENT_SECRET": "test-client-secret",
    "OWNER_DISCORD_ID": OWNER_ID,
    "OWNER_SESSION_SECRET": "test-session-secret-please-change",
}


def _basic(pw: str, user: str = "owner") -> dict:
    token = base64.b64encode(f"{user}:{pw}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


@pytest.fixture(autouse=True)
def _reset(monkeypatch):
    """Every test starts from a clean auth slate: no Discord env, no
    SITE_PASSWORD, GitHub calls mocked offline, rate limits reset."""
    for name in _DISCORD_ENV:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.delenv("DISCORD_REDIRECT_URI", raising=False)
    monkeypatch.setattr(config, "SITE_PASSWORD", "")
    monkeypatch.setattr(github, "clear_cache", lambda: 0)

    async def fake_get(url, refresh=False, raw=False):
        return {
            "ok": False, "status": 0, "data": None,
            "error": "offline test", "fetched_at": "", "cached": False,
            "url": url,
        }

    monkeypatch.setattr(github, "_get", fake_get)
    owner.reset_rate_limits()
    yield
    owner.reset_rate_limits()


def _configure(monkeypatch):
    for name, value in _DISCORD_ENV.items():
        monkeypatch.setenv(name, value)


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


# --------------------------------------------------------------------------- #
# env unset — fail closed, honest login page, locked /owner
# --------------------------------------------------------------------------- #
def test_oauth_not_configured_when_env_unset():
    assert discord_auth.oauth_configured() is False


def test_login_page_200_names_owner_action_when_unconfigured(client):
    r = client.get("/owner/login")
    assert r.status_code == 200
    body = r.text
    assert "not configured" in body.lower()
    # names the opening owner actions (ASK-0002 redirect URI + env, ASK-0003)
    assert "ASK-0002" in body and "DISCORD_CLIENT_ID" in body
    assert "/owner/auth/callback" in body  # the redirect URI it asks the owner to add


def test_owner_locked_503_with_neither_password_nor_session(client):
    r = client.get("/owner")
    assert r.status_code == 503
    # the lock names the opening owner action rather than a bare failure
    assert "/owner/login" in r.text or "DISCORD_CLIENT_ID" in r.text


# --------------------------------------------------------------------------- #
# configured — /owner/login redirects to Discord and sets the state cookie
# --------------------------------------------------------------------------- #
def test_login_redirects_to_discord_when_configured(client, monkeypatch):
    _configure(monkeypatch)
    r = client.get("/owner/login", follow_redirects=False)
    assert r.status_code == 302
    loc = r.headers["location"]
    assert loc.startswith("https://discord.com/api/oauth2/authorize")
    q = parse_qs(urlparse(loc).query)
    assert q["client_id"] == [CLIENT_ID]
    assert q["scope"] == ["identify"]
    assert q["response_type"] == ["code"]
    assert q["state"] and q["state"][0]
    assert discord_auth.STATE_COOKIE in r.cookies


# --------------------------------------------------------------------------- #
# callback — happy path, non-owner, CSRF
# --------------------------------------------------------------------------- #
def _install_seams(monkeypatch, user_id):
    async def fake_exchange(code, redirect_uri):
        return {"access_token": "fake-token"}

    async def fake_fetch(access_token):
        return {"id": user_id, "username": "someone"}

    monkeypatch.setattr(discord_auth, "exchange_code", fake_exchange)
    monkeypatch.setattr(discord_auth, "fetch_user", fake_fetch)


def _begin_login(client):
    """Drive /owner/login and return the state param that matches the cookie."""
    r = client.get("/owner/login", follow_redirects=False)
    assert r.status_code == 302
    return parse_qs(urlparse(r.headers["location"]).query)["state"][0]


def test_callback_happy_path_sets_session_and_authorizes_owner(client, monkeypatch):
    _configure(monkeypatch)
    _install_seams(monkeypatch, OWNER_ID)
    state = _begin_login(client)
    cb = client.get(
        f"/owner/auth/callback?code=abc&state={state}", follow_redirects=False
    )
    assert cb.status_code == 302
    assert cb.headers["location"] == "/owner"
    assert discord_auth.SESSION_COOKIE in cb.cookies
    # the minted session cookie now authorizes the gated /owner board
    r = client.get("/owner")
    assert r.status_code == 200


def test_callback_non_owner_id_403_no_session(client, monkeypatch):
    _configure(monkeypatch)
    _install_seams(monkeypatch, NON_OWNER_ID)
    state = _begin_login(client)
    cb = client.get(
        f"/owner/auth/callback?code=abc&state={state}", follow_redirects=False
    )
    assert cb.status_code == 403
    assert discord_auth.SESSION_COOKIE not in cb.cookies
    # and no session leaked into the jar → /owner stays locked
    assert client.get("/owner").status_code in (401, 503)


def test_callback_missing_state_rejected_csrf(client, monkeypatch):
    _configure(monkeypatch)
    _install_seams(monkeypatch, OWNER_ID)
    _begin_login(client)  # sets a real state cookie
    # ...but the callback carries no state param → CSRF check fails
    cb = client.get("/owner/auth/callback?code=abc", follow_redirects=False)
    assert cb.status_code == 400
    assert discord_auth.SESSION_COOKIE not in cb.cookies


def test_callback_wrong_state_rejected_csrf(client, monkeypatch):
    _configure(monkeypatch)
    _install_seams(monkeypatch, OWNER_ID)
    _begin_login(client)
    cb = client.get(
        "/owner/auth/callback?code=abc&state=forged-state-value",
        follow_redirects=False,
    )
    assert cb.status_code == 400
    assert discord_auth.SESSION_COOKIE not in cb.cookies


def test_callback_unconfigured_is_locked_503(client):
    # no _configure → oauth not configured
    cb = client.get(
        "/owner/auth/callback?code=abc&state=whatever", follow_redirects=False
    )
    assert cb.status_code == 503


# --------------------------------------------------------------------------- #
# session cookie helpers — sign / verify / expiry / tamper
# --------------------------------------------------------------------------- #
def test_session_roundtrip_valid(monkeypatch):
    _configure(monkeypatch)
    token = discord_auth.make_session(OWNER_ID)
    assert token
    assert discord_auth.verify_session(token) == OWNER_ID


def test_session_tampered_returns_none(monkeypatch):
    _configure(monkeypatch)
    token = discord_auth.make_session(OWNER_ID)
    payload_b64, _, sig_b64 = token.partition(".")
    # flip the payload but keep the old signature → signature mismatch
    forged = discord_auth._b64e(f"{NON_OWNER_ID}|0|9999999999".encode())
    assert discord_auth.verify_session(f"{forged}.{sig_b64}") is None


def test_session_expired_returns_none(monkeypatch):
    _configure(monkeypatch)
    # issued far in the past so issued + TTL is already elapsed
    stale = discord_auth.make_session(
        OWNER_ID, now=1_000_000  # ~1970; expiry long gone
    )
    assert discord_auth.verify_session(stale) is None


def test_session_without_secret_cannot_be_minted_or_verified(monkeypatch):
    # secret unset → no token can be minted, and any raw verifies to None
    assert discord_auth.make_session(OWNER_ID) == ""
    monkeypatch.setenv("OWNER_SESSION_SECRET", "s")
    real = discord_auth.make_session(OWNER_ID)
    monkeypatch.delenv("OWNER_SESSION_SECRET", raising=False)
    assert discord_auth.verify_session(real) is None


def test_tampered_cookie_leaves_owner_locked(client, monkeypatch):
    _configure(monkeypatch)
    r = client.get(
        "/owner", cookies={discord_auth.SESSION_COOKIE: "not.a.valid.token"}
    )
    # no valid session, no SITE_PASSWORD → 401 (bad creds; something configured)
    assert r.status_code == 401


# --------------------------------------------------------------------------- #
# logout — clears the cookie, CSRF-protected
# --------------------------------------------------------------------------- #
def test_logout_clears_cookie_same_origin(client, monkeypatch):
    _configure(monkeypatch)
    _install_seams(monkeypatch, OWNER_ID)
    state = _begin_login(client)
    client.get(f"/owner/auth/callback?code=abc&state={state}", follow_redirects=False)
    assert client.get("/owner").status_code == 200  # logged in
    r = client.post(
        "/owner/logout",
        headers={"Origin": "http://testserver"},
        follow_redirects=False,
    )
    assert r.status_code == 302
    assert r.headers["location"] == "/"
    # the Set-Cookie deletion clears the jar → /owner locks again
    assert client.get("/owner").status_code in (401, 503)


def test_logout_without_origin_rejected(client, monkeypatch):
    _configure(monkeypatch)
    r = client.post("/owner/logout", follow_redirects=False)
    assert r.status_code == 403


def test_logout_cross_origin_rejected(client, monkeypatch):
    _configure(monkeypatch)
    r = client.post(
        "/owner/logout",
        headers={"Origin": "https://evil.example"},
        follow_redirects=False,
    )
    assert r.status_code == 403


# --------------------------------------------------------------------------- #
# regression — the existing HTTP-Basic SITE_PASSWORD gate still authorizes
# --------------------------------------------------------------------------- #
def test_site_password_basic_auth_still_authorizes(client, monkeypatch):
    monkeypatch.setattr(config, "SITE_PASSWORD", "the-owner-pw")
    r = client.get("/owner", headers=_basic("the-owner-pw"))
    assert r.status_code == 200


def test_site_password_wrong_still_401(client, monkeypatch):
    monkeypatch.setattr(config, "SITE_PASSWORD", "the-owner-pw")
    r = client.get("/owner", headers=_basic("nope"))
    assert r.status_code == 401
