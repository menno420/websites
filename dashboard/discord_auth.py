"""Discord OAuth owner login for the dashboard (ORDER 038).

The fleet-login-unification port into the dashboard's admin surface: ONE Discord
login now gates the dashboard's state-changing admin actions (the dry-run control
panel's ``POST /admin/actions/preview`` + ``/admin/actions/confirm``). It mounts
the login door at ``/admin/login`` and its callback at ``/admin/auth/callback``.

This is a near-verbatim port of ``botsite/discord_auth.py`` /
``app/discord_auth.py`` — services never share a running process (each has its
own Dockerfile + Railway service), so this is a deliberate idiomatic DUPLICATION,
not an import. It REUSES the existing fleet-side SuperBot Discord app: the owner
adds a dashboard redirect URI + copies the client id/secret onto THIS service's
Railway env; until then every gated action stays locked and the login page names
exactly which owner action opens it.

Discord-ONLY: unlike botsite/control-plane, the dashboard never had a
``SITE_PASSWORD`` gate ([D-0011] made every read view public), so there is no
password fallback here — a valid Discord owner session is the only key, and the
read-only oversight views stay public and ungated.

Fail-closed by construction:

* ``oauth_configured()`` is True ONLY when all four of DISCORD_CLIENT_ID,
  DISCORD_CLIENT_SECRET, OWNER_DISCORD_ID and OWNER_SESSION_SECRET are set.
  Env-unset → ``/admin/login`` renders an honest "not configured" page (HTTP
  200) naming the four vars + the redirect URI; the callback 503s and the gated
  actions 503.
* The session cookie is an HMAC-SHA256 signature (stdlib only — ``hmac``,
  ``hashlib``, ``secrets``, ``base64``) over ``discord_id|issued_at|expiry``
  keyed on OWNER_SESSION_SECRET; ``verify_session`` returns the id only on a
  constant-time signature match that has not expired.
* A signed random ``state`` token (CSRF floor) is stored in a short-lived
  cookie and echoed as the ``state`` query param; the callback rejects any
  mismatch.
* The callback mints a session ONLY when the Discord user id it fetches
  equals OWNER_DISCORD_ID — any other identity gets 403 and no cookie.

The two network calls are factored into ``exchange_code``/``fetch_user`` seams
so tests monkeypatch them without live Discord.

Wiring: ``owner_session_id(request)`` is what ``require_owner`` (the fail-closed
dependency on the two state-changing admin POSTs) consults, and ``actor_for``
turns a valid session into the audit-log actor. The router here is included by
``dashboard/app.py`` and is deliberately NOT gated (it is the door, not a room
behind it).
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
import time
from pathlib import Path

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

# Discord OAuth endpoints (the standard public URLs — not secrets).
AUTHORIZE_URL = "https://discord.com/api/oauth2/authorize"
TOKEN_URL = "https://discord.com/api/oauth2/token"
USER_URL = "https://discord.com/api/users/@me"
OAUTH_SCOPE = "identify"

SESSION_COOKIE = "owner_session"
STATE_COOKIE = "owner_oauth_state"
# Session lifetime: long enough for an owner working session, short enough that
# a leaked cookie expires on its own. The expiry is signed INTO the token, so a
# tampered lifetime fails verification.
SESSION_TTL_SECONDS = 8 * 60 * 60  # 8 hours
STATE_TTL_SECONDS = 10 * 60  # the login round-trip window

# Env var NAMES (never values) — read live on every call so a monkeypatched or
# newly-pasted env is picked up without a restart.
ENV_CLIENT_ID = "DISCORD_CLIENT_ID"
ENV_CLIENT_SECRET = "DISCORD_CLIENT_SECRET"
ENV_OWNER_ID = "OWNER_DISCORD_ID"
ENV_SESSION_SECRET = "OWNER_SESSION_SECRET"
ENV_REDIRECT_URI = "DISCORD_REDIRECT_URI"  # optional override


def _env(name: str) -> str:
    return (os.environ.get(name) or "").strip()


def oauth_configured() -> bool:
    """True only when client id + secret + owner id + session secret are ALL
    set. The single fail-closed predicate every route consults."""
    return bool(
        _env(ENV_CLIENT_ID)
        and _env(ENV_CLIENT_SECRET)
        and _env(ENV_OWNER_ID)
        and _env(ENV_SESSION_SECRET)
    )


# --------------------------------------------------------------------------- #
# stdlib-only signed-token helpers (HMAC-SHA256, base64url). No new deps.
# --------------------------------------------------------------------------- #
def _b64e(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64d(text: str) -> bytes:
    pad = "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode(text + pad)


def _sign(message: bytes) -> bytes:
    """HMAC-SHA256 of ``message`` under OWNER_SESSION_SECRET. Returns b'' when
    the secret is unset so an unconfigured service can never mint a token."""
    secret = _env(ENV_SESSION_SECRET)
    if not secret:
        return b""
    return hmac.new(secret.encode("utf-8"), message, hashlib.sha256).digest()


def make_session(discord_id: str, *, now: int | None = None) -> str:
    """Signed session token for ``discord_id``: ``payload.signature`` where
    payload = b64url(``discord_id|issued_at|expiry``) and signature = b64url of
    the HMAC over that payload. Empty string if the secret is unset."""
    issued = int(time.time() if now is None else now)
    expiry = issued + SESSION_TTL_SECONDS
    payload = f"{discord_id}|{issued}|{expiry}".encode("utf-8")
    sig = _sign(payload)
    if not sig:
        return ""
    return f"{_b64e(payload)}.{_b64e(sig)}"


def verify_session(raw: str | None) -> str | None:
    """Return the discord id iff ``raw`` is a well-formed token whose signature
    verifies (constant-time) AND whose expiry is still in the future; else None.
    Any malformed/tampered/expired input returns None (never raises)."""
    if not raw or "." not in raw:
        return None
    payload_b64, _, sig_b64 = raw.partition(".")
    try:
        payload = _b64d(payload_b64)
        supplied_sig = _b64d(sig_b64)
    except (ValueError, TypeError):
        return None
    expected_sig = _sign(payload)
    if not expected_sig or not hmac.compare_digest(supplied_sig, expected_sig):
        return None
    try:
        discord_id, issued_s, expiry_s = payload.decode("utf-8").split("|")
        expiry = int(expiry_s)
    except (ValueError, UnicodeDecodeError):
        return None
    if int(time.time()) >= expiry:
        return None
    return discord_id or None


def make_state(*, now: int | None = None) -> str:
    """A signed random CSRF ``state`` token: ``nonce|issued.signature``. The
    same value is stored in a short-lived cookie AND passed as the state query
    param; the callback requires both to match and the signature to verify."""
    issued = int(time.time() if now is None else now)
    nonce = secrets.token_urlsafe(18)
    payload = f"{nonce}|{issued}".encode("utf-8")
    sig = _sign(payload)
    if not sig:
        return ""
    return f"{_b64e(payload)}.{_b64e(sig)}"


def _state_signature_valid(raw: str | None) -> bool:
    """True iff ``raw`` is a well-formed state token with a verifying signature
    that has not aged past STATE_TTL_SECONDS."""
    if not raw or "." not in raw:
        return False
    payload_b64, _, sig_b64 = raw.partition(".")
    try:
        payload = _b64d(payload_b64)
        supplied_sig = _b64d(sig_b64)
    except (ValueError, TypeError):
        return False
    expected_sig = _sign(payload)
    if not expected_sig or not hmac.compare_digest(supplied_sig, expected_sig):
        return False
    try:
        _nonce, issued_s = payload.decode("utf-8").split("|")
        issued = int(issued_s)
    except (ValueError, UnicodeDecodeError):
        return False
    return int(time.time()) - issued <= STATE_TTL_SECONDS


def owner_session_id(request: Request) -> str | None:
    """The verified owner discord id carried by the request's session cookie,
    or None. ``require_owner`` + ``actor_for`` consult it."""
    return verify_session(request.cookies.get(SESSION_COOKIE))


# --------------------------------------------------------------------------- #
# request-scheme + redirect-uri helpers (behind Railway's TLS-terminating
# proxy the app-side scheme is http; the browser-side one is https — trust the
# forwarded header for the Secure-cookie + redirect_uri decision).
# --------------------------------------------------------------------------- #
def _is_https(request: Request) -> bool:
    proto = (request.headers.get("x-forwarded-proto") or "").split(",")[0].strip().lower()
    return proto == "https" or request.url.scheme == "https"


def redirect_uri_for(request: Request) -> str:
    """The OAuth redirect URI: the DISCORD_REDIRECT_URI override when set, else
    derived from the request's own base URL + /admin/auth/callback (honoring the
    forwarded https scheme so it matches what the owner registers)."""
    override = _env(ENV_REDIRECT_URI)
    if override:
        return override
    base = str(request.base_url).rstrip("/")
    if _is_https(request) and base.startswith("http://"):
        base = "https://" + base[len("http://"):]
    return f"{base}/admin/auth/callback"


def _set_session_cookie(response: Response, request: Request, token: str) -> None:
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=SESSION_TTL_SECONDS,
        httponly=True,
        secure=_is_https(request),
        samesite="lax",
        path="/",
    )


# --------------------------------------------------------------------------- #
# owner-gate seams — the reader (actor_for) + the fail-closed dependency
# (require_owner) the two state-changing admin POSTs depend on. Discord-only, no
# SITE_PASSWORD path (the dashboard never had one).
# --------------------------------------------------------------------------- #
def actor_for(request: Request) -> dict:
    """The audit-log actor for this request: the signed-in Discord owner when a
    valid session cookie is present, else the honest anonymous actor. Imports
    control_plane lazily to avoid a circular import at module load."""
    owner_id = owner_session_id(request)
    if owner_id:
        return {"discord_user_id": owner_id, "display": "owner (Discord)"}
    from . import control_plane as cp

    return cp.ANONYMOUS_ACTOR


def require_owner(request: Request) -> None:
    """Fail-closed owner gate for the state-changing admin actions. Discord-only:

    * a valid owner session → pass;
    * OAuth unconfigured → 503 naming the opening owner action;
    * configured but no/invalid session → 401.
    """
    if owner_session_id(request):
        return
    if not oauth_configured():
        raise HTTPException(
            status_code=503,
            detail=(
                "dashboard admin actions are unavailable: sign in with Discord "
                "at /admin/login (needs DISCORD_CLIENT_ID, DISCORD_CLIENT_SECRET, "
                "OWNER_DISCORD_ID, OWNER_SESSION_SECRET)"
            ),
        )
    raise HTTPException(
        status_code=401,
        detail="owner authentication required — sign in at /admin/login",
    )


# --------------------------------------------------------------------------- #
# network seams — overridable so tests never touch live Discord.
# --------------------------------------------------------------------------- #
async def exchange_code(code: str, redirect_uri: str) -> dict:
    """Exchange an authorization code for a token at Discord's token endpoint.
    Overridden in tests. Returns the parsed token JSON (carries access_token)."""
    data = {
        "client_id": _env(ENV_CLIENT_ID),
        "client_secret": _env(ENV_CLIENT_SECRET),
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
    }
    async with httpx.AsyncClient(timeout=15.0, trust_env=True) as client:
        resp = await client.post(
            TOKEN_URL,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        resp.raise_for_status()
        return resp.json()


async def fetch_user(access_token: str) -> dict:
    """Fetch the authenticated Discord user (@me). Overridden in tests. Returns
    the parsed user JSON (carries the ``id`` compared against OWNER_DISCORD_ID)."""
    async with httpx.AsyncClient(timeout=15.0, trust_env=True) as client:
        resp = await client.get(
            USER_URL, headers={"Authorization": f"Bearer {access_token}"}
        )
        resp.raise_for_status()
        return resp.json()


# --------------------------------------------------------------------------- #
# routes — included by dashboard/app.py, NOT under the owner gate.
# --------------------------------------------------------------------------- #
def _login_context(request: Request, configured: bool) -> dict:
    """Context for admin_login.html. The dashboard's base.html reads its nav +
    banner + build context from the route (there are no Jinja globals for it), so
    this supplies SAFE DEFAULTS for every base.html variable — an empty nav, no
    active highlight, the feed-ok flags set so no error/drift banner shows, and
    empty build/counts/meta — so the page renders standalone WITHOUT importing
    dashboard.app (which would be a circular import)."""
    return {
        "request": request,
        "configured": configured,
        "authorize_hint": AUTHORIZE_URL,
        "redirect_uri": redirect_uri_for(request),
        # base.html header/banner/footer defaults (this is an auth-flow endpoint,
        # not a nav page — it carries no nav highlight key on purpose):
        "nav": [],
        "active": "",
        "data_ok": True,
        "data_error": "",
        "schema_warning": "",
        "build": {"commit": "", "subject": ""},
        "counts": {},
        "meta": {},
        "res": {},
        "data": {},
        "fetched_at": "",
    }


@router.get("/admin/login", response_class=HTMLResponse)
async def admin_login(request: Request):
    """Start the Discord owner login. Unconfigured → an honest HTTP-200 page
    naming the opening owner action (add the dashboard redirect URI + set the
    four vars on the dashboard Railway service). Configured → set the signed
    state cookie and 302 to Discord's authorize endpoint (scope=identify)."""
    if not oauth_configured():
        return templates.TemplateResponse(
            request, "admin_login.html", _login_context(request, configured=False)
        )
    state = make_state()
    redirect_uri = redirect_uri_for(request)
    params = httpx.QueryParams(
        {
            "client_id": _env(ENV_CLIENT_ID),
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": OAUTH_SCOPE,
            "state": state,
        }
    )
    response = RedirectResponse(f"{AUTHORIZE_URL}?{params}", status_code=302)
    response.set_cookie(
        STATE_COOKIE,
        state,
        max_age=STATE_TTL_SECONDS,
        httponly=True,
        secure=_is_https(request),
        samesite="lax",
        path="/",
    )
    return response


