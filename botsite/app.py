"""SuperBot public bot site — server-rendered marketing + reference site.

The **public** half of the websites estate (plan
``docs/planning/dashboard-botsite-rework-plan-2026-07-09.md``). Rebuilt on this repo's
substrate — FastAPI + Jinja2, server-rendered, no build step — from superbot's
``botsite/``: same ideas and functionality, fresh implementation on the shared ``ds/``
design system.

Data: the committed public subset ``site.json``, fetched live from the superbot repo
over raw.githubusercontent.com (``data_source``). This app **never imports bot code**
and holds **no secret** — it is the public, secret-free marketing surface. The future
gated control panel is a *separate service*, never a router mounted here.

``/submit`` ships its form; the DB write path is a clearly-labeled stub until the
submissions Postgres is provisioned (owner-deferred question Q5 in the plan).

Deploy: a new Railway service in ``superbot-websites`` (Root Directory = ``botsite``),
own Dockerfile, binds ``0.0.0.0:$PORT``. See ``botsite/README.md`` and
``docs/botsite.md``.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import data_source as ds
from . import testing

BASE_DIR = Path(__file__).resolve().parent
NAV = [
    ("features", "Features", "/features"),
    ("commands", "Commands", "/commands"),
    ("games", "Games", "/games"),
    ("testing", "Testing", "/testing"),
    ("changelog", "Changelog", "/changelog"),
    ("status", "Status", "/status"),
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    if ds._client is None:  # tests may pre-set a client; don't clobber it
        ds.set_client(ds.make_client())
    try:
        await ds.fetch_site()  # warm the cache; failure is non-fatal (pages degrade)
    except Exception:  # pragma: no cover - never block startup on the network
        pass
    yield
    await ds._get_client().aclose()


app = FastAPI(title="SuperBot", lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
# Tester-recruitment program (ORDER 018): public claim/submit flow + gated
# owner queue, all under /testing (see botsite/testing.py).
app.include_router(testing.router)


def _base_ctx(request: Request, active: str, site_res: dict[str, Any]) -> dict[str, Any]:
    site = site_res.get("data", {}) or {}
    return {
        "request": request,
        "active": active,
        "nav": NAV,
        "add_url": ds.ADD_TO_DISCORD_URL,
        "site_ok": site_res.get("ok", False),
        "site_error": site_res.get("error", ""),
        "build": ds.build_meta(site),
        "counts": ds.counts(site),
    }


def _refresh(request: Request) -> bool:
    return request.query_params.get("refresh") in ("1", "true", "yes")


@app.get("/healthz")
async def healthz() -> dict[str, Any]:
    """Liveness probe (Railway). Unauthenticated, no network dependency."""
    return {"status": "ok", "service": "botsite"}


def _version_info() -> dict[str, Any]:
    """Which commit this container is running (deployed SHA). Read live from the
    env: ``RAILWAY_GIT_COMMIT_SHA`` (Railway injects the deployed commit) first,
    then a build-time ``GIT_SHA`` fallback, then ``"unknown"``."""
    sha = (
        os.environ.get("RAILWAY_GIT_COMMIT_SHA")
        or os.environ.get("GIT_SHA")
        or ""
    ).strip()
    return {
        "service": "botsite",
        "sha": sha or "unknown",
        "short": sha[:8] if sha else "unknown",
    }


@app.get("/version")
async def version() -> dict[str, Any]:
    """Deployed SHA (unauthenticated, no network dependency). The control-plane
    readiness board queries this to compute the deploy-state drift cell."""
    return _version_info()


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    res = await ds.fetch_site(refresh=_refresh(request))
    site = res.get("data", {}) or {}
    ctx = _base_ctx(request, "home", res)
    ctx.update(
        {
            "categories": ds.present_categories(site),
            "changelog": ds.changelog(site)[:3],
        }
    )
    return templates.TemplateResponse(request, "index.html", ctx)


@app.get("/features", response_class=HTMLResponse)
async def features(request: Request):
    res = await ds.fetch_site(refresh=_refresh(request))
    site = res.get("data", {}) or {}
    ctx = _base_ctx(request, "features", res)
    ctx.update({"features": ds.features(site), "categories": ds.present_categories(site)})
    return templates.TemplateResponse(request, "features.html", ctx)


@app.get("/features/{key}", response_class=HTMLResponse)
async def feature_detail(request: Request, key: str):
    res = await ds.fetch_site(refresh=_refresh(request))
    site = res.get("data", {}) or {}
    feature = ds.feature_by_key(site, key)
    if feature is None:
        ctx = _base_ctx(request, "features", res)
        ctx.update({"key": key})
        return templates.TemplateResponse(request, "not_found.html", ctx, status_code=404)
    area_cmds = [c for c in ds.commands(site) if c["category"] == feature["category"]]
    ctx = _base_ctx(request, "features", res)
    ctx.update({"feature": feature, "area_commands": area_cmds})
    return templates.TemplateResponse(request, "feature_detail.html", ctx)


@app.get("/commands", response_class=HTMLResponse)
async def commands(request: Request):
    res = await ds.fetch_site(refresh=_refresh(request))
    site = res.get("data", {}) or {}
    ctx = _base_ctx(request, "commands", res)
    ctx.update({"commands": ds.commands(site), "categories": ds.present_categories(site)})
    return templates.TemplateResponse(request, "commands.html", ctx)


@app.get("/commands/{name}", response_class=HTMLResponse)
async def command_detail(request: Request, name: str):
    res = await ds.fetch_site(refresh=_refresh(request))
    site = res.get("data", {}) or {}
    command = ds.command_by_name(site, name)
    if command is None:
        ctx = _base_ctx(request, "commands", res)
        ctx.update({"key": name, "what": "command"})
        return templates.TemplateResponse(request, "not_found.html", ctx, status_code=404)
    ctx = _base_ctx(request, "commands", res)
    ctx.update({"command": command, "related": ds.related_commands(site, command)})
    return templates.TemplateResponse(request, "command_detail.html", ctx)


@app.get("/games", response_class=HTMLResponse)
async def games(request: Request):
    res = await ds.fetch_site(refresh=_refresh(request))
    site = res.get("data", {}) or {}
    ctx = _base_ctx(request, "games", res)
    ctx.update({"games": ds.games(site)})
    return templates.TemplateResponse(request, "games.html", ctx)


@app.get("/changelog", response_class=HTMLResponse)
async def changelog(request: Request):
    res = await ds.fetch_site(refresh=_refresh(request))
    site = res.get("data", {}) or {}
    ctx = _base_ctx(request, "changelog", res)
    ctx.update(
        {
            "changelog": ds.changelog(site),
            "changelog_kinds": ds.changelog_by_kind(site),
            "changelog_ctx": ds.changelog_context(site),
        }
    )
    return templates.TemplateResponse(request, "changelog.html", ctx)


@app.get("/status", response_class=HTMLResponse)
async def status(request: Request):
    res = await ds.fetch_site(refresh=_refresh(request))
    site = res.get("data", {}) or {}
    ctx = _base_ctx(request, "status", res)
    ctx.update({"systems": ds.systems(site)})
    return templates.TemplateResponse(request, "status.html", ctx)


@app.get("/design", response_class=HTMLResponse)
async def design(request: Request):
    """Living style guide — renders the design-system tokens + components."""
    res = await ds.fetch_site(refresh=_refresh(request))
    ctx = _base_ctx(request, "design", res)
    return templates.TemplateResponse(request, "design.html", ctx)


@app.get("/submit", response_class=HTMLResponse)
async def submit_form(request: Request):
    res = await ds.fetch_site(refresh=_refresh(request))
    ctx = _base_ctx(request, "submit", res)
    ctx.update({"submitted": False})
    return templates.TemplateResponse(request, "submit.html", ctx)


@app.post("/submit", response_class=HTMLResponse)
async def submit_post(request: Request):
    # INTAKE STUB (owner-deferred Q5): the submissions Postgres is not provisioned in
    # superbot-websites yet, so there is no write target. Rather than fake acceptance,
    # the form honestly reports the intake is not live. When the submissions DB + role
    # is provisioned, this handler INSERTs one pending row (INSERT-only DSN, the only
    # secret this public surface may ever hold) and mirrors to a GitHub issue on
    # moderation — exactly superbot's flow, re-provisioned. See docs/botsite.md.
    res = await ds.fetch_site()
    ctx = _base_ctx(request, "submit", res)
    ctx.update({"submitted": True, "intake_live": False})
    return templates.TemplateResponse(request, "submit.html", ctx)


@app.get("/palette.json")
async def palette(request: Request):
    """Command-palette index (pages + features + games + commands)."""
    res = await ds.fetch_site(refresh=_refresh(request))
    return JSONResponse(ds.palette_items(res.get("data", {}) or {}))


@app.exception_handler(404)
async def not_found(request: Request, exc: Any):
    res = await ds.fetch_site()
    ctx = _base_ctx(request, "", res)
    ctx.update({"key": ""})
    return templates.TemplateResponse(request, "not_found.html", ctx, status_code=404)
