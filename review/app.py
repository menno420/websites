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
in the domain layer (``story.py``) so it stays unit-testable. ORDER 017 added
ONE deliberate exception to the network-free rule: the AI assistant's
server-side Anthropic API call in ``ai.py`` (nothing else gained network).

Deploy: a new Railway service in ``superbot-websites`` (Root Directory =
``review``), own Dockerfile, binds ``0.0.0.0:$PORT`` — queued as an
⚑ OWNER-ACTION in ``docs/owner/OWNER-ACTIONS.md``.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import ai, editions, fleetdata, listfilter, story

BASE_DIR = Path(__file__).resolve().parent

NAV = [
    ("overview", "Overview", "/"),
    ("process", "Process", "/process"),
    ("growth", "Growth", "/growth"),
    ("fleet", "Fleet", "/fleet"),
    ("reviews", "Reviews", "/reviews"),
    ("questionnaire", "Q&A", "/questionnaire"),
    ("ask", "Ask AI", "/ask"),
    ("successes", "Successes", "/successes"),
    ("problems", "Problems", "/problems"),
]

app = FastAPI(title="Program Review", docs_url=None, redoc_url=None, openapi_url=None)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# ORDER 017 workstream B: the AI assistant's POST endpoint (/ask/api) — the
# service's one deliberate runtime-network exception; see review/ai.py.
app.include_router(ai.router)


def _deployed_sha() -> str:
    return (os.environ.get("RAILWAY_GIT_COMMIT_SHA") or os.environ.get("GIT_SHA") or "").strip()