@router.get("/admin/auth/callback")
async def admin_auth_callback(request: Request, code: str = "", state: str = ""):
    """Finish the login: verify the CSRF state against the cookie, exchange the
    code, fetch the user, and mint a session ONLY when the id matches
    OWNER_DISCORD_ID. Unconfigured → 503 (locked); bad state → 400; non-owner →
    403 (no cookie). Success redirects to the control panel (/admin)."""
    if not oauth_configured():
        raise HTTPException(
            status_code=503,
            detail=(
                "Discord owner login is not configured — set "
                f"{ENV_CLIENT_ID}, {ENV_CLIENT_SECRET}, {ENV_OWNER_ID} and "
                f"{ENV_SESSION_SECRET} on this service."
            ),
        )
    cookie_state = request.cookies.get(STATE_COOKIE)
    if (
        not state
        or not cookie_state
        or not hmac.compare_digest(state, cookie_state)
        or not _state_signature_valid(state)
    ):
        raise HTTPException(
            status_code=400,
            detail="login state mismatch (CSRF check failed) — start again at /admin/login",
        )
    if not code:
        raise HTTPException(status_code=400, detail="missing authorization code")
    try:
        token = await exchange_code(code, redirect_uri_for(request))
        access_token = (token or {}).get("access_token")
        if not access_token:
            raise HTTPException(
                status_code=502, detail="Discord returned no access token"
            )
        user = await fetch_user(access_token)
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502, detail=f"Discord OAuth exchange failed: {exc}"
        )
    discord_id = str((user or {}).get("id") or "")
    if not discord_id or discord_id != _env(ENV_OWNER_ID):
        # Not the owner — no session is minted. The state cookie is cleared so a
        # fresh attempt starts clean.
        resp = HTMLResponse(
            "<h1>Not authorized</h1><p>This Discord account is not the owner.</p>",
            status_code=403,
        )
        resp.delete_cookie(STATE_COOKIE, path="/")
        return resp
    # Land the freshly-authorized owner straight on the control panel.
    response = RedirectResponse("/admin", status_code=302)
    _set_session_cookie(response, request, make_session(discord_id))
    response.delete_cookie(STATE_COOKIE, path="/")
    return response


@router.post("/admin/logout")
async def admin_logout(request: Request):
    """Clear the owner session and return to the control panel. CSRF-protected:
    a same-origin Origin/Referer is required (a header-less or cross-origin POST
    is rejected 403), mirroring the /admin state-change floor."""
    own_host = (request.headers.get("host") or "").strip().lower()
    origin = request.headers.get("origin")
    referer = request.headers.get("referer")
    source = origin if origin is not None else referer
    if source is None:
        raise HTTPException(
            status_code=403,
            detail="logout rejected: missing Origin/Referer (same-origin required)",
        )
    from urllib.parse import urlsplit

    if not own_host or urlsplit(source).netloc.lower() != own_host:
        raise HTTPException(
            status_code=403, detail="logout rejected: cross-origin request"
        )
    response = RedirectResponse("/admin", status_code=302)
    response.delete_cookie(SESSION_COOKIE, path="/")
    return response
