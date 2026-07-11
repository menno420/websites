"""Program review site — how an owner + Claude-agent fleet ships, told honestly.

The FOURTH independent service in the websites repo (alongside control-plane,
botsite, dashboard — same pattern: own Dockerfile, own requirements, own
tests, server-rendered FastAPI + Jinja2 on the vendored ``ds/`` design system,
no build step, no client-side framework).

**Purpose.** Built for Anthropic reviewers looking at how this program runs:
one human owner who designs and directs but does not code, and a fleet of
Claude agents that build, verify, and coordinate through committed git files.
The site gives a visual, plain-English account of the process (the substrate
workflow), the growth (real per-day numbers from git history), the successes,
and — deliberately first-class — the problems. Every claim links to committed
evidence; nothing is marketing prose.

**Data.** Read-only and network-free: the one data source is the committed
``data/snapshot.json``, baked from the real repo record by ``gen_snapshot.py``
at build time (the deployed container ships only this folder, so runtime reads
of git/.sessions/control are impossible by design — see that module's
docstring). A missing or corrupt snapshot renders an honest banner, never
invented numbers. Charts are server-rendered inline SVG; geometry is computed
in the domain layer (``story.py``) so it stays unit-testable.

Deploy: a new Railway service in ``superbot-websites`` (Root Directory =
``review``), own Dockerfile, binds ``0.0.0.0:$PORT`` — queued as an
⚑ OWNER-ACTION in ``docs/owner/OWNER-ACTIONS.md``.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import story

BASE_DIR = Path(__file__).resolve().parent

NAV = [
    ("overview", "Overview", "/"),
    ("process", "Process", "/process"),
    ("growth", "Growth", "/growth"),
    ("successes", "Successes", "/successes"),
    ("problems", "Problems", "/problems"),
]

app = FastAPI(title="Program Review", docs_url=None, redoc_url=None, openapi_url=None)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def _base_ctx(request: Request, active: str) -> dict[str, Any]:
    snap = story.load_snapshot()
    return {
        "request": request,
        "active": active,
        "nav": NAV,
        "snap_ok": snap["ok"],
        "snap_error": snap["error"],
        "snapshot": snap["data"],
        "totals": (snap["data"].get("totals") or {}) if snap["ok"] else {},
        "generated_at": snap["data"].get("generated_at", "") if snap["ok"] else "",
        "git_head": snap["data"].get("git_head", "") if snap["ok"] else "",
        "repo_url": story.REPO_URL,
    }


# ---------------------------------------------------------------------------
# Liveness + version — the estate-standard probes (Railway + the drift cell).
# ---------------------------------------------------------------------------
@app.get("/healthz")
async def healthz() -> dict[str, Any]:
    """Liveness probe. Unauthenticated, no network dependency."""
    return {"status": "ok", "service": "review"}


@app.get("/version")
async def version() -> dict[str, Any]:
    """Deployed SHA — ``RAILWAY_GIT_COMMIT_SHA`` (primary) -> ``GIT_SHA``
    (Docker build-arg fallback) -> honest ``"unknown"``."""
    sha = (os.environ.get("RAILWAY_GIT_COMMIT_SHA") or os.environ.get("GIT_SHA") or "").strip()
    return {"service": "review", "sha": sha or "unknown", "short": sha[:8] if sha else "unknown"}


@app.get("/story.json")
async def story_json() -> JSONResponse:
    """The snapshot the pages render from — machine-readable, same honesty."""
    snap = story.load_snapshot()
    return JSONResponse({"ok": snap["ok"], "error": snap["error"], "snapshot": snap["data"]})


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def overview(request: Request):
    ctx = _base_ctx(request, "overview")
    ctx.update(
        {
            "stats": story.overview_stats(ctx["snapshot"]),
            "services": story.SERVICES,
            "days": ctx["snapshot"].get("days", []) if ctx["snap_ok"] else [],
        }
    )
    return templates.TemplateResponse(request, "index.html", ctx)


@app.get("/process", response_class=HTMLResponse)
async def process(request: Request):
    ctx = _base_ctx(request, "process")
    ctx.update({"landing_path": story.LANDING_PATH, "glossary": story.GLOSSARY})
    return templates.TemplateResponse(request, "process.html", ctx)


@app.get("/growth", response_class=HTMLResponse)
async def growth(request: Request):
    ctx = _base_ctx(request, "growth")
    ctx.update(
        {
            "charts": story.growth_charts(ctx["snapshot"]) if ctx["snap_ok"] else [],
            "milestones": story.MILESTONES,
            "days": ctx["snapshot"].get("days", []) if ctx["snap_ok"] else [],
        }
    )
    return templates.TemplateResponse(request, "growth.html", ctx)


@app.get("/successes", response_class=HTMLResponse)
async def successes(request: Request):
    ctx = _base_ctx(request, "successes")
    ctx.update({"items": story.SUCCESSES})
    return templates.TemplateResponse(request, "successes.html", ctx)


@app.get("/problems", response_class=HTMLResponse)
async def problems(request: Request):
    ctx = _base_ctx(request, "problems")
    ctx.update({"items": story.PROBLEMS})
    return templates.TemplateResponse(request, "problems.html", ctx)


@app.exception_handler(404)
async def not_found(request: Request, exc: Any):
    ctx = _base_ctx(request, "")
    return templates.TemplateResponse(request, "not_found.html", ctx, status_code=404)
