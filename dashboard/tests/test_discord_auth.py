"""Discord OAuth owner login for the dashboard (ORDER 038).

Covers the ported login half: ``oauth_configured``, the stdlib signed session +
CSRF-state helpers, and the three routes (``/admin/login``,
``/admin/auth/callback``, ``/admin/logout``) — all without live Discord (the
``exchange_code``/``fetch_user`` seams are monkeypatched). Also pins the
fail-closed gate wiring on the dashboard's admin surface: env-unset keeps the
two state-changing admin POSTs locked (503) and the login page names the opening
owner action; a valid Discord session authorizes them AND is attributed as the
owner in the dry-run audit log; a non-owner is rejected; and configured-but-not-
signed-in is 401. Discord-only — the dashboard never had a SITE_PASSWORD gate.
"""

from __future__ import annotations

import html
import json
import re
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi.testclient import TestClient

from dashboard import app as app_module
from dashboard import control_plane as cp
from dashboard import data_source as ds
from dashboard import discord_auth

from dashboard.tests.test_dashboard import (
    ARCADE_FIXTURE,
    CONSOLE_FIXTURE,
    DASHBOARD_FIXTURE,
)

OWNER_ID = "123456789012345678"
NON_OWNER_ID = "999888777666555444"
CLIENT_ID = "test-client-id"
GUILD = "123456789012345678"

# Browsers send Origin on form POSTs; the same-origin logout guard requires it.
ORIGIN = {"Origin": "http://testserver"}

_DISCORD_ENV = {
    "DISCORD_CLIENT_ID": CLIENT_ID,
    "DISCORD_CLIENT_SECRET": "test-client-secret",
    "OWNER_DISCORD_ID": OWNER_ID,
    "OWNER_SESSION_SECRET": "test-session-secret-please-change",
}

# A valid setting.write form the gated preview/confirm actions accept.
_PREVIEW_FORM = {
    "action": "setting.write",
    "guild_id": GUILD,
    "domain": "economy",
    "key": "daily_amount",
    "value": "250",
}


@pytest.fixture()
def client(monkeypatch):
    """Clean auth slate: no Discord/OWNER env, the feeds primed (network-free),
    the dry-run audit log cleared."""
    for var in (*_DISCORD_ENV, "DISCORD_REDIRECT_URI"):
        monkeypatch.delenv(var, raising=False)
    ds.clear_cache()
    cp.controller.clear()
    ds.prime_cache(ds.DASHBOARD_JSON_URL, DASHBOARD_FIXTURE)
    ds.prime_cache(ds.CONSOLE_JSON_URL, CONSOLE_FIXTURE)
    ds.prime_cache(ds.ARCADE_JSON_URL, ARCADE_FIXTURE)
    ds.prime_cache(ds.RELEASES_JSON_URL, {"entries": [], "drift_count": 0})
    ds.set_client(ds.make_client())  # never actually hit (cache is warm)
    with TestClient(app_module.app) as c:
        yield c
    ds.clear_cache()
    cp.controller.clear()


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
    """Drive /admin/login and return the state param that matches the cookie."""
    r = client.get("/admin/login", follow_redirects=False)
    assert r.status_code == 302
    return parse_qs(urlparse(r.headers["location"]).query)["state"][0]


def _extract_request_json(page_text: str) -> dict:
    m = re.search(r'<pre class="snippet" id="request-json">(.*?)</pre>', page_text, re.S)
    assert m, "the page must embed the exact request JSON"
    return json.loads(html.unescape(m.group(1)))


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
# env unset — fail closed, honest login page (no SITE_PASSWORD), locked actions
# --------------------------------------------------------------------------- #
def test_login_page_200_names_vars_no_site_password(client):
    r = client.get("/admin/login")
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
    # Discord-only: the dashboard never had a password gate.
    assert "SITE_PASSWORD" not in body
    # the redirect URI it asks the owner to add is shown
    assert "/admin/auth/callback" in body


def test_callback_unconfigured_is_locked_503(client):
    cb = client.get(
        "/admin/auth/callback?code=abc&state=whatever", follow_redirects=False
    )
    assert cb.status_code == 503


def test_gated_actions_locked_503_when_unconfigured(client):
    """Both state-changing admin POSTs fail closed (503) with no session and no
    OAuth configured — and the 503 names the opening owner action."""
    for path in ("/admin/actions/preview", "/admin/actions/confirm"):
        r = client.post(path, data=_PREVIEW_FORM)
        assert r.status_code == 503, path
        assert "/admin/login" in r.text
    assert cp.controller.entries() == []  # nothing recorded


def test_read_views_stay_public_when_unconfigured(client):
    """The read-only oversight + admin display pages stay ungated (200)."""
    for path in ("/", "/admin", "/admin/cogs", "/admin/help", "/admin/audit"):
        assert client.get(path).status_code == 200, path


