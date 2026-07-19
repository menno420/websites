"""Discord OAuth owner login for botsite (ORDER 037).

Covers the ported login half: ``oauth_configured``, the stdlib signed session +
CSRF-state helpers, and the three routes (``/owner/login``,
``/owner/auth/callback``, ``/owner/logout``) — all without live Discord (the
``exchange_code``/``fetch_user`` seams are monkeypatched). Also pins the
fail-closed gate wiring on botsite's owner surface: env-unset keeps
``/testing/owner`` locked (503) and names the opening owner action; a valid
Discord session authorizes it with NO SITE_PASSWORD set; the existing
HTTP-Basic SITE_PASSWORD path still works (regression).
"""

from __future__ import annotations

import base64
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi.testclient import TestClient

from botsite import app as app_module
from botsite import data_source as ds
from botsite import discord_auth, testing, testing_ai

OWNER_ID = "123456789012345678"
NON_OWNER_ID = "999888777666555444"
CLIENT_ID = "test-client-id"

# Browsers send Origin on form POSTs; the same-origin guard requires it.
ORIGIN = {"Origin": "http://testserver"}
PW = "owner-pass"

_DISCORD_ENV = {
    "DISCORD_CLIENT_ID": CLIENT_ID,
    "DISCORD_CLIENT_SECRET": "test-client-secret",
    "OWNER_DISCORD_ID": OWNER_ID,
    "OWNER_SESSION_SECRET": "test-session-secret-please-change",
}


