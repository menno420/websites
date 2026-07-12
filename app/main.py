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
    listfilter,
    nav,
    orders,
    owner,
    owner_queue,
    projects,
    prompts,
    readiness,
    reviews,
    web_presence,
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
# Nav manifest as Jinja globals: base.html renders the ~5 main categories
# from ONE structure (app/nav.py CATEGORIES) instead of hand-kept markup —
# the category → subcategory decision lives in exactly one place
# (tests/test_nav_manifest.py holds routes to it). NAV_CATEGORY_FOR maps a
# route's active key to its category for the current-category highlight.
templates.env.globals["NAV_CATEGORIES"] = nav.CATEGORIES
templates.env.globals["NAV_CATEGORY_FOR"] = nav.category_for

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


def _attention(rows: list, heartbeat_chips: dict) -> list[dict]:
    """The overview dashboard's what-needs-attention summary — derived from
    data the home page ALREADY fetches (readiness rows + board-repo
    heartbeat freshness), never a new fan-out. Only definite bads surface
    (broken checks, deploy DRIFT, stale heartbeats); unknown-because-
    unfetchable cells stay the board's per-cell honesty below, not alarms."""
    items: list[dict] = []
    for r in rows:
        if r.get("broken_runs"):
            items.append({
                "text": f"{r['repo']}: {len(r['broken_runs'])} broken check(s)",
                "href": "/",
                "state": "bad",
            })
        ds = r.get("deploy_state") or {}
        if ds.get("any_drift"):
            items.append({
                "text": f"{r['repo']}: deploy DRIFT",
                "href": "/",
                "state": "bad",
            })
    for repo, hb in heartbeat_chips.items():
        if hb.get("stale"):
            items.append({
                "text": f"{repo}: heartbeat stale ({hb.get('age_human', '?')})",
                "href": "/fleet",
                "state": "warn",
            })
    return items


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
            "attention": _attention(rows, heartbeat_chips),
            "ttl": config.CACHE_TTL_SECONDS,
            "active": "board",
            "autorefresh_seconds": config.AUTOREFRESH_SECONDS,
        },
    )


@app.get("/api/readiness.json")
async def board_json(request: Request):
    return JSONResponse(await readiness.board(refresh=_refresh(request)))


# ---------------------------------------------------------------------------
# Category landing pages (IA v2, owner-directed 2026-07-12): /work, /history,
# /console. Each renders its category's subcategories as clear rows — name +
# one-line purpose + a live count chip where one is cheap + the primary action
# as a right-aligned button. The hierarchy itself is data in app/nav.py; these
# routes only attach counts. GET-only, no state change, no CSRF surface.
# ---------------------------------------------------------------------------


async def _count_queue(refresh: bool):
    d = await owner_queue.overview(refresh=refresh)
    n = d["summary"]["total"]
    return n, "open", ("warn" if n else "ok")


async def _count_orders(refresh: bool):
    d = await orders.overview(refresh=refresh)
    n = d["summary"]["open"]
    return n, "open", ("warn" if n else "ok")


async def _count_ideas(refresh: bool):
    repos = await ideas.overview(refresh=refresh)
    return ideas.totals(repos)["ideas"], "ideas", "repo"


async def _count_reviews(refresh: bool):
    d = await reviews.overview(refresh=refresh)
    if d["state"] != "ok":
        return None
    n = d["open_count"]
    return n, "open", ("warn" if n else "ok")


async def _count_activity(refresh: bool):
    d = await activity.timeline(refresh=refresh)
    return len(d["items"]), "recent PRs", "repo"


async def _count_projects(refresh: bool):
    d = await projects.overview(refresh=refresh)
    if d["state"] != "ok":
        return None
    seats = [p for p in d["packages"] if not p.get("stub")]
    return len(seats), "seats", "repo"


async def _count_prompts(refresh: bool):
    # Static registry size (app/prompts.py pins the artifact list) — the one
    # genuinely free count: no fetch at all.
    return prompts.TOTAL_ARTIFACTS, "artifacts", "repo"


async def _count_directory(refresh: bool):
    reg = web_presence.load_registry()
    if not reg["ok"]:
        return None
    return len(reg["sites"]), "surfaces", "repo"


# Per-item count providers, keyed by the nav item's active key. Items absent
# here (journal, environments, the gated owner pages, board/fleet) render
# without a chip — a count is only shown where it is CHEAP and honest.
# NOTE environments stays chip-less on purpose: a parallel session is landing
# an environments-hub rework; keeping this row generic keeps the merge clean.
_COUNTERS = {
    "queue": _count_queue,
    "orders": _count_orders,
    "ideas": _count_ideas,
    "reviews": _count_reviews,
    "activity": _count_activity,
    "projects": _count_projects,
    "prompts": _count_prompts,
    "directory": _count_directory,
}