def _base_ctx(request: Request, active: str) -> dict[str, Any]:
    snap = story.load_snapshot()
    git_head = snap["data"].get("git_head", "") if snap["ok"] else ""
    deployed = _deployed_sha()
    # Footer "last refreshed" stamps — from the committed data files, never
    # hardcoded. Each mirror stamps its own bake time; absence stays honest.
    fl = fleetdata.load_fleet()
    fleet_generated_at = fl["data"].get("generated_at", "") if fl["ok"] else ""
    return {
        "request": request,
        "active": active,
        "nav": NAV,
        "snap_ok": snap["ok"],
        "snap_error": snap["error"],
        "snapshot": snap["data"],
        "totals": (snap["data"].get("totals") or {}) if snap["ok"] else {},
        "generated_at": snap["data"].get("generated_at", "") if snap["ok"] else "",
        "git_head": git_head,
        # Snapshot-aging honesty (the backlog's snapshot-aging idea, built):
        # when the deployed commit is known and is NOT the snapshot's source
        # commit, the repo has moved since the numbers were baked — say so.
        "snapshot_aged": bool(deployed and git_head and deployed[:8] != git_head[:8]),
        "deployed_sha": deployed,
        "fleet_generated_at": fleet_generated_at,
        "repo_url": story.REPO_URL,
        # "Room to interact", read-only: a prefilled new-issue link per page.
        "ask_url": story.ask_url(f"{active or 'site'} page"),
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
    """ORDER 017 C: the 30-second front door — what-this-is, the key-stats
    row (snapshot + fleet mirror, never literals), the five start-here
    findings, the AI panel, the site map, and the evidence links."""
    ctx = _base_ctx(request, "overview")
    fl = fleetdata.load_fleet()
    fleet_data = fl["data"] if fl["ok"] else {}
    seats_count = len(fleet_data.get("seats") or []) or None
    ctx.update(
        {
            "stats": story.homepage_stats(ctx["snapshot"], fleet_data),
            "start_here": story.START_HERE,
            "site_map": story.site_map(seats_count),
            "evidence_links": story.EVIDENCE_LINKS,
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


# ---------------------------------------------------------------------------
# Fleet — every seat in the manager's registry, from the committed mirror.
# ---------------------------------------------------------------------------
@app.get("/fleet", response_class=HTMLResponse)
async def fleet(request: Request):
    """ORDER 019 PR2: the lanes grid gains the centralized listfilter widget
    (disposition / derived heartbeat-freshness / seat dimensions + lane/repo/
    seat search, defined in fleetdata.py); the default sort keeps the
    existing disposition order, so no params renders exactly as before."""
    ctx = _base_ctx(request, "fleet")
    fl = fleetdata.load_fleet()
    st = fleetdata.load_stats()
    overview = fleetdata.fleet_overview(fl["data"], st["data"]) if fl["ok"] else {}
    lanes_filter = None
    if fl["ok"]:
        lanes = fleetdata.annotate_lane_seats(
            overview.get("lanes", []), fleetdata.seat_by_repo(fl["data"])
        )
        state = listfilter.parse(
            fleetdata.LANES_FILTER_SPEC, request.query_params
        )
        lanes_filter = listfilter.apply(
            fleetdata.LANES_FILTER_SPEC, lanes, state
        )
    ctx.update(
        {
            "fleet_ok": fl["ok"],
            "fleet_error": fl["error"],
            "stats_ok": st["ok"],
            "stats_error": st["error"],
            "overview": overview,
            "lanes_filter": lanes_filter,
            "seats": fleetdata.seats_view(fl["data"]) if fl["ok"] else None,
            "fleet_age": fleetdata.freshness(fl["data"].get("generated_at", "")) if fl["ok"] else None,
            "stats_age": fleetdata.freshness(st["data"].get("generated_at", "")) if st["ok"] else None,
        }
    )
    return templates.TemplateResponse(request, "fleet.html", ctx)


@app.get("/fleet.json")
async def fleet_json() -> JSONResponse:
    """The fleet + stats mirrors, machine-readable — same honesty as the page."""
    fl = fleetdata.load_fleet()
    st = fleetdata.load_stats()
    return JSONResponse(
        {
            "fleet": {"ok": fl["ok"], "error": fl["error"], "data": fl["data"]},
            "stats": {"ok": st["ok"], "error": st["error"], "data": st["data"]},
        }
    )


@app.get("/fleet/{repo}", response_class=HTMLResponse)
async def fleet_repo(request: Request, repo: str):
    ctx = _base_ctx(request, "fleet")
    fl = fleetdata.load_fleet()
    st = fleetdata.load_stats()
    lane = fleetdata.lane_detail(fl["data"], st["data"], repo) if fl["ok"] else None
    if lane is None:
        ctx["fleet_error"] = fl["error"]
        return templates.TemplateResponse(request, "not_found.html", ctx, status_code=404)
    ctx.update(
        {
            "lane": lane,
            "fleet_age": fleetdata.freshness(fl["data"].get("generated_at", "")),
            "stats_age": fleetdata.freshness(st["data"].get("generated_at", "")) if st["ok"] else None,
            "stats_ok": st["ok"],
            "stats_error": st["error"],
            "ask_url": story.ask_url(f"fleet repo {repo}"),
        }
    )
    return templates.TemplateResponse(request, "fleet_detail.html", ctx)


# ---------------------------------------------------------------------------
# Reviews — dated editions + Atom feed (the continuous-review channel).
# ---------------------------------------------------------------------------
@app.get("/reviews", response_class=HTMLResponse)
async def reviews(request: Request):
    """ORDER 019 PR2: filter/sort/search over the centralized listfilter core
    (month dimension + title/summary search, defined in editions.py); no
    params renders exactly the pre-filter page."""
    ctx = _base_ctx(request, "reviews")
    all_editions = editions.list_editions()
    state = listfilter.parse(editions.FILTER_SPEC, request.query_params)
    ctx.update(
        {
            "editions": all_editions,
            "editions_filter": listfilter.apply(
                editions.FILTER_SPEC, all_editions, state
            ),
        }
    )
    return templates.TemplateResponse(request, "reviews.html", ctx)


@app.get("/reviews/feed.xml")
async def reviews_feed(request: Request) -> Response:
    xml = editions.atom_feed(editions.list_editions(), str(request.base_url))
    return Response(content=xml, media_type="application/atom+xml")


@app.get("/reviews/{slug}", response_class=HTMLResponse)
async def review_edition(request: Request, slug: str):
    ctx = _base_ctx(request, "reviews")
    edition = editions.get_edition(slug)
    if edition is None:
        return templates.TemplateResponse(request, "not_found.html", ctx, status_code=404)
    ctx.update(
        {
            "edition": edition,
            "body_html": editions.render_markdown(edition["body_md"]),
            "ask_url": story.ask_url(f"review edition {slug}"),
        }
    )
    return templates.TemplateResponse(request, "edition.html", ctx)


# ---------------------------------------------------------------------------
# Questionnaire + questions ledger (interaction, read-only by design).
# ---------------------------------------------------------------------------
@app.get("/questionnaire", response_class=HTMLResponse)
async def questionnaire(request: Request):
    ctx = _base_ctx(request, "questionnaire")
    ctx.update({"items": story.QUESTIONNAIRE})
    return templates.TemplateResponse(request, "questionnaire.html", ctx)


@app.get("/ask", response_class=HTMLResponse)
async def ask(request: Request):
    """The AI assistant page (ORDER 017 B): Ask/Review widget + the seeded
    evidence-backed answers, honest about the degraded no-key state."""
    ctx = _base_ctx(request, "ask")
    ctx.update(ai.page_context())
    return templates.TemplateResponse(request, "ask.html", ctx)


@app.get("/questions", response_class=HTMLResponse)
async def questions(request: Request):
    """ORDER 019 PR2: filter/sort/search over the centralized listfilter core
    (status / answered dimensions + title search, defined in story.py); no
    params renders exactly the pre-filter page."""
    ctx = _base_ctx(request, "questionnaire")
    q = story.load_questions()
    records = q["data"].get("questions") or [] if q["ok"] else []
    state = listfilter.parse(story.QUESTIONS_FILTER_SPEC, request.query_params)
    ctx.update(
        {
            "q_ok": q["ok"],
            "q_error": q["error"],
            "ledger": q["data"],
            "q_filter": listfilter.apply(
                story.QUESTIONS_FILTER_SPEC, records, state
            ),
        }
    )
    return templates.TemplateResponse(request, "questions.html", ctx)


@app.exception_handler(404)
async def not_found(request: Request, exc: Any):
    ctx = _base_ctx(request, "")
    return templates.TemplateResponse(request, "not_found.html", ctx, status_code=404)