def _basic(pw: str, user: str = "owner") -> dict:
    token = base64.b64encode(f"{user}:{pw}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """Clean auth slate: temp sqlite, no SITE_PASSWORD, no Discord/OWNER env,
    the AI feed degraded, the site feed primed (network-free), rate limits
    reset."""
    monkeypatch.setenv("TESTING_DB_PATH", str(tmp_path / "testing.sqlite3"))
    for var in (
        "SITE_PASSWORD",
        "ANTHROPIC_API_KEY",
        "TESTING_AI_MODEL",
        "TESTING_AI_DAILY_CAP",
        *_DISCORD_ENV,
        "DISCORD_REDIRECT_URI",
    ):
        monkeypatch.delenv(var, raising=False)
    testing.reset_rate_limits()
    testing_ai.reset_ai_state()
    ds.clear_cache()
    ds.prime_cache({})
    ds.set_client(ds.make_client())  # never actually hit (cache is warm)
    with TestClient(app_module.app) as c:
        yield c
    ds.clear_cache()


def _configure(monkeypatch):
    for name, value in _DISCORD_ENV.items():
        monkeypatch.setenv(name, value)


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


# --------------------------------------------------------------------------- #
# oauth_configured — the fail-closed predicate
# --------------------------------------------------------------------------- #
def test_oauth_not_configured_when_env_unset(client):
    assert discord_auth.oauth_configured() is False


def test_oauth_configured_when_all_four_set(client, monkeypatch):
    _configure(monkeypatch)
    assert discord_auth.oauth_configured() is True


def test_oauth_not_configured_when_one_missing(client, monkeypatch):
    _configure(monkeypatch)
    monkeypatch.delenv("OWNER_SESSION_SECRET", raising=False)
    assert discord_auth.oauth_configured() is False


# --------------------------------------------------------------------------- #
# signed session helpers — sign / verify / expiry / tamper / garbage
# --------------------------------------------------------------------------- #
def test_session_roundtrip_valid(client, monkeypatch):
    _configure(monkeypatch)
    token = discord_auth.make_session(OWNER_ID)
    assert token
    assert discord_auth.verify_session(token) == OWNER_ID


def test_session_tampered_returns_none(client, monkeypatch):
    _configure(monkeypatch)
    token = discord_auth.make_session(OWNER_ID)
    _payload_b64, _, sig_b64 = token.partition(".")
    forged = discord_auth._b64e(f"{NON_OWNER_ID}|0|9999999999".encode())
    assert discord_auth.verify_session(f"{forged}.{sig_b64}") is None


def test_session_expired_returns_none(client, monkeypatch):
    _configure(monkeypatch)
    stale = discord_auth.make_session(OWNER_ID, now=1_000_000)  # ~1970
    assert discord_auth.verify_session(stale) is None


def test_session_garbage_returns_none(client, monkeypatch):
    _configure(monkeypatch)
    assert discord_auth.verify_session(None) is None
    assert discord_auth.verify_session("") is None
    assert discord_auth.verify_session("not-a-token") is None
    assert discord_auth.verify_session("a.b.c") is None


def test_session_without_secret_cannot_be_minted_or_verified(client, monkeypatch):
    assert discord_auth.make_session(OWNER_ID) == ""
    monkeypatch.setenv("OWNER_SESSION_SECRET", "s")
    real = discord_auth.make_session(OWNER_ID)
    monkeypatch.delenv("OWNER_SESSION_SECRET", raising=False)
    assert discord_auth.verify_session(real) is None


# --------------------------------------------------------------------------- #
# CSRF state helpers
# --------------------------------------------------------------------------- #
def test_state_roundtrip_valid(client, monkeypatch):
    _configure(monkeypatch)
    state = discord_auth.make_state()
    assert state
    assert discord_auth._state_signature_valid(state) is True


def test_state_tampered_or_missing_invalid(client, monkeypatch):
    _configure(monkeypatch)
    assert discord_auth._state_signature_valid(None) is False
    assert discord_auth._state_signature_valid("") is False
    assert discord_auth._state_signature_valid("forged.value") is False


# --------------------------------------------------------------------------- #
# env unset — fail closed, honest login page, locked owner queue
# --------------------------------------------------------------------------- #
def test_login_page_200_names_vars_and_optional_password(client):
    r = client.get("/owner/login")
    assert r.status_code == 200
    body = r.text
    assert "not configured" in body.lower()
    for var in (
        "DISCORD_CLIENT_ID",
        "DISCORD_CLIENT_SECRET",
        "OWNER_DISCORD_ID",
        "OWNER_SESSION_SECRET",
    ):
        assert var in body
    assert "SITE_PASSWORD" in body and "optional" in body.lower()
    # the redirect URI it asks the owner to add is shown
    assert "/owner/auth/callback" in body


def test_callback_unconfigured_is_locked_503(client):
    cb = client.get(
        "/owner/auth/callback?code=abc&state=whatever", follow_redirects=False
    )
    assert cb.status_code == 503


def test_owner_queue_locked_503_with_neither_password_nor_session(client):
    r = client.get("/testing/owner")
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
# callback — happy path (Discord session ALONE authorizes, no SITE_PASSWORD)
# --------------------------------------------------------------------------- #
def test_callback_happy_path_sets_session_and_authorizes_owner_queue(client, monkeypatch):
    _configure(monkeypatch)
    _install_seams(monkeypatch, OWNER_ID)
    state = _begin_login(client)
    cb = client.get(
        f"/owner/auth/callback?code=abc&state={state}", follow_redirects=False
    )
    assert cb.status_code == 302
    assert cb.headers["location"] == "/testing/owner"
    assert discord_auth.SESSION_COOKIE in cb.cookies
    # the minted session cookie now authorizes the gated queue — NO SITE_PASSWORD
    r = client.get("/testing/owner")
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
    # nothing leaked into the jar → the queue stays locked (401: oauth is
    # configured, so a bad/absent credential is 401 not 503)
    assert client.get("/testing/owner").status_code in (401, 503)


def test_callback_missing_state_rejected_csrf(client, monkeypatch):
    _configure(monkeypatch)
    _install_seams(monkeypatch, OWNER_ID)
    _begin_login(client)  # sets a real state cookie
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


def test_tampered_cookie_leaves_owner_queue_locked(client, monkeypatch):
    _configure(monkeypatch)
    r = client.get(
        "/testing/owner",
        cookies={discord_auth.SESSION_COOKIE: "not.a.valid.token"},
    )
    # no valid session, no SITE_PASSWORD, but oauth configured → 401
    assert r.status_code == 401


# --------------------------------------------------------------------------- #
# logout — clears the cookie, CSRF-protected
# --------------------------------------------------------------------------- #
def test_logout_clears_cookie_same_origin(client, monkeypatch):
    _configure(monkeypatch)
    _install_seams(monkeypatch, OWNER_ID)
    state = _begin_login(client)
    client.get(f"/owner/auth/callback?code=abc&state={state}", follow_redirects=False)
    assert client.get("/testing/owner").status_code == 200  # logged in
    r = client.post("/owner/logout", headers=ORIGIN, follow_redirects=False)
    assert r.status_code == 302
    assert r.headers["location"] == "/"
    # the Set-Cookie deletion clears the jar → the queue locks again
    assert client.get("/testing/owner").status_code in (401, 503)


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
# regression — the existing HTTP-Basic SITE_PASSWORD gate still authorizes the
# owner queue (no Discord env set)
# --------------------------------------------------------------------------- #
def test_site_password_basic_auth_still_authorizes(client, monkeypatch):
    monkeypatch.setenv("SITE_PASSWORD", PW)
    r = client.get("/testing/owner", headers=_basic(PW))
    assert r.status_code == 200


def test_site_password_wrong_still_401(client, monkeypatch):
    monkeypatch.setenv("SITE_PASSWORD", PW)
    r = client.get("/testing/owner", headers=_basic("nope"))
    assert r.status_code == 401
