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

from fastapi import Depends, FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import agent_pr_tree as agent_pr_tree_registry
from . import arcade as arcade_registry
from . import catalog as catalog_registry
from . import data_source as ds
from . import field_manual as field_manual_registry
from . import graveyard as graveyard_registry
from . import products as products_registry
from . import puddle_museum as puddle_museum_registry
from . import rubric as rubric_registry
from . import stripe_gotchas as stripe_gotchas_registry
from . import webhook_analyzer as webhook_analyzer_registry
from . import discord_auth
from . import listfilter
from . import testing
from . import submissions_store

BASE_DIR = Path(__file__).resolve().parent
NAV = [
    ("features", "Features", "/features"),
    ("commands", "Commands", "/commands"),
    ("games", "Games", "/games"),
    ("arcade", "Arcade", "/arcade"),
    ("products", "Products", "/products"),
    ("field-manual", "Field Manual", "/field-manual"),
    ("testing", "Testing", "/testing"),
    ("changelog", "Changelog", "/changelog"),
    ("status", "Status", "/status"),
    ("puddle-museum", "Puddle Museum", "/puddle-museum"),
    ("graveyard", "Graveyard", "/graveyard"),
    ("agent-pr-check", "PR Check", "/agent-pr-check"),
    ("stripe-gotchas", "Stripe Gotchas", "/stripe-gotchas"),
    ("should-i-build-it", "Rubric Scorer", "/should-i-build-it"),
    ("webhook-analyzer", "Webhook Analyzer", "/webhook-analyzer"),
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
# Discord OAuth owner login (ORDER 037) — the door, not a gated room, so it is
# NOT behind require_owner. It gates botsite's owner surfaces (/testing/owner,
# /submit/queue.json) via the signed session require_owner consults first.
app.include_router(discord_auth.router)


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


@app.get("/favicon.ico", include_in_schema=False)
async def favicon() -> FileResponse:
    """Serve the site icon at the path browsers probe on their own — raw
    JSON views carry no <link rel="icon">, so the viewer requests
    /favicon.ico directly (the PR #321 fleet-wide 404 finding). Same SVG
    the HTML pages declare in base.html."""
    return FileResponse(
        BASE_DIR / "static" / "favicon.svg", media_type="image/svg+xml"
    )


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
    """In-chat mini-games front door (data: the public ``site.json`` feed). It
    also surfaces the Fleet Arcade's launch-readiness at a glance — the same
    live / blocked / distinct-owner-clicks summary the /arcade catalog carries
    (``arcade.availability_summary`` over the committed registry read from disk;
    no network, no duplicated counting) — cross-linking to /arcade. Read-only:
    the summary is static registry data, never a live verdict."""
    res = await ds.fetch_site(refresh=_refresh(request))
    site = res.get("data", {}) or {}
    ctx = _base_ctx(request, "games", res)
    ctx.update(
        {
            "games": ds.games(site),
            "arcade_summary": arcade_registry.availability_summary(
                arcade_registry.load_games()
            ),
        }
    )
    return templates.TemplateResponse(request, "games.html", ctx)


@app.get("/arcade", response_class=HTMLResponse)
async def arcade(request: Request):
    """Fleet Arcade — public catalog of the fleet's playable games (ORDER 014,
    slice 1). Data is the committed ``botsite/data/arcade.json`` read from disk
    at request time — no network. Honest labels: a play/download link renders
    only when a game is really reachable; otherwise the card carries its
    status note. Read-only in this slice: no state-changing routes.
    ORDER 019 PR2: filter/sort/search over the vendored listfilter core
    (maturity / availability dimensions, defined in arcade.py); no params
    renders exactly the pre-filter page. Each unavailable card also surfaces
    its blocking ``owner_action`` / ``ask_id`` (the same honest ledger text the
    /arcade/{slug} detail panel renders — static registry data only, never a
    live askverify verdict), and a top-of-page availability summary strip
    counts live vs blocked games and the distinct owner clicks among the
    blocked ones (``arcade.availability_summary``, a pure fail-soft helper)."""
    res = await ds.fetch_site(refresh=_refresh(request))
    ctx = _base_ctx(request, "arcade", res)
    games = arcade_registry.load_games()
    state = listfilter.parse(arcade_registry.FILTER_SPEC, request.query_params)
    ctx.update(
        {
            "arcade_games": games,
            "arcade_summary": arcade_registry.availability_summary(games),
            "arcade_owner_actions": arcade_registry.pending_owner_actions(games),
            "arcade_filter": listfilter.apply(
                arcade_registry.FILTER_SPEC, games, state
            ),
        }
    )
    return templates.TemplateResponse(request, "arcade.html", ctx)


@app.get("/arcade/{slug}", response_class=HTMLResponse)
async def arcade_detail(request: Request, slug: str):
    """Per-game detail page — the arcade front door gets depth. Driven
    entirely by the committed ``botsite/data/arcade.json`` read from disk at
    request time (same loader as /arcade — the detail page and the catalog can
    never disagree); no network, no live probes. Honest rendering: an
    available game carries the same play/download affordance the catalog
    offers (link only when really reachable, ``ref=fleet-arcade`` attribution);
    an unavailable game renders a structured "What's blocking launch" panel —
    the blocker recorded in the registry (the named owner click), plus its
    "how it unblocks" line. Unknown slug → the site's standard 404. GET-only,
    no forms."""
    res = await ds.fetch_site(refresh=_refresh(request))
    game = arcade_registry.game_by_slug(slug)
    if game is None:
        ctx = _base_ctx(request, "arcade", res)
        ctx.update({"key": slug, "what": "game"})
        return templates.TemplateResponse(request, "not_found.html", ctx, status_code=404)
    ctx = _base_ctx(request, "arcade", res)
    ctx.update({"game": game})
    return templates.TemplateResponse(request, "arcade_detail.html", ctx)


@app.get("/products", response_class=HTMLResponse)
async def products(request: Request):
    """Fleet store — the storefront face for venture-lab's products (ORDER 022
    item 4). Data is the committed ``botsite/data/products.json`` read from
    disk at request time — no network; cross-repo data arrives only as
    committed JSON, curated from venture-lab launch copy. Honest labels: a
    buy link renders only for a product that is really purchasable (live on
    Gumroad with a URL); coming-soon cards carry their status note instead.
    GET-only, no payment handling — buy links go out to Gumroad."""
    res = await ds.fetch_site(refresh=_refresh(request))
    ctx = _base_ctx(request, "products", res)
    ctx.update(
        {
            "products": products_registry.load_products(),
            "catalog_count": len(catalog_registry.load_catalog()),
        }
    )
    return templates.TemplateResponse(request, "products.html", ctx)


@app.get("/products/catalog", response_class=HTMLResponse)
async def products_catalog(request: Request):
    """Vetting catalog — the FULL venture-lab publishing pipeline (ORDER 022
    item 4, venture WEBSITE-IDEA intake). Where /products is the 4-item
    store, this subpage curates all 22 vetting packets + the derived
    OWNER-QUEUE into honest per-title states (live / publish-ready /
    hard-gated / parked). Data is the committed ``botsite/data/catalog.json``
    read from disk at request time — no network; cross-repo data arrives
    only as committed JSON. A buy link renders only for an entry that is
    really purchasable (live on Gumroad with a URL). GET-only, no payment
    handling — sales happen on Gumroad."""
    res = await ds.fetch_site(refresh=_refresh(request))
    ctx = _base_ctx(request, "products", res)
    entries = catalog_registry.load_catalog()
    ctx.update(
        {
            "catalog": entries,
            "catalog_groups": catalog_registry.group_by_status(entries),
        }
    )
    return templates.TemplateResponse(request, "catalog.html", ctx)


@app.get("/field-manual", response_class=HTMLResponse)
async def field_manual(request: Request):
    """Free-chapter funnel page for the Agent Fleet Field Manual (ORDER 022
    item 4, venture WEBSITE-IDEA batch-2 intake; marker: venture-lab
    ``control/outbox.md`` batch 2 @ 0679327). The pitch, chapter list and
    the launch kit's designated free chapter (chapter 1, "The D1 Lesson")
    render from the committed ``botsite/data/field_manual.json`` read from
    disk at request time (``botsite/field_manual.py``, provenance recorded
    in-file) — cross-repo data arrives only as committed JSON, never a live
    fetch on the request path. The CTA is HONEST via the committed
    ``data/catalog.json`` entry: a buy link renders ONLY when that entry
    carries a real ``url`` (today it does not — the publish click is queued
    to the owner); the moment the catalog gains the url, the page shows it
    automatically."""
    res = await ds.fetch_site(refresh=_refresh(request))
    ctx = _base_ctx(request, "field-manual", res)
    manual = field_manual_registry.load_field_manual()
    entry = field_manual_registry.catalog_entry()
    ctx.update(
        {
            "book": manual["book"],
            "excerpt": manual["excerpt"],
            "entry": entry,
            "buy_url": field_manual_registry.buy_url(entry),
        }
    )
    return templates.TemplateResponse(request, "field_manual.html", ctx)


@app.get("/puddle-museum", response_class=HTMLResponse)
async def puddle_museum(request: Request):
    """The Puddle Museum — marketing + concept page for venture-lab's
    rainy-day picture book (ORDER 022 item 4 venture WEBSITE-IDEA intake).
    Data is the committed ``botsite/data/puddle_museum.json`` read from disk
    at request time (``botsite/puddle_museum.py``) — cross-repo data arrives
    only as committed JSON, never a live import. GET-only: no forms, no
    state-changing routes, and no buy links until an edition is really live."""
    res = await ds.fetch_site(refresh=_refresh(request))
    ctx = _base_ctx(request, "puddle-museum", res)
    ctx.update({"museum": puddle_museum_registry.load_museum()})
    return templates.TemplateResponse(request, "puddle_museum.html", ctx)


@app.get("/graveyard", response_class=HTMLResponse)
async def graveyard(request: Request):
    """Strategy Graveyard — the honest leaderboard of the trading-strategy
    lab's experiment ledger (ORDER 022 item 4, venture WEBSITE-IDEA batch-2
    intake). Data is the committed ``botsite/data/graveyard.json`` read from
    disk at request time (``botsite/graveyard.py``), baked by
    ``botsite/gen_graveyard.py`` from trading-strategy's
    ``experiments/index.jsonl`` — cross-repo data arrives only as committed
    JSON, never a live fetch in the request path. GET-only. The headline
    zero (0 promoted) is the page's point: the lab's promotion protocol is
    closed (holdout spent), and the page presents that plainly."""
    res = await ds.fetch_site(refresh=_refresh(request))
    ctx = _base_ctx(request, "graveyard", res)
    ctx.update({"graveyard": graveyard_registry.load_graveyard()})
    return templates.TemplateResponse(request, "graveyard.html", ctx)


@app.get("/agent-pr-check", response_class=HTMLResponse)
async def agent_pr_check(request: Request):
    """Agent-PR diagnostic tree — "Can your agent land its own PR?" (ORDER
    022 item 4, venture WEBSITE-IDEA batch-2 intake). A static, server-
    rendered decision tree that walks a visitor through this fleet's PROVEN
    agent merge-wall lore: the verbatim production errors an AI agent hits
    when it tries to open or merge its own pull request, and the verified
    fix for each — every leaf cited to a file@sha in this repo or a fleet
    findings-doc URL. Data is the committed ``botsite/data/agent_pr_tree.json``
    read from disk at request time (``botsite/agent_pr_tree.py``) — never a
    live fetch in the request path; cross-repo facts arrive only as
    committed JSON. GET-only: no forms, no state-changing routes. The tree
    renders as nested native details/summary (progressive disclosure, zero
    JS required). The end-of-tree CTA references The Agent Merge-Wall
    Cookbook from the committed catalog HONESTLY: publish-ready with no URL
    means coming-soon copy and a link to /products — never an invented buy
    link."""
    res = await ds.fetch_site(refresh=_refresh(request))
    ctx = _base_ctx(request, "agent-pr-check", res)
    cookbook = next(
        (e for e in catalog_registry.load_catalog() if e["slug"] == "merge-wall-cookbook"),
        None,
    )
    ctx.update(
        {
            "tree": agent_pr_tree_registry.load_tree(),
            "cookbook": cookbook,
        }
    )
    return templates.TemplateResponse(request, "agent_pr_check.html", ctx)


@app.get("/stripe-gotchas", response_class=HTMLResponse)
async def stripe_gotchas(request: Request):
    """SWTK webhook-gotchas companion — the free marketing microsite for the
    Stripe Webhook Test Kit, the fleet's one LIVE product (ORDER 022 item 4,
    venture WEBSITE-IDEA batch-2 intake; marker: "SWTK gotchas microsite").
    Six real Stripe checkout-webhook gotchas, each as symptom → fix, curated
    verbatim-faithfully from the kit's own GOTCHAS.md + gotcha article. Data
    is the committed ``botsite/data/stripe_gotchas.json`` read from disk at
    request time (``botsite/stripe_gotchas.py``, provenance recorded in-file:
    venture-lab @ 0679327) — cross-repo data arrives only as committed JSON,
    never a live fetch on the request path. GET-only: no forms, no
    state-changing routes. The buy CTA is HONEST via the committed
    ``data/products.json`` entry: the $29 Gumroad link (with the standard
    ``ref=fleet-store`` attribution) renders ONLY while the registry says the
    kit is live with a real URL — never an invented store link, and the copy
    states the kit's own honest limits alongside its four checks."""
    res = await ds.fetch_site(refresh=_refresh(request))
    ctx = _base_ctx(request, "stripe-gotchas", res)
    ctx.update(
        {
            "page": stripe_gotchas_registry.load_gotchas(),
            "swtk": stripe_gotchas_registry.swtk_product(),
        }
    )
    return templates.TemplateResponse(request, "stripe_gotchas.html", ctx)


@app.get("/should-i-build-it", response_class=HTMLResponse)
async def should_i_build_it(request: Request):
    """"Should I build it?" rubric scorer — an interactive form of
    **venture-eval-001**, the venture lane's REAL distribution-first vetting
    rubric (ORDER 022 item 4, venture WEBSITE-IDEA batch-2 intake; marker:
    "'Should I build it?' rubric scorer"). The five weighted axes, 0–5
    anchors, verdict bands, and anti-gaming rules are the ones venture-lab's
    candidate intakes actually score on. Data is the committed
    ``botsite/data/rubric.json`` read from disk at request time
    (``botsite/rubric.py``, provenance recorded in-file: venture-lab @
    0679327) — cross-repo data arrives only as committed JSON, never a live
    fetch on the request path. GET-only with ZERO server state: the verdict
    is computed entirely in the visitor's browser by vanilla JS
    (``static/rubric_scorer.js``) over a config serialized from the SAME
    loaded rubric — no POST, no storage, nothing submitted anywhere. The
    rubric's own honesty caveat (comparative, not absolute — no magic pass
    mark) renders with the verdict, and the cross-link points at
    /products/catalog, where the packets this rubric really vetted live."""
    res = await ds.fetch_site(refresh=_refresh(request))
    ctx = _base_ctx(request, "should-i-build-it", res)
    rubric = rubric_registry.load_rubric()
    ctx.update(
        {
            "rubric": rubric,
            "scorer_config": rubric_registry.scorer_config(rubric),
        }
    )
    return templates.TemplateResponse(request, "should_i_build_it.html", ctx)


@app.get("/webhook-analyzer", response_class=HTMLResponse)
async def webhook_analyzer(request: Request):
    """Webhook payload analyzer — a CLIENT-SIDE-ONLY tool page (ORDER 022
    item 4 SCAN AND INITIATE; marker: the LAST venture WEBSITE-IDEA batch-2
    marker "webhook-payload analyzer", venture-lab ``control/outbox.md``
    2026-07-13 morning tally @ 0679327). Paste a webhook JSON payload into
    the textarea and vanilla in-browser JS (``static/webhook_analyzer.js``)
    parses and classifies it: provider detection from body shape (Stripe /
    GitHub / Discord, evidence shown, never claimed with certainty), a
    depth-capped field walk with honest type inference, and per-provider
    signature-verification guidance — every guidance line cited to its
    source (SWTK material via ``botsite/data/stripe_gotchas.json`` @
    venture-lab 0679327 for Stripe; official docs fetched 2026-07-13 for
    GitHub; Discord's signature specifics honestly downgraded to a docs
    pointer). GET-only; pasted payloads never reach the server — no form
    POST, no network calls from the analyzer JS, zero server state. The
    knowledge base is the committed ``botsite/data/webhook_analyzer.json``
    read from disk at request time (``botsite/webhook_analyzer.py``); a
    missing/corrupt file degrades to the honest unavailable state."""
    res = await ds.fetch_site(refresh=_refresh(request))
    ctx = _base_ctx(request, "webhook-analyzer", res)
    analyzer = webhook_analyzer_registry.load_analyzer()
    ctx.update(
        {
            "analyzer": analyzer,
            "analyzer_config": (webhook_analyzer_registry.analyzer_config(analyzer)
                                if analyzer else None),
        }
    )
    return templates.TemplateResponse(request, "webhook_analyzer.html", ctx)


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
    ctx.update({"submitted": False, "intake_live": submissions_store.is_live()})
    return templates.TemplateResponse(request, "submit.html", ctx)


@app.post("/submit", response_class=HTMLResponse)
async def submit_post(request: Request, _: None = Depends(testing.guard_state_change)):
    # Durable intake (ORDER 034 / ASK-0004): when DATABASE_URL is configured the
    # public /submit form persists one pending row to the submissions database
    # (Postgres in production, SQLite in tests). Without DATABASE_URL the intake
    # is not live and the form honestly says so -- no fake acceptance. The POST is
    # guarded (same-origin + rate limit) because it now changes state.
    res = await ds.fetch_site()
    form = await request.form()
    kind = str(form.get("kind") or "").strip().lower()[:40]
    if kind not in submissions_store.KINDS:
        kind = submissions_store.KINDS[0]
    title = str(form.get("title") or "").strip()[:120]
    body = str(form.get("body") or "").strip()[:5000]
    live = submissions_store.is_live()
    stored = None
    if live and title and body:
        try:
            stored = submissions_store.create_submission(kind, title, body)
        except Exception:  # pragma: no cover - a DB hiccup must not 500 a public page
            stored = None
    ctx = _base_ctx(request, "submit", res)
    ctx.update(
        {
            "submitted": True,
            "intake_live": live,
            "accepted": stored is not None,
            "missing_fields": live and not (title and body),
        }
    )
    return templates.TemplateResponse(request, "submit.html", ctx)


@app.get("/submit/queue.json")
async def submit_queue(request: Request, _: None = Depends(testing.require_owner)):
    """Owner-authed moderation queue -- the read-back seed for ASK-0004. The
    GitHub-issue mirror on moderation is the follow-up build."""
    return JSONResponse(
        {
            "live": submissions_store.is_live(),
            "submissions": submissions_store.list_submissions(),
        }
    )


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
