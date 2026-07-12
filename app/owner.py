"""Gated owner area — the one non-public corner of an otherwise public site.

Everything here sits behind `require_owner` (HTTP Basic, any username, password
compared constant-time to `SITE_PASSWORD`). The public site in `app/main.py`
never touches this module or the gate, so the two surfaces cannot leak into each
other: the board at `/` stays byte-identical and credential-free, while `/owner`
un-masks the data it hides (Actions secret NAMES) and exposes real, reversible
privileged actions (cache refresh, re-run the latest failed CI run) using creds
already on the service.

Fail closed: if `SITE_PASSWORD` is unset the /owner routes return 503 while the
public site keeps working.
"""

from __future__ import annotations

import base64
import secrets
import time
from collections import defaultdict, deque
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from . import config, github, railway, readiness

router = APIRouter(prefix="/owner")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
# The environments page deep-links each live variable name to its console
# (prefix-matched in app/railway.py) — exposed as a filter so the template
# needs no hand-kept link table.
templates.env.filters["manage_link"] = railway.manage_link

_UNAUTH_HEADERS = {"WWW-Authenticate": 'Basic realm="owner area"'}

# ---------------------------------------------------------------------------
# CSRF + rate-limit hardening for the state-changing POST actions (ORDER 013).
#
# CSRF: strict same-origin check on Origin/Referer. If an Origin header is
# present its host must match the request's own Host header; if Origin is
# absent we fall back to Referer with the same rule. If BOTH are absent the
# request is REJECTED with 403 (strictest choice, deliberate): every modern
# browser sends Origin on a POST, so a browser-driven owner console always
# passes, while a header-less forged/cross-context POST never does.
# Non-browser callers (curl, scripts) must supply a matching Origin header.
# Hosts are compared (netloc, case-insensitive) rather than full scheme+host
# because the service runs behind Railway's TLS-terminating proxy, where the
# app-side scheme may not match the browser-side one; the host comparison is
# what defeats a cross-site request, since an attacker's page cannot forge
# the browser-set Origin/Referer host.
#
# Rate limit: a dependency-free in-process sliding window, per route path +
# client host — 10 requests per 60s, 429 beyond that. State is module-level
# and in-memory (one process per service), resettable for tests.
# ---------------------------------------------------------------------------

RATE_LIMIT_MAX_REQUESTS = 10
RATE_LIMIT_WINDOW_SECONDS = 60.0

_rate_buckets: dict[str, deque] = defaultdict(deque)


def reset_rate_limits() -> None:
    """Clear all rate-limit state (test isolation hook)."""
    _rate_buckets.clear()


def _header_host(value: str) -> str:
    """Lowercased netloc of an Origin/Referer header value ('' if unparsable)."""
    try:
        return urlsplit(value).netloc.lower()
    except ValueError:
        return ""


def _require_same_origin(request: Request) -> None:
    """Reject state-changing requests whose Origin/Referer is not this host."""
    own_host = request.headers.get("host", "").strip().lower()
    origin = request.headers.get("origin")
    if origin is not None:
        if not own_host or _header_host(origin) != own_host:
            raise HTTPException(
                status_code=403,
                detail="cross-origin request rejected (Origin mismatch)",
            )
        return
    referer = request.headers.get("referer")
    if referer is not None:
        if not own_host or _header_host(referer) != own_host:
            raise HTTPException(
                status_code=403,
                detail="cross-origin request rejected (Referer mismatch)",
            )
        return
    # Documented strict choice: no Origin AND no Referer → reject. Browsers
    # always send Origin on POST, so this only ever blocks non-browser
    # callers that omitted the header.
    raise HTTPException(
        status_code=403,
        detail=(
            "request rejected: missing Origin/Referer header "
            "(same-origin required for owner actions)"
        ),
    )


def _enforce_rate_limit(request: Request) -> None:
    """Sliding-window limiter per (route path, client host); 429 when tripped."""
    client_host = request.client.host if request.client else "unknown"
    key = f"{request.url.path}|{client_host}"
    now = time.monotonic()
    bucket = _rate_buckets[key]
    while bucket and now - bucket[0] > RATE_LIMIT_WINDOW_SECONDS:
        bucket.popleft()
    if len(bucket) >= RATE_LIMIT_MAX_REQUESTS:
        retry_after = max(1, int(RATE_LIMIT_WINDOW_SECONDS - (now - bucket[0])) + 1)
        raise HTTPException(
            status_code=429,
            detail="rate limit exceeded for owner actions — retry shortly",
            headers={"Retry-After": str(retry_after)},
        )
    bucket.append(now)


