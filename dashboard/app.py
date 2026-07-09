"""SuperBot developer dashboard — private, server-rendered oversight site.

The **private** half of the websites estate (plan
``docs/planning/dashboard-botsite-rework-plan-2026-07-09.md``). Rebuilt on this repo's
substrate — FastAPI + Jinja2, server-rendered, no build step — from superbot's
``dashboard/``: same read-only ideas and functionality, fresh implementation on the
shared ``ds/`` design system.

**Auth.** The whole surface is internal oversight data, so it is gated behind HTTP Basic
(any username, password compared constant-time to ``SITE_PASSWORD``), identical to the
control-plane app. Fail-closed: an unset ``SITE_PASSWORD`` 503s rather than opening the
door. ``/healthz`` is the single unauthenticated route (Railway probe).

**Data.** The read-only oversight pages consume superbot's committed ``dashboard.json`` /
``console.json`` live over raw.githubusercontent.com (``data_source``). This app **never
imports bot code** and holds **no bot control credential**. A failed feed renders an
honest banner — never faked data.

**The control-panel stub (the deliberate boundary).** superbot's dashboard also has a
Discord-OAuth control panel that WRITES the *live production bot's* control API
(start/stop/config the running bot) and an owner-gated submissions-moderation ring. That
live-write path is **NOT wired here** (plan Q4): ``/admin`` renders a clearly-labeled
stub whose mutating actions are disabled placeholders, and **no** production bot
control-API URL or token is referenced anywhere in this service. See ``docs/dashboard.md``.

Deploy: a new Railway service in ``superbot-websites`` (Root Directory = ``dashboard``),
own Dockerfile, binds ``0.0.0.0:$PORT``.
"""

from __future__ import annotations

import base64
import secrets
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import config
from . import data_source as ds

BASE_DIR = Path(__file__).resolve().parent