async def _category_rows(cat: dict, refresh: bool) -> list[dict]:
    """The category's items decorated with fail-soft live counts: a counter
    exception or an honest non-ok upstream state yields count=None (the row
    shows —), never a 500 and never an invented number."""

    async def one(item: dict) -> dict:
        row = {**item, "counted": False, "count": None, "unit": "",
               "chip_state": "repo"}
        fn = _COUNTERS.get(item["key"])
        if fn is None:
            return row
        row["counted"] = True
        try:
            got = await fn(refresh)
        except Exception:
            got = None
        if got is not None:
            row["count"], row["unit"], row["chip_state"] = got
        return row

    return list(await asyncio.gather(*[one(it) for it in cat["items"]]))


async def _category_page(request: Request, active: str) -> HTMLResponse:
    cat = nav.category(active)
    rows = await _category_rows(cat, _refresh(request))
    return templates.TemplateResponse(
        request, "category.html", {"cat": cat, "rows": rows, "active": active}
    )


@app.get("/work", response_class=HTMLResponse)
async def work_landing(request: Request):
    """Category landing: the Work rows (queue / orders / ideas / reviews)."""
    return await _category_page(request, active="work")


@app.get("/history", response_class=HTMLResponse)
async def history_landing(request: Request):
    """Category landing: the History rows (activity / journal)."""
    return await _category_page(request, active="history")


