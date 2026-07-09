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
from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from . import config, github, readiness

router = APIRouter(prefix="/owner")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

_UNAUTH_HEADERS = {"WWW-Authenticate": 'Basic realm="owner area"'}


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
async def action_refresh(request: Request, _: None = Depends(require_owner)):
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
    request: Request, repo: str = Form(...), _: None = Depends(require_owner)
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
