"""Control-plane site: readiness board + journal browser.

Public: every route defined here serves without credentials. The board's one
non-public datum, the GitHub Actions secret *names*, is masked to a count (see
readiness.py). The single gated corner is the `/owner` area (app/owner.py,
HTTP Basic on `SITE_PASSWORD`) which un-masks that detail and exposes privileged
actions; it never affects the public routes below. /healthz is the Railway
healthcheck.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import activity, config, fleet, github, ideas, journal, owner, readiness


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = github.make_client()
    raw_client = github.make_raw_client()
    github.set_clients(client, raw_client)
    yield
    await client.aclose()
    await raw_client.aclose()


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

# Static assets (the live-monitoring auto-refresh JS). Public, no credentials —
# served straight from app/static/ (mirrors the credential-free public site).
app.mount(
    "/static",
    StaticFiles(directory=str(Path(__file__).parent / "static")),
    name="static",
)

# The one gated area — /owner and /owner/*. Every route in THIS module stays
# public; the gate lives entirely on the included router.
app.include_router(owner.router)


def _refresh(request: Request) -> bool:
    return request.query_params.get("refresh") in ("1", "true", "yes")


@app.get("/healthz")
async def healthz():
    return {"ok": True, "cache_entries": github.cache_size()}


@app.get("/version")
async def version():
    """The commit this service is running (deployed SHA). Unauthenticated,
    no network dependency — read straight from the environment. Powers the
    readiness board's deploy-state drift cell."""
    return config.version_info("control-plane")


@app.get("/", response_class=HTMLResponse)
async def board(request: Request):
    rows = await readiness.board(refresh=_refresh(request))
    return templates.TemplateResponse(
        request,
        "board.html",
        {
            "rows": rows,
            "ttl": config.CACHE_TTL_SECONDS,
            "active": "board",
            "autorefresh_seconds": config.AUTOREFRESH_SECONDS,
        },
    )


@app.get("/api/readiness.json")
async def board_json(request: Request):
    return JSONResponse(await readiness.board(refresh=_refresh(request)))


@app.get("/activity", response_class=HTMLResponse)
async def activity_timeline(request: Request):
    data = await activity.timeline(refresh=_refresh(request))
    return templates.TemplateResponse(
        request, "activity.html", {"a": data, "active": "activity"}
    )


@app.get("/activity.json")
async def activity_timeline_json(request: Request):
    return JSONResponse(await activity.timeline(refresh=_refresh(request)))


@app.get("/activity.xml")
async def activity_feed(request: Request):
    """The /activity timeline as a subscribable Atom 1.0 feed. Same TTL-cached
    data as /activity — a second serializer, not a second fetch — so a reader or
    webhook can watch fleet PR activity without polling the page."""
    data = await activity.timeline(refresh=_refresh(request))
    base = str(request.base_url).rstrip("/")
    xml = activity.atom_feed(
        data, self_url=f"{base}/activity.xml", alternate_url=f"{base}/activity"
    )
    return Response(content=xml, media_type="application/atom+xml")


@app.get("/fleet", response_class=HTMLResponse)
async def fleet_heartbeat(request: Request):
    data = await fleet.overview(refresh=_refresh(request))
    return templates.TemplateResponse(
        request,
        "fleet.html",
        {
            "f": data,
            "active": "fleet",
            "autorefresh_seconds": config.AUTOREFRESH_SECONDS,
        },
    )


@app.get("/fleet.json")
async def fleet_heartbeat_json(request: Request):
    data = await fleet.overview(refresh=_refresh(request))
    # Drop the rendered markdown body from the JSON payload — callers get the
    # parsed fields + freshness + repo signals and the GitHub deep-link; the
    # rendered HTML is an HTML-view concern only (mirrors /journal/search.json).
    payload = dict(data)
    payload["lanes"] = [
        {k: v for k, v in lane.items() if k != "body_html"} for lane in data["lanes"]
    ]
    return JSONResponse(payload)


@app.get("/ideas", response_class=HTMLResponse)
async def ideas_backlog(request: Request):
    repos = await ideas.overview(refresh=_refresh(request))
    return templates.TemplateResponse(
        request, "ideas.html", {"repos": repos, "active": "ideas"}
    )


@app.get("/ideas.json")
async def ideas_backlog_json(request: Request):
    return JSONResponse(await ideas.overview(refresh=_refresh(request)))


@app.get("/journal", response_class=HTMLResponse)
async def journal_index(request: Request):
    repos = await journal.overview(refresh=_refresh(request))
    return templates.TemplateResponse(
        request, "journal.html", {"repos": repos, "active": "journal"}
    )


@app.get("/journal/search", response_class=HTMLResponse)
async def journal_search(request: Request, q: str = ""):
    # Registered BEFORE /journal/{repo} so "search" is not captured as a repo.
    data = await journal.search_journal(q, refresh=_refresh(request))
    return templates.TemplateResponse(
        request, "journal_search.html", {"s": data, "active": "journal"}
    )


@app.get("/journal/search.json")
async def journal_search_json(request: Request, q: str = ""):
    data = await journal.search_journal(q, refresh=_refresh(request))
    # Drop the HTML snippet from the JSON payload — callers get the plain text
    # snippet plus the deep-link; the highlighted variant is HTML-view only.
    payload = dict(data)
    payload["results"] = [
        {k: v for k, v in r.items() if k != "snippet_html"}
        for r in data["results"]
    ]
    return JSONResponse(payload)


@app.get("/journal/{repo}", response_class=HTMLResponse)
async def journal_repo(request: Request, repo: str):
    if repo not in config.REPOS:
        return HTMLResponse("unknown repo", status_code=404)
    data = await journal.repo_journal(repo, refresh=_refresh(request))
    return templates.TemplateResponse(
        request, "journal_repo.html", {"j": data, "active": "journal"}
    )


@app.get("/journal/{repo}/file", response_class=HTMLResponse)
async def journal_file(request: Request, repo: str, path: str, ref: str = "main"):
    if repo not in config.REPOS:
        return HTMLResponse("unknown repo", status_code=404)
    if ".." in path or path.startswith("/"):
        return HTMLResponse("bad path", status_code=400)
    res = await github.fetch_file(repo, path, ref=ref, refresh=_refresh(request))
    body_html = ""
    if res["ok"] and isinstance(res["data"], str):
        if path.endswith((".md", ".markdown")):
            body_html = journal.render_markdown(res["data"])
        else:
            import html as _html

            body_html = f"<pre>{_html.escape(res['data'])}</pre>"
    return templates.TemplateResponse(
        request,
        "file.html",
        {
            "repo": repo,
            "path": path,
            "ref": ref,
            "res": res,
            "body_html": body_html,
            "github_url": f"https://github.com/{config.OWNER}/{repo}/blob/{ref}/{path}",
            "active": "journal",
        },
    )