def require_owner(request: Request) -> None:
    """Dependency gating every /owner route. Raises 503 (unset) or 401 (bad)."""
    if not config.SITE_PASSWORD:
        # Fail closed: an unset password never means an open door. The public
        # site is unaffected — only this gated area 503s.
        raise HTTPException(
            status_code=503,
            detail="owner area unavailable: SITE_PASSWORD is not configured",
        )
    header = request.headers.get("authorization", "")
    supplied = ""
    if header.lower().startswith("basic "):
        try:
            decoded = base64.b64decode(header.split(" ", 1)[1]).decode("utf-8")
            _user, _, supplied = decoded.partition(":")
        except Exception:
            supplied = ""
    if not supplied or not secrets.compare_digest(supplied, config.SITE_PASSWORD):
        raise HTTPException(
            status_code=401,
            detail="owner authentication required",
            headers=_UNAUTH_HEADERS,
        )


def require_owner_action(request: Request) -> None:
    """Dependency gating every STATE-CHANGING /owner route.

    Auth first (401/503 exactly as `require_owner`), then the strict
    same-origin CSRF check (403), then the in-process rate limit (429).
    """
    require_owner(request)
    _require_same_origin(request)
    _enforce_rate_limit(request)


def _refresh(request: Request) -> bool:
    return request.query_params.get("refresh") in ("1", "true", "yes")


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def owner_board(request: Request, _: None = Depends(require_owner)):
    # reveal_secrets=True: the authed path un-masks the secret NAMES the public
    # board only counts. This flag never reaches the public board() call.
    rows = await readiness.board(refresh=_refresh(request), reveal_secrets=True)
    return templates.TemplateResponse(
        request,
        "owner.html",
        {
            "rows": rows,
            "ttl": config.CACHE_TTL_SECONDS,
            "cache_entries": github.cache_size(),
            "banner": None,
            "repos": list(config.REPOS),
        },
    )


@router.get("/api/readiness.json")
async def owner_board_json(request: Request, _: None = Depends(require_owner)):
    # Authed JSON: unlike the public /api/readiness.json, this DOES carry the
    # secret names (under each row's secrets.names).
    return JSONResponse(
        await readiness.board(refresh=_refresh(request), reveal_secrets=True)
    )


@router.get("/environments", response_class=HTMLResponse)
async def owner_environments(request: Request, _: None = Depends(require_owner)):
    """Live-env-visibility page (ORDER 015, plan slice 1 —
    docs/planning/live-env-visibility-plan-2026-07-11.md). Read-only GET
    behind the same gate as the rest of /owner: committed per-service env
    facts always; live Railway variable NAMES (never values) when the
    project-scoped RAILWAY_TOKEN is configured; an honest owner-errand
    banner while it is not."""
    data = await railway.overview(refresh=_refresh(request))
    return templates.TemplateResponse(
        request,
        "owner_environments.html",
        {"env": data, "ttl": config.CACHE_TTL_SECONDS},
    )


async def _render_with_banner(request: Request, banner: dict) -> HTMLResponse:
    rows = await readiness.board(reveal_secrets=True)
    return templates.TemplateResponse(
        request,
        "owner.html",
        {
            "rows": rows,
            "ttl": config.CACHE_TTL_SECONDS,
            "cache_entries": github.cache_size(),
            "banner": banner,
            "repos": list(config.REPOS),
        },
    )


@router.post("/actions/refresh", response_class=HTMLResponse)
async def action_refresh(request: Request, _: None = Depends(require_owner_action)):
    dropped = github.clear_cache()
    banner = {
        "ok": True,
        "text": (
            f"cache cleared — {dropped} entr{'y' if dropped == 1 else 'ies'} "
            "dropped; the board below is re-fetched live"
        ),
    }
    return await _render_with_banner(request, banner)


@router.post("/actions/rerun-ci", response_class=HTMLResponse)
async def action_rerun_ci(
    request: Request, repo: str = Form(...), _: None = Depends(require_owner_action)
):
    if repo not in config.REPOS:
        banner = {"ok": False, "text": f"unknown repo: {repo!r}"}
        return await _render_with_banner(request, banner)
    result = await github.rerun_latest_failed(repo)
    banner = {
        "ok": bool(result.get("ok")),
        "text": result.get("message", "re-run attempted"),
        "url": result.get("url"),
    }
    return await _render_with_banner(request, banner)