@app.get("/console", response_class=HTMLResponse)
async def console_landing(request: Request):
    """Category landing: the Console rows (projects / prompts /
    environments hub / directory)."""
    return await _category_page(request, active="console")


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
    # List-IA (2026-07-12): date sections + state counts for the HTML view
    # only — computed from the already-fetched items, so /activity.json and
    # the Atom feed keep their exact payloads.
    return templates.TemplateResponse(
        request,
        "activity.html",
        {
            "a": data,
            "groups": activity.date_groups(data["items"]),
            "state_counts": activity.state_counts(data["items"]),
            "active": "activity",
        },
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
    refresh = _refresh(request)
    # Seat-package coverage rollup (backlog bullet): the SAME projects-registry
    # data /projects renders, reduced to one "packages incomplete: N" chip —
    # same TTL-cached github layer, zero new network surface.
    data, cov = await asyncio.gather(
        fleet.overview(refresh=refresh),
        projects.coverage_rollup(refresh=refresh),
    )
    return templates.TemplateResponse(
        request,
        "fleet.html",
        {
            "f": data,
            "cov": cov,
            "active": "fleet",
            "autorefresh_seconds": config.AUTOREFRESH_SECONDS,
        },
    )


@app.get("/fleet.json")
async def fleet_heartbeat_json(request: Request):
    refresh = _refresh(request)
    data, cov = await asyncio.gather(
        fleet.overview(refresh=refresh),
        projects.coverage_rollup(refresh=refresh),
    )
    # Drop the rendered markdown body from the JSON payload — callers get the
    # parsed fields + freshness + repo signals and the GitHub deep-link; the
    # rendered HTML is an HTML-view concern only (mirrors /journal/search.json).
    payload = dict(data)
    payload["lanes"] = [
        {k: v for k, v in lane.items() if k != "body_html"} for lane in data["lanes"]
    ]
    # Seat-package coverage rollup — same data the /fleet chip renders, so
    # machine consumers get the registry-lint signal too (contract pinned in
    # tests/test_fleet_json_contract.py).
    payload["coverage"] = cov
    return JSONResponse(payload)


@app.get("/queue", response_class=HTMLResponse)
async def owner_queue_page(request: Request):
    """ORDER 005: the owner's single to-do surface — every lane's ⚑ needs-owner
    plus the fleet-manager owner-queue, deduplicated, newest first. Degrades
    honestly when GITHUB_TOKEN is unset or the private upstream is unreachable.
    ORDER 019: filter/sort/search over the centralized listfilter core
    (project / derived kind / age dimensions, defined in owner_queue.py);
    no params renders exactly the pre-filter page."""
    data = await owner_queue.overview(refresh=_refresh(request))
    state = listfilter.parse(owner_queue.FILTER_SPEC, request.query_params)
    data["filter"] = listfilter.apply(
        owner_queue.FILTER_SPEC, data["items"], state
    )
    # List-IA (2026-07-12): the untouched default view renders in age
    # sections with jump anchors; any active filter/sort/search shows the
    # flat list exactly as before (an explicit ordering beats sections).
    data["groups"] = (
        owner_queue.group_by_age(data["filter"]["items"])
        if not data["filter"]["active"] and state.sort == "newest"
        else None
    )
    return templates.TemplateResponse(
        request, "queue.html", {"q": data, "active": "queue"}
    )


@app.get("/queue.json")
async def owner_queue_json(request: Request):
    """JSON variant of /queue — the manager's machine round-trip: file an ask
    in a lane heartbeat, poll this, confirm it actually surfaces. Same
    overview dict, minus the fleet-manager doc's rendered HTML (an HTML-view
    concern; the /fleet.json precedent). Accepts the same ORDER 019 filter
    params as /queue (project/kind/age/q/sort) — a ``filter`` echo key states
    what was applied; without params ``items`` is byte-identical to before."""
    data = await owner_queue.overview(refresh=_refresh(request))
    state = listfilter.parse(owner_queue.FILTER_SPEC, request.query_params)
    fl = listfilter.apply(owner_queue.FILTER_SPEC, data["items"], state)
    payload = dict(data)
    payload["items"] = fl["items"]
    payload["filter"] = {
        k: fl[k] for k in ("q", "sort", "selected", "active", "shown", "total")
    }
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


@app.get("/projects/{package}", response_class=HTMLResponse)
async def project_detail(request: Request, package: str):
    """Owner Launch Console (single-screen dispatch, 2026-07-12): one seat's
    dispatch screen — every recognized role file's FULL content copy-ready,
    deployed-state / environment / Project-link meta fields, and the static
    dispatch checklist. The package name is validated against the live
    registry listing (unknown or traversal-shaped → 404); registry-fetch
    failures degrade honestly on a 200 page, mirroring /projects."""
    data = await projects.detail(package, refresh=_refresh(request))
    if data["state"] == "not-found":
        return HTMLResponse("unknown package", status_code=404)
    return templates.TemplateResponse(
        request, "project_detail.html", {"d": data, "active": "projects"}
    )


@app.get("/prompts", response_class=HTMLResponse)
async def prompts_page(request: Request):
    """ORDER 014: the fleet prompt library — all 26 registry paste artifacts
    (8 seats x coordinator/instructions/failsafe + the fleet-wide
    universal-startup and session-ender) rendered inline, verbatim, from
    fleet-manager main over the raw-content read-only pattern (TTL-cached).
    Per-artifact honest degradation on fetch failure — never a 500, never
    fabricated content."""
    data = await prompts.overview(refresh=_refresh(request))
    return templates.TemplateResponse(
        request, "prompts.html", {"p": data, "active": "prompts"}
    )


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
    # ORDER 019: the /queue filter widget, reused verbatim (same module, same
    # partial). Orders filter as a FLAT list (each stamped with its card's
    # repo), then regroup per card; the per-card attention sort stays. With
    # no params every card shows its full inbox order — identical to before.
    state = listfilter.parse(orders.FILTER_SPEC, request.query_params)
    flat = [
        {**o, "repo": c["repo"]} for c in data["cards"] for o in c["orders"]
    ]
    fl = listfilter.apply(orders.FILTER_SPEC, flat, state)
    shown_by_repo: dict[str, list] = {}
    for o in fl["items"]:
        shown_by_repo.setdefault(o["repo"], []).append(o)
    for c in data["cards"]:
        c["shown_orders"] = shown_by_repo.get(c["repo"], [])
    data["filter"] = fl
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
    # List-IA (2026-07-12): fleet-wide rollup for the summary header — pure
    # aggregation over the same per-repo dicts; /ideas.json is untouched.
    return templates.TemplateResponse(
        request,
        "ideas.html",
        {"repos": repos, "t": ideas.totals(repos), "active": "ideas"},
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


@app.get("/directory", response_class=HTMLResponse)
async def web_directory(request: Request):
    """ORDER 021: the web-presence directory — every web surface we own on one
    read-only page. Rows come from the committed registry
    app/data/web_presence.json (single source of truth; add rows by PR), read
    at request time. Per-row liveness is probed through the same TTL-cached
    raw fetch as the board's deploy-drift cell — a failed probe or a missing
    URL renders its honest state, never a fabricated green badge. Public like
    every other route in this module: the registry holds public-repo data
    only (the repo itself is public), no secrets."""
    data = await web_presence.overview(refresh=_refresh(request))
    return templates.TemplateResponse(
        request,
        "web_presence.html",
        {"d": data, "ttl": config.CACHE_TTL_SECONDS, "active": "directory"},
    )


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
    # Render allow-set is wider than REPOS: any fleet lane repo may render.
    if repo not in config.JOURNAL_RENDER_REPOS:
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