# Primary read-only oversight nav. The control panel is a labelled stub, linked apart.
NAV = [
    ("functions", "Functions", "/functions"),
    ("commands", "Commands", "/commands"),
    ("settings", "Settings", "/settings"),
    ("access", "Access", "/access"),
    ("env", "Env map", "/env"),
    ("ideas", "Ideas", "/ideas"),
    ("bugs", "Bugs", "/bugs"),
    ("updates", "Updates", "/updates"),
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    if ds._client is None:  # tests may pre-set a client; don't clobber it
        ds.set_client(ds.make_client())
    try:
        await ds.fetch_dashboard()  # warm the cache; failure is non-fatal (pages degrade)
    except Exception:  # pragma: no cover - never block startup on the network
        pass
    yield
    await ds._get_client().aclose()


app = FastAPI(title="SuperBot Dashboard", lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


# ---------------------------------------------------------------------------
# Auth — HTTP Basic on every route except /healthz (mirrors app/main.py).
# ---------------------------------------------------------------------------
def _authorized(request: Request) -> bool:
    if not config.SITE_PASSWORD:
        return False  # fail closed: an unset password never means an open door
    header = request.headers.get("authorization", "")
    if not header.lower().startswith("basic "):
        return False
    try:
        decoded = base64.b64decode(header.split(" ", 1)[1]).decode("utf-8")
        _user, _, password = decoded.partition(":")
    except Exception:
        return False
    return secrets.compare_digest(password, config.SITE_PASSWORD)


@app.middleware("http")
async def auth_gate(request: Request, call_next):
    if request.url.path == "/healthz":
        return await call_next(request)
    if not _authorized(request):
        detail = (
            "SITE_PASSWORD is not configured on the server."
            if not config.SITE_PASSWORD
            else "Authentication required."
        )
        return Response(
            content=detail,
            status_code=503 if not config.SITE_PASSWORD else 401,
            headers={"WWW-Authenticate": 'Basic realm="dashboard"'},
            media_type="text/plain",
        )
    return await call_next(request)


def _refresh(request: Request) -> bool:
    return request.query_params.get("refresh") in ("1", "true", "yes")


async def _base_ctx(request: Request, active: str) -> dict[str, Any]:
    res = await ds.fetch_dashboard(refresh=_refresh(request))
    data = res.get("data", {}) or {}
    return {
        "request": request,
        "active": active,
        "nav": NAV,
        "res": res,
        "data": data,
        "data_ok": res.get("ok", False),
        "data_error": res.get("error", ""),
        "fetched_at": res.get("fetched_at", ""),
        "build": ds.build(data),
        "counts": ds.counts(data),
        "meta": ds.meta(data),
    }


# ---------------------------------------------------------------------------
# Liveness
# ---------------------------------------------------------------------------
@app.get("/healthz")
async def healthz() -> dict[str, Any]:
    """Liveness probe (Railway). Unauthenticated, no network dependency."""
    return {"status": "ok", "service": "dashboard"}


# ---------------------------------------------------------------------------
# Read-only oversight pages — the point of this service.
# ---------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    ctx = await _base_ctx(request, "home")
    data = ctx["data"]
    ctx.update(
        {
            "groups": ds.catalogue_by_category(data),
            "updates": ds.updates(data)[:6],
            "open_bugs": ds.open_bugs(data),
            "command_stats": ds.command_stats(data),
        }
    )
    return templates.TemplateResponse(request, "index.html", ctx)


@app.get("/functions", response_class=HTMLResponse)
async def functions(request: Request):
    ctx = await _base_ctx(request, "functions")
    ctx.update({"groups": ds.catalogue_by_category(ctx["data"])})
    return templates.TemplateResponse(request, "functions.html", ctx)


@app.get("/commands", response_class=HTMLResponse)
async def commands(request: Request):
    ctx = await _base_ctx(request, "commands")
    data = ctx["data"]
    ctx.update(
        {
            "commands": ds.all_commands(data),
            "cogs": ds.cogs(data),
            "stats": ds.command_stats(data),
            "categories": [
                {"id": cat, "label": m["label"]}
                for cat, m, _ in ds.catalogue_by_category(data)
            ],
            "sysmap": {c["key"]: c for c in ds.catalogue(data)},
        }
    )
    return templates.TemplateResponse(request, "commands.html", ctx)


@app.get("/aliases", response_class=HTMLResponse)
async def aliases(request: Request):
    ctx = await _base_ctx(request, "aliases")
    data = ctx["data"]
    ctx.update(
        {
            "commands_list": ds.command_names(data),
            "taken": ds.build_taken_map(data),
            "synonyms": ds.synonyms(data),
        }
    )
    return templates.TemplateResponse(request, "aliases.html", ctx)


@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    ctx = await _base_ctx(request, "settings")
    ctx.update({"settings": ds.settings(ctx["data"])})
    return templates.TemplateResponse(request, "settings.html", ctx)


@app.get("/access", response_class=HTMLResponse)
async def access_page(request: Request):
    ctx = await _base_ctx(request, "access")
    ctx.update({"access": ds.access(ctx["data"])})
    return templates.TemplateResponse(request, "access.html", ctx)


@app.get("/env", response_class=HTMLResponse)
async def env_page(request: Request):
    ctx = await _base_ctx(request, "env")
    ctx.update({"env_usage": ds.env_usage(ctx["data"]), "source_url": ds.source_url})
    return templates.TemplateResponse(request, "env.html", ctx)


@app.get("/ideas", response_class=HTMLResponse)
async def ideas_page(request: Request):
    ctx = await _base_ctx(request, "ideas")
    ctx.update({"ideas": ds.ideas(ctx["data"])})
    return templates.TemplateResponse(request, "ideas.html", ctx)


@app.get("/bugs", response_class=HTMLResponse)
async def bugs_page(request: Request):
    ctx = await _base_ctx(request, "bugs")
    data = ctx["data"]
    ctx.update({"bugs": ds.bugs(data), "open_bugs": ds.open_bugs(data)})
    return templates.TemplateResponse(request, "bugs.html", ctx)


@app.get("/updates", response_class=HTMLResponse)
async def updates_page(request: Request):
    ctx = await _base_ctx(request, "updates")
    ctx.update({"updates": ds.updates(ctx["data"])})
    return templates.TemplateResponse(request, "updates.html", ctx)


@app.get("/console", response_class=HTMLResponse)
async def console_page(request: Request):
    """Owner one-glance console — fed by superbot's committed ``console.json``."""
    ctx = await _base_ctx(request, "console")
    cres = await ds.fetch_console(refresh=_refresh(request))
    cdata = cres.get("data", {}) or {}
    ctx.update(
        {
            "console_ok": cres.get("ok", False),
            "console_error": cres.get("error", ""),
            "console_meta": cdata.get("meta", {}) or {},
            "sessions": cdata.get("sessions", []) or [],
            "console_ideas": cdata.get("ideas", []) or [],
            "console_bugs": cdata.get("bugs", []) or [],
            "console_changelog": cdata.get("bot_changelog", []) or [],
        }
    )
    return templates.TemplateResponse(request, "console.html", ctx)


@app.get("/status", response_class=HTMLResponse)
async def status_page(request: Request):
    ctx = await _base_ctx(request, "status")
    data = ctx["data"]
    count_links = {
        "functions": ("Subsystems", "/functions"),
        "cogs": ("Cogs", "/commands"),
        "commands": ("Commands", "/commands"),
        "setting_keys": ("Setting keys", "/settings"),
        "setting_domains": ("Setting domains", "/settings"),
        "synonyms": ("Synonyms", "/aliases"),
        "env_vars": ("Env vars", "/env"),
        "ideas": ("Ideas", "/ideas"),
        "bugs": ("Bugs", "/bugs"),
        "updates": ("Updates", "/updates"),
        "visible_subsystems": ("Visible subsystems", "/access"),
    }
    c = ds.counts(data)
    cards = [
        {"key": k, "label": label, "href": href, "value": c.get(k, 0)}
        for k, (label, href) in count_links.items()
    ]
    ctx.update(
        {
            "cards": cards,
            "open_bugs": ds.open_bugs(data),
            "bugs_total": len(ds.bugs(data)),
        }
    )
    return templates.TemplateResponse(request, "status.html", ctx)


@app.get("/palette.json")
async def palette(request: Request):
    """Command-palette index (pages + subsystems + commands)."""
    res = await ds.fetch_dashboard(refresh=_refresh(request))
    data = res.get("data", {}) or {}
    items: list[dict[str, str]] = [
        {"group": "Pages", "label": "Overview", "href": "/"},
        {"group": "Pages", "label": "Functions", "href": "/functions"},
        {"group": "Pages", "label": "Commands", "href": "/commands"},
        {"group": "Pages", "label": "Aliases", "href": "/aliases"},
        {"group": "Pages", "label": "Settings", "href": "/settings"},
        {"group": "Pages", "label": "Access", "href": "/access"},
        {"group": "Pages", "label": "Env map", "href": "/env"},
        {"group": "Pages", "label": "Ideas", "href": "/ideas"},
        {"group": "Pages", "label": "Bugs", "href": "/bugs"},
        {"group": "Pages", "label": "Updates", "href": "/updates"},
        {"group": "Pages", "label": "Console", "href": "/console"},
        {"group": "Pages", "label": "Status", "href": "/status"},
    ]
    for entry in ds.catalogue(data):
        key = entry.get("key")
        if key:
            items.append(
                {
                    "group": "Subsystems",
                    "label": entry.get("display_name") or key,
                    "sub": entry.get("category") or "",
                    "href": "/functions",
                }
            )
    for name in ds.command_names(data):
        items.append({"group": "Commands", "label": name, "code": f"!{name}", "href": f"/commands#cmd-{name}"})
    return JSONResponse(items)


# ===========================================================================
# Control panel — DELIBERATE, CLEARLY-LABELED STUB (plan Q4).
#
# superbot's dashboard control panel signs in with Discord OAuth and WRITES the
# LIVE PRODUCTION BOT's control API (settings / help / cog-routing, applied live),
# plus an owner-gated submissions-moderation ring. That live-write path couples
# websites to the running production bot across the repo boundary and is an owner
# decision (plan Q4) — so it is NOT wired here. This route renders the UI so the
# shape is visible, but every mutating action is a disabled placeholder and NO
# production bot control-API URL or token exists anywhere in this service.
# ===========================================================================
@app.get("/admin", response_class=HTMLResponse)
async def admin_stub(request: Request):
    ctx = await _base_ctx(request, "admin")
    return templates.TemplateResponse(request, "admin.html", ctx)


@app.exception_handler(404)
async def not_found(request: Request, exc: Any):
    # The 404 handler runs OUTSIDE the auth middleware short-circuit for unknown
    # paths that passed the gate; render a simple in-system 404.
    try:
        ctx = await _base_ctx(request, "")
    except Exception:  # pragma: no cover - never fail the error page on data
        ctx = {"request": request, "active": "", "nav": NAV, "data_ok": False, "counts": {}, "build": {}}
    return templates.TemplateResponse(request, "not_found.html", ctx, status_code=404)
