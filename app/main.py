"""Control-plane site: readiness board + journal browser.

Public: every route defined here serves without credentials. The board's one
non-public datum, the GitHub Actions secret *names*, is masked to a count (see
readiness.py). The single gated corner is the `/owner` area (app/owner.py,
HTTP Basic on `SITE_PASSWORD`) which un-masks that detail and exposes privileged
actions; it never affects the public routes below. /healthz is the Railway
healthcheck.
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import (
    activity,
    config,
    environments,
    fleet,
    github,
    ideas,
    journal,
    nav,
    orders,
    owner,
    owner_queue,
    projects,
    readiness,
    reviews,
)


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
# Nav manifest as Jinja globals: base.html iterates ONE list (app/nav.py)
# instead of hand-kept markup — the overflow-guard membership lives in
# exactly one place (tests/test_nav_manifest.py holds routes to it).
templates.env.globals["NAV_PRIMARY"] = nav.PRIMARY
templates.env.globals["NAV_GROUPED"] = nav.GROUPED

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
    refresh = _refresh(request)
    # Conveyor-health chips (idea-lifecycle counts per repo) render on the
    # board rows — the owner's habit path — reusing the exact TTL-cached
    # fetches /ideas rides (zero extra fetch on a warm cache). A repo whose
    # ideas listing is missing or errored simply shows no chip here: the
    # board stays a readiness surface; /ideas is the honest home for idea
    # errors/absences.
    repo_names = list(config.REPOS)
    rows, idea_rows, fleet_fresh = await asyncio.gather(
        readiness.board(refresh=refresh),
        ideas.overview(refresh=refresh),
        # Heartbeat-freshness chips: ONLY the board repos' status.md files
        # (TTL-cached) — deliberately not the full 18-lane fleet fan-out.
        asyncio.gather(
            *[fleet.heartbeat_freshness(r, refresh=refresh) for r in repo_names]
        ),
    )
    idea_chips = {
        r["repo"]: {"counts": r["state_counts"], "shown": r["shown"],
                    "total": r["total"]}
        for r in idea_rows
        if r.get("state_counts") and not r.get("listing_error")
    }
    heartbeat_chips = {
        repo: fresh
        for repo, fresh in zip(repo_names, fleet_fresh)
        if fresh is not None
    }
    return templates.TemplateResponse(
        request,
        "board.html",
        {
            "rows": rows,
            "idea_chips": idea_chips,
            "heartbeat_chips": heartbeat_chips,
            "ttl": config.CACHE_TTL_SECONDS,
            "active": "board",
            "autorefresh_seconds": config.AUTOREFRESH_SECONDS,
        },
    )


@app.get("/api/readiness.json")
async def board_json(request: Request):
    return JSONResponse(await readiness.board(refresh=_refresh(request)))


def _repo_param(request: Request) -> str | None:
    """The ``?repo=`` filter value, or None. Validation (unknown repo → an
    honest empty state, never a 500) happens in activity.timeline."""
    value = (request.query_params.get("repo") or "").strip()
    return value or None


@app.get("/activity", response_class=HTMLResponse)
async def activity_timeline(request: Request):
    data = await activity.timeline(
        refresh=_refresh(request), repo=_repo_param(request)
    )
    return templates.TemplateResponse(
        request, "activity.html", {"a": data, "active": "activity"}
    )


@app.get("/activity.json")
async def activity_timeline_json(request: Request):
    return JSONResponse(
        await activity.timeline(refresh=_refresh(request), repo=_repo_param(request))
    )


@app.get("/activity.xml")
async def activity_feed(request: Request):
    """The /activity timeline as a subscribable Atom 1.0 feed. Same TTL-cached
    data as /activity — a second serializer, not a second fetch — so a reader or
    webhook can watch fleet PR activity without polling the page. With ?repo=
    it becomes a per-lane subscription (feed title names the repo)."""
    repo = _repo_param(request)
    data = await activity.timeline(refresh=_refresh(request), repo=repo)
    base = str(request.base_url).rstrip("/")
    suffix = f"?repo={repo}" if repo else ""
    xml = activity.atom_feed(
        data,
        self_url=f"{base}/activity.xml{suffix}",
        alternate_url=f"{base}/activity{suffix}",
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


@app.get("/queue", response_class=HTMLResponse)
async def owner_queue_page(request: Request):
    """ORDER 005: the owner's single to-do surface — every lane's ⚑ needs-owner
    plus the fleet-manager owner-queue, deduplicated, newest first. Degrades
    honestly when GITHUB_TOKEN is unset or the private upstream is unreachable."""
    data = await owner_queue.overview(refresh=_refresh(request))
    return templates.TemplateResponse(
        request, "queue.html", {"q": data, "active": "queue"}
    )


@app.get("/queue.json")
async def owner_queue_json(request: Request):
    """JSON variant of /queue — the manager's machine round-trip: file an ask
    in a lane heartbeat, poll this, confirm it actually surfaces. Same
    overview dict, minus the fleet-manager doc's rendered HTML (an HTML-view
    concern; the /fleet.json precedent)."""
    data = await owner_queue.overview(refresh=_refresh(request))
    payload = dict(data)
    payload["fleet_manager"] = {
        k: v for k, v in data["fleet_manager"].items() if k != "body_html"
    }
    return JSONResponse(payload)


@app.get("/environments", response_class=HTMLResponse)
async def environments_page(request: Request):
    """ORDER 005: read-only render of the fleet-manager environments/ registry
    (setup scripts + env-var schemas, copy-to-clipboard). Degrades honestly
    when GITHUB_TOKEN is unset or the private upstream is unreachable."""
    data = await environments.overview(refresh=_refresh(request))
    return templates.TemplateResponse(
        request, "environments.html", {"e": data, "active": "environments"}
    )


@app.get("/projects", response_class=HTMLResponse)
async def projects_page(request: Request):
    """ORDER 009 increment (1): read-only render of the fleet-manager
    projects/ registry — one card per Project package (instructions /
    coordinator prompt / setup / failsafe / meta.md with deployed-state).
    Degrades honestly: empty state while the registry is still landing
    upstream, not-configured / unavailable on fetch failure — never a 500."""
    data = await projects.overview(refresh=_refresh(request))
    return templates.TemplateResponse(
        request, "projects.html", {"p": data, "active": "projects"}
    )


@app.get("/projects.json")
async def projects_json(request: Request):
    """JSON variant of /projects — the same overview dict, minus rendered
    meta HTML (an HTML-view concern; mirrors /fleet.json's body_html drop)."""
    data = await projects.overview(refresh=_refresh(request))
    payload = dict(data)
    payload["packages"] = [
        {k: v for k, v in pkg.items() if k != "meta_html"}
        for pkg in data["packages"]
    ]
    return JSONResponse(payload)


@app.get("/reviews", response_class=HTMLResponse)
async def reviews_page(request: Request):
    """ORDER 009 increment (3): the fleet's post-merge review queue
    (fleet-manager docs/review-queue.md) — open rows as cards with the
    repo#N token deep-linked, findings/records links extracted from the
    ledger itself, full doc rendered below. Honest degradation; always 200."""
    data = await reviews.overview(refresh=_refresh(request))
    return templates.TemplateResponse(
        request, "reviews.html", {"r": data, "active": "reviews"}
    )


@app.get("/reviews.json")
async def reviews_json(request: Request):
    """JSON variant of /reviews — parsed rows + findings links, minus the
    rendered doc HTML (an HTML-view concern; the /fleet.json precedent)."""
    data = await reviews.overview(refresh=_refresh(request))
    payload = {k: v for k, v in data.items() if k != "body_html"}
    return JSONResponse(payload)


@app.get("/orders", response_class=HTMLResponse)
async def orders_page(request: Request):
    """Fleet orders: every repo's control/inbox.md ORDER blocks
    cross-referenced against its own heartbeat done=/claimed-by lines (the
    protocol keeps inbox orders 'new' forever — execution truth lives in the
    status files). Honest absences/banners/unknowns; always 200."""
    data = await orders.overview(refresh=_refresh(request))
    return templates.TemplateResponse(
        request, "orders.html", {"o": data, "active": "orders"}
    )


@app.get("/orders.json")
async def orders_json(request: Request):
    """JSON variant of /orders — parsed orders + states, minus rendered
    order-body HTML (an HTML-view concern; the /fleet.json precedent)."""
    data = await orders.overview(refresh=_refresh(request))
    payload = dict(data)
    payload["cards"] = [
        {
            **{k: v for k, v in card.items() if k != "orders"},
            "orders": [
                {k: v for k, v in o.items() if k != "body_html"}
                for o in card["orders"]
            ],
        }
        for card in data["cards"]
    ]
    return JSONResponse(payload)


def _state_param(request: Request) -> str | None:
    """The /ideas ``?state=`` lifecycle filter, or None (validated in
    ideas.overview — an unknown value flags itself, never guesses)."""
    value = (request.query_params.get("state") or "").strip().lower()
    return value or None


@app.get("/ideas", response_class=HTMLResponse)
async def ideas_backlog(request: Request):
    repos = await ideas.overview(
        refresh=_refresh(request), state=_state_param(request)
    )
    return templates.TemplateResponse(
        request, "ideas.html", {"repos": repos, "active": "ideas"}
    )


@app.get("/ideas.json")
async def ideas_backlog_json(request: Request):
    return JSONResponse(
        await ideas.overview(refresh=_refresh(request), state=_state_param(request))
    )


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