# --------------------------------------------------------------------------- #
# configured — /admin/login redirects to Discord and sets the state cookie
# --------------------------------------------------------------------------- #
def test_login_redirects_to_discord_when_configured(client, monkeypatch):
    _configure(monkeypatch)
    r = client.get("/admin/login", follow_redirects=False)
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
# callback — happy path (Discord session authorizes the gated actions; the
# confirmed action is attributed to the real owner, not anonymous)
# --------------------------------------------------------------------------- #
def test_callback_happy_path_authorizes_and_attributes_owner(client, monkeypatch):
    _configure(monkeypatch)
    _install_seams(monkeypatch, OWNER_ID)
    state = _begin_login(client)
    cb = client.get(
        f"/admin/auth/callback?code=abc&state={state}", follow_redirects=False
    )
    assert cb.status_code == 302
    assert cb.headers["location"] == "/admin"
    assert discord_auth.SESSION_COOKIE in cb.cookies

    # the minted session cookie now authorizes the gated preview (not 503/401)…
    prev = client.post("/admin/actions/preview", data=_PREVIEW_FORM)
    assert prev.status_code == 200
    req = _extract_request_json(prev.text)
    assert req["actor"]["display"] == "owner (Discord)"
    assert req["actor"]["discord_user_id"] == OWNER_ID

    # …and a confirmed action records the OWNER in the dry-run audit log.
    conf = client.post("/admin/actions/confirm", data=_PREVIEW_FORM)
    assert conf.status_code == 200
    entries = cp.controller.entries()
    assert len(entries) == 1
    assert entries[0]["actor"] == "owner (Discord)"
    assert entries[0]["request"]["actor"]["discord_user_id"] == OWNER_ID


def test_callback_non_owner_id_403_no_session(client, monkeypatch):
    _configure(monkeypatch)
    _install_seams(monkeypatch, NON_OWNER_ID)
    state = _begin_login(client)
    cb = client.get(
        f"/admin/auth/callback?code=abc&state={state}", follow_redirects=False
    )
    assert cb.status_code == 403
    assert discord_auth.SESSION_COOKIE not in cb.cookies
    # nothing leaked into the jar → the gated actions stay locked (401: oauth is
    # configured, so a bad/absent credential is 401 not 503)
    assert client.post("/admin/actions/preview", data=_PREVIEW_FORM).status_code == 401


def test_callback_missing_state_rejected_csrf(client, monkeypatch):
    _configure(monkeypatch)
    _install_seams(monkeypatch, OWNER_ID)
    _begin_login(client)  # sets a real state cookie
    cb = client.get("/admin/auth/callback?code=abc", follow_redirects=False)
    assert cb.status_code == 400
    assert discord_auth.SESSION_COOKIE not in cb.cookies


def test_callback_wrong_state_rejected_csrf(client, monkeypatch):
    _configure(monkeypatch)
    _install_seams(monkeypatch, OWNER_ID)
    _begin_login(client)
    cb = client.get(
        "/admin/auth/callback?code=abc&state=forged-state-value",
        follow_redirects=False,
    )
    assert cb.status_code == 400
    assert discord_auth.SESSION_COOKIE not in cb.cookies


# --------------------------------------------------------------------------- #
# configured but not signed in — the gated actions are 401
# --------------------------------------------------------------------------- #
def test_configured_but_not_signed_in_is_401(client, monkeypatch):
    _configure(monkeypatch)
    r = client.post("/admin/actions/preview", data=_PREVIEW_FORM)
    assert r.status_code == 401
    assert cp.controller.entries() == []


def test_tampered_cookie_leaves_actions_locked_401(client, monkeypatch):
    _configure(monkeypatch)
    r = client.post(
        "/admin/actions/preview",
        data=_PREVIEW_FORM,
        cookies={discord_auth.SESSION_COOKIE: "not.a.valid.token"},
    )
    assert r.status_code == 401


# --------------------------------------------------------------------------- #
# logout — clears the cookie, CSRF-protected
# --------------------------------------------------------------------------- #
def test_logout_clears_cookie_same_origin(client, monkeypatch):
    _configure(monkeypatch)
    _install_seams(monkeypatch, OWNER_ID)
    state = _begin_login(client)
    client.get(f"/admin/auth/callback?code=abc&state={state}", follow_redirects=False)
    assert client.post("/admin/actions/preview", data=_PREVIEW_FORM).status_code == 200
    r = client.post("/admin/logout", headers=ORIGIN, follow_redirects=False)
    assert r.status_code == 302
    assert r.headers["location"] == "/admin"
    # the Set-Cookie deletion clears the jar → the gated actions lock again (401)
    assert client.post("/admin/actions/preview", data=_PREVIEW_FORM).status_code == 401


def test_logout_without_origin_rejected(client, monkeypatch):
    _configure(monkeypatch)
    r = client.post("/admin/logout", follow_redirects=False)
    assert r.status_code == 403


def test_logout_cross_origin_rejected(client, monkeypatch):
    _configure(monkeypatch)
    r = client.post(
        "/admin/logout",
        headers={"Origin": "https://evil.example"},
        follow_redirects=False,
    )
    assert r.status_code == 403
