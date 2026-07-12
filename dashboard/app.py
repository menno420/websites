"""SuperBot developer dashboard — private, server-rendered oversight site.

The **private** half of the websites estate (plan
``docs/planning/dashboard-botsite-rework-plan-2026-07-09.md``). Rebuilt on this repo's
substrate — FastAPI + Jinja2, server-rendered, no build step — from superbot's
``dashboard/``: same read-only ideas and functionality, fresh implementation on the
shared ``ds/`` design system.

**Public.** Every route serves without credentials (owner decision [D-0011] — the
Basic-auth gate was dropped). The surface is read-only oversight of public data
(superbot's committed ``dashboard.json`` / ``console.json``); it holds no secret and no
bot control credential, so there is nothing to gate. ``/healthz`` is the Railway probe.

**Data.** The read-only oversight pages consume superbot's committed ``dashboard.json`` /
``console.json`` live over raw.githubusercontent.com (``data_source``). This app **never
imports bot code** and holds **no bot control credential**. A failed feed renders an
honest banner — never faked data.

**The control panel (the deliberate boundary — DRY-RUN).** superbot's dashboard also has
a Discord-OAuth control panel that WRITES the *live production bot's* control API
(settings / help / cog-routing, applied live), plus an owner-gated submissions-moderation
ring. That live-write path is **NOT wired here** (plan Q4 / Q-0004 is an open owner
decision, and doctrine places a wired panel in a **separate** service): ``/admin`` is a
complete management UX running against an explicit **dry-run controller seam**
(``dashboard/control_plane.py``). Every action is validated against the live typed
schema, previewed as the exact contract-v1 request JSON (spec
``docs/specs/bot-control-api-v1.md``), and on confirm recorded to an in-memory audit log
that clears on restart — nothing is ever sent, and **no** production bot control-API URL
or token is referenced anywhere in this service. See ``docs/dashboard.md``.

Deploy: a new Railway service in ``superbot-websites`` (Root Directory = ``dashboard``),
own Dockerfile, binds ``0.0.0.0:$PORT``.
"""

from __future__ import annotations

import json
import os
import urllib.parse
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import control_plane as cp
from . import data_source as ds

BASE_DIR = Path(__file__).resolve().parent

# Primary read-only oversight nav. The control panel (dry-run) is linked apart.
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
        # Cross-repo schema pin: '' when the fetched feed matches the version this
        # consumer was built against; an honest drift message otherwise (base.html
        # banners it on every page — never a crash, never a silent misrender).
        "schema_warning": ds.dashboard_schema_issue(data) if res.get("ok", False) else "",
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
        "service": "dashboard",
        "sha": sha or "unknown",
        "short": sha[:8] if sha else "unknown",
    }


@app.get("/version")
async def version() -> dict[str, Any]:
    """Deployed SHA (unauthenticated, no network dependency). The control-plane
    readiness board queries this to compute the deploy-state drift cell."""
    return _version_info()


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
    """Owner one-glance console — fed by superbot's committed ``console.json``.

    The feed's shape is pinned by the cross-repo contract
    (``dashboard/console_data_contract.json``, a copy of the canonical contract in
    superbot); a drifted feed renders an honest schema banner rather than a
    silently wrong page. ``ideas``/``bugs`` are contracted as counter DICTS
    (``{total, by_status, …}``), not lists.
    """
    ctx = await _base_ctx(request, "console")
    cres = await ds.fetch_console(refresh=_refresh(request))
    cdata = cres.get("data", {}) or {}
    ideas = cdata.get("ideas")
    bugs = cdata.get("bugs")
    ctx.update(
        {
            "console_ok": cres.get("ok", False),
            "console_error": cres.get("error", ""),
            "console_schema_warning": (
                ds.console_contract_issue(cdata) if cres.get("ok") else ""
            ),
            "console_meta": cdata.get("meta", {}) or {},
            "sessions": cdata.get("sessions", []) or [],
            "console_ideas": ideas if isinstance(ideas, dict) else {},
            "console_bugs": bugs if isinstance(bugs, dict) else {},
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
# Control panel — DRY-RUN management UX (plan Q4 / Q-0004 stays an open owner
# decision).
#
# superbot's dashboard control panel signs in with Discord OAuth and WRITES the
# LIVE PRODUCTION BOT's control API (settings / help / cog-routing, applied live),
# plus an owner-gated submissions-moderation ring. That live-write path couples
# websites to the running production bot across the repo boundary; doctrine also
# places a wired control panel in a SEPARATE service, never on this read-only
# surface. So the complete management UX here runs against the DRY-RUN controller
# seam (dashboard/control_plane.py): actions are validated against the live typed
# schema from dashboard.json, previewed as the exact contract-v1 request JSON
# (docs/specs/bot-control-api-v1.md), and on confirm recorded to an in-memory
# audit log that clears on restart. Nothing is ever sent anywhere, and NO
# production bot control-API URL or token exists anywhere in this service.
# ===========================================================================
async def _form_fields(request: Request) -> dict[str, str]:
    """Parse a urlencoded POST body with the stdlib (no form-parsing dependency)."""
    body = (await request.body()).decode("utf-8", "replace")
    return dict(urllib.parse.parse_qsl(body, keep_blank_values=True))


def _cog_rows(data: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for cog in ds.cogs(data):
        rows.append(
            {
                "cog": cog.get("cog") or "",
                "file": cog.get("file") or "",
                "subsystem": cog.get("subsystem") or "",
                "is_cog": bool(cog.get("is_cog")),
                "command_count": len(cog.get("commands") or []),
            }
        )
    return rows


@app.get("/admin", response_class=HTMLResponse)
async def admin_overview(request: Request):
    ctx = await _base_ctx(request, "admin")
    data = ctx["data"]
    settings = ds.settings(data)
    cogs = _cog_rows(data)
    ctx.update(
        {
            "settings": settings,
            "setting_key_total": sum(len(d.get("keys") or []) for d in settings),
            "cog_total": sum(1 for c in cogs if c["is_cog"]),
            "command_total": len(ds.all_commands(data)),
            "audit_count": len(cp.controller.entries()),
            "controller_mode": cp.controller.mode,
        }
    )
    return templates.TemplateResponse(request, "admin.html", ctx)


@app.get("/admin/settings/{domain}", response_class=HTMLResponse)
async def admin_settings_domain(request: Request, domain: str):
    ctx = await _base_ctx(request, "admin")
    dom = next((d for d in ds.settings(ctx["data"]) if d.get("domain") == domain), None)
    if dom is None:
        raise HTTPException(status_code=404)
    ctx.update({"domain": dom})
    return templates.TemplateResponse(request, "admin_settings_domain.html", ctx)


@app.get("/admin/cogs", response_class=HTMLResponse)
async def admin_cogs(request: Request):
    ctx = await _base_ctx(request, "admin")
    ctx.update({"cog_rows": _cog_rows(ctx["data"])})
    return templates.TemplateResponse(request, "admin_cogs.html", ctx)


@app.get("/admin/help", response_class=HTMLResponse)
async def admin_help(request: Request):
    ctx = await _base_ctx(request, "admin")
    data = ctx["data"]
    ctx.update(
        {
            "command_names": ds.command_names(data),
            "subsystem_keys": sorted(c.get("key") for c in ds.catalogue(data) if c.get("key")),
        }
    )
    return templates.TemplateResponse(request, "admin_help.html", ctx)


@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login(request: Request):
    """Honest OAuth scaffold: sign-in is NOT configured on this deployment — and
    per doctrine it never will be on this service (the armed panel is a separate
    service; the future env-var names live in docs/specs, not in this code)."""
    ctx = await _base_ctx(request, "admin")
    return templates.TemplateResponse(request, "admin_login.html", ctx)


@app.get("/admin/audit", response_class=HTMLResponse)
async def admin_audit(request: Request):
    ctx = await _base_ctx(request, "admin")
    ctx.update({"entries": list(reversed(cp.controller.entries()))})
    return templates.TemplateResponse(request, "admin_audit.html", ctx)


def _rejected(request: Request, ctx: dict[str, Any], action: str, exc: cp.ActionRejected):
    """Honest 400 for an action that failed typed validation — nothing recorded."""
    ctx.update({"reject_code": exc.code, "reject_message": str(exc), "action": action})
    return templates.TemplateResponse(request, "admin_rejected.html", ctx, status_code=400)


@app.post("/admin/actions/preview", response_class=HTMLResponse)
async def admin_action_preview(request: Request):
    """Step 1 of the dry-run flow: validate + show the exact request JSON."""
    form = await _form_fields(request)
    ctx = await _base_ctx(request, "admin")
    action = form.get("action", "")
    try:
        req = cp.controller.build_request(action, form, ctx["data"])
    except cp.ActionRejected as exc:
        return _rejected(request, ctx, action, exc)
    carry = [(k, v) for k, v in form.items() if k not in ("idempotency_key", "requested_at")]
    carry += [("idempotency_key", req["idempotency_key"]), ("requested_at", req["requested_at"])]
    ctx.update({"action": action, "request_json": json.dumps(req, indent=2), "carry": carry})
    return templates.TemplateResponse(request, "admin_preview.html", ctx)


@app.post("/admin/actions/confirm", response_class=HTMLResponse)
async def admin_action_confirm(request: Request):
    """Step 2: re-validate the carried fields, record the dry-run audit entry."""
    form = await _form_fields(request)
    ctx = await _base_ctx(request, "admin")
    action = form.get("action", "")
    try:
        req = cp.controller.build_request(
            action,
            form,
            ctx["data"],
            idempotency_key=form.get("idempotency_key") or None,
            requested_at=form.get("requested_at") or None,
        )
    except cp.ActionRejected as exc:
        return _rejected(request, ctx, action, exc)
    entry = cp.controller.record(req)
    ctx.update({"entry": entry, "request_json": json.dumps(req, indent=2)})
    return templates.TemplateResponse(request, "admin_result.html", ctx)


@app.exception_handler(404)
async def not_found(request: Request, exc: Any):
    # No middleware runs in this service (public by [D-0011]); just render a
    # simple in-system 404 page.
    try:
        ctx = await _base_ctx(request, "")
    except Exception:  # pragma: no cover - never fail the error page on data
        ctx = {"request": request, "active": "", "nav": NAV, "data_ok": False, "counts": {}, "build": {}}
    return templates.TemplateResponse(request, "not_found.html", ctx, status_code=404)
