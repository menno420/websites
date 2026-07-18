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

Auth seam: `require_owner` is the single gate dependency — the planned Discord
OAuth (ORDER 021) replaces it in one place, starting at /environments-hub.
"""

from __future__ import annotations

import asyncio
import base64
import secrets
import time
from collections import defaultdict, deque
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from . import (
    askverify,
    briefing,
    card_gating,
    codedrift,
    config,
    discord_auth,
    envdrift,
    envhub,
    fleet,
    github,
    listfilter,
    nav,
    owner_assist,
    owner_queue,
    prompts,
    railway,
    readiness,
    release_drift,
    writeback,
)

router = APIRouter(prefix="/owner")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
# The environments page deep-links each live variable name to its console
# (prefix-matched in app/railway.py) — exposed as a filter so the template
# needs no hand-kept link table.
templates.env.filters["manage_link"] = railway.manage_link
# Nav manifest globals, mirroring app/main.py: this module renders base.html
# through its OWN Jinja env, so without these the /owner pages served an
# EMPTY header nav (Jinja iterates an undefined global as nothing). Same
# single source (app/nav.py) — the two envs cannot drift.
templates.env.globals["NAV_CATEGORIES"] = nav.CATEGORIES
templates.env.globals["NAV_CATEGORY_FOR"] = nav.category_for

_UNAUTH_HEADERS = {"WWW-Authenticate": 'Basic realm="owner area"'}

# ---------------------------------------------------------------------------
# CSRF + rate-limit hardening for the state-changing POST actions (ORDER 013).
#
# CSRF: strict same-origin check on Origin/Referer. If an Origin header is
# present its host must match the request's own Host header; if Origin is
# absent we fall back to Referer with the same rule. If BOTH are absent the
# request is REJECTED with 403 (strictest choice, deliberate): every modern
# browser sends Origin on a POST, so a browser-driven owner console always
# passes, while a header-less forged/cross-context POST never does.
# Non-browser callers (curl, scripts) must supply a matching Origin header.
# Hosts are compared (netloc, case-insensitive) rather than full scheme+host
# because the service runs behind Railway's TLS-terminating proxy, where the
# app-side scheme may not match the browser-side one; the host comparison is
# what defeats a cross-site request, since an attacker's page cannot forge
# the browser-set Origin/Referer host.
#
# Rate limit: a dependency-free in-process sliding window, per route path +
# client host — 10 requests per 60s, 429 beyond that. State is module-level
# and in-memory (one process per service), resettable for tests.
# ---------------------------------------------------------------------------

RATE_LIMIT_MAX_REQUESTS = 10
RATE_LIMIT_WINDOW_SECONDS = 60.0

# Failed-login throttle for the GET auth gate (require_owner). The password
# check alone left `/owner` GETs open to unlimited brute-force guessing — an
# attacker only ever saw 401, never a slowdown. This caps FAILED Basic-auth
# attempts per client host, reusing the same sliding-window mechanism and
# window as the POST-action limiter above; a SUCCESSFUL auth is never counted.
# Same shape as the POST limiter (10 / 60s), tracked separately so the two
# budgets never cross-consume.
AUTH_FAIL_MAX_ATTEMPTS = 10

_rate_buckets: dict[str, deque] = defaultdict(deque)


def reset_rate_limits() -> None:
    """Clear all rate-limit state (test isolation hook)."""
    _rate_buckets.clear()


def _header_host(value: str) -> str:
    """Lowercased netloc of an Origin/Referer header value ('' if unparsable)."""
    try:
        return urlsplit(value).netloc.lower()
    except ValueError:
        return ""


def _require_same_origin(request: Request) -> None:
    """Reject state-changing requests whose Origin/Referer is not this host."""
    own_host = request.headers.get("host", "").strip().lower()
    origin = request.headers.get("origin")
    if origin is not None:
        if not own_host or _header_host(origin) != own_host:
            raise HTTPException(
                status_code=403,
                detail="cross-origin request rejected (Origin mismatch)",
            )
        return
    referer = request.headers.get("referer")
    if referer is not None:
        if not own_host or _header_host(referer) != own_host:
            raise HTTPException(
                status_code=403,
                detail="cross-origin request rejected (Referer mismatch)",
            )
        return
    # Documented strict choice: no Origin AND no Referer → reject. Browsers
    # always send Origin on POST, so this only ever blocks non-browser
    # callers that omitted the header.
    raise HTTPException(
        status_code=403,
        detail=(
            "request rejected: missing Origin/Referer header "
            "(same-origin required for owner actions)"
        ),
    )


def _sliding_window_hit(key: str, max_hits: int, detail: str) -> None:
    """Record one hit against a per-key sliding window; 429 when it overflows.

    The shared core of both limiters — the per-(route, client) POST-action
    limiter and the per-client failed-auth limiter on the GET gate. Same
    window (RATE_LIMIT_WINDOW_SECONDS), same in-memory bucket store
    (_rate_buckets, resettable via reset_rate_limits), same Retry-After 429
    shape; only the key namespace and the ceiling differ. The (max_hits+1)-th
    hit inside the window raises 429 instead of being recorded."""
    now = time.monotonic()
    bucket = _rate_buckets[key]
    while bucket and now - bucket[0] > RATE_LIMIT_WINDOW_SECONDS:
        bucket.popleft()
    if len(bucket) >= max_hits:
        retry_after = max(1, int(RATE_LIMIT_WINDOW_SECONDS - (now - bucket[0])) + 1)
        raise HTTPException(
            status_code=429,
            detail=detail,
            headers={"Retry-After": str(retry_after)},
        )
    bucket.append(now)


def _enforce_rate_limit(request: Request) -> None:
    """Sliding-window limiter per (route path, client host); 429 when tripped."""
    client_host = request.client.host if request.client else "unknown"
    key = f"{request.url.path}|{client_host}"
    _sliding_window_hit(
        key,
        RATE_LIMIT_MAX_REQUESTS,
        "rate limit exceeded for owner actions — retry shortly",
    )


def require_owner(request: Request) -> None:
    """Dependency gating every /owner route. Accepts EITHER a valid Discord
    owner session (the ASK-0001 login flow, app/discord_auth.py) OR the
    existing HTTP-Basic SITE_PASSWORD. Fail-closed: 503 when NEITHER auth is
    configured (naming the opening owner action), 401 on bad/missing creds."""
    # Discord owner session takes precedence — a valid signed session cookie
    # from the OAuth login flow authorizes the whole gated area without Basic.
    if discord_auth.owner_session_id(request):
        return
    oauth_up = discord_auth.oauth_configured()
    if not config.SITE_PASSWORD and not oauth_up:
        # Fail closed: with NOTHING configured an unset password never means an
        # open door. Name the owner action that opens the gate. The public site
        # is unaffected — only this gated area 503s.
        raise HTTPException(
            status_code=503,
            detail=(
                "owner area unavailable: no owner authentication is configured "
                "— set SITE_PASSWORD, or complete the Discord OAuth owner login "
                "at /owner/login (needs DISCORD_CLIENT_ID, DISCORD_CLIENT_SECRET, "
                "OWNER_DISCORD_ID, OWNER_SESSION_SECRET; ASK-0002 adds the "
                "redirect URI on the SuperBot Discord app)"
            ),
        )
    header = request.headers.get("authorization", "")
    supplied = ""
    if header.lower().startswith("basic "):
        try:
            decoded = base64.b64decode(header.split(" ", 1)[1]).decode("utf-8")
            _user, _, supplied = decoded.partition(":")
        except Exception:
            supplied = ""
    if supplied and secrets.compare_digest(supplied, config.SITE_PASSWORD):
        # Correct password — return immediately. A successful auth is NEVER
        # throttled and never touches the failed-attempt budget.
        return
    # Failed attempt (bad or missing password): brute-force throttle. The
    # (AUTH_FAIL_MAX_ATTEMPTS+1)-th failure from this client host inside the
    # window raises 429 (with Retry-After) BEFORE re-prompting, closing the
    # previously unbounded 401 loop. Keyed per client host across ALL /owner
    # GET paths (one shared budget), so path-hopping cannot mint fresh tries.
    client_host = request.client.host if request.client else "unknown"
    _sliding_window_hit(
        f"auth-fail|{client_host}",
        AUTH_FAIL_MAX_ATTEMPTS,
        "too many failed owner logins — retry shortly",
    )
    raise HTTPException(
        status_code=401,
        detail="owner authentication required",
        headers=_UNAUTH_HEADERS,
    )


def require_owner_action(request: Request) -> None:
    """Dependency gating every STATE-CHANGING /owner route.

    Auth first (401/503 exactly as `require_owner`), then the strict
    same-origin CSRF check (403), then the in-process rate limit (429).
    """
    require_owner(request)
    _require_same_origin(request)
    _enforce_rate_limit(request)


def _refresh(request: Request) -> bool:
    return request.query_params.get("refresh") in ("1", "true", "yes")


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def owner_board(request: Request, _: None = Depends(require_owner)):
    # reveal_secrets=True: the authed path un-masks the secret NAMES the public
    # board only counts. This flag never reaches the public board() call.
    # Environments rollup (the #219 session's captured idea, promoted):
    # envhub.group_summary across all groups reduced to one board chip —
    # same TTL-cached railway.live_overview read the environments-hub makes,
    # zero new network surface.
    # Fleet prompt-state rows (ORDER 041 remainder): per-seat deployed vs
    # canonical + stale count, reduced from the SAME drift rows /prompts
    # renders (prompts.console_rollup — identical TTL-cached fetches, no
    # second source, no stored copies).
    # Ask preflight rollup (launch preflight verdicts, 2026-07-15): the
    # SAME briefing.asks composition — ledger fetch + askverify's
    # read-only probes, all TTL-cached — reduced to one "N of M asks
    # machine-verified" chip. Honest-unknown passes through untouched.
    rows, envcov, promptstate, askcov = await asyncio.gather(
        readiness.board(refresh=_refresh(request), reveal_secrets=True),
        envhub.board_rollup(refresh=_refresh(request)),
        prompts.console_rollup(refresh=_refresh(request)),
        briefing.asks(refresh=_refresh(request)),
    )
    return templates.TemplateResponse(
        request,
        "owner.html",
        {
            "rows": rows,
            "envcov": envcov,
            "promptstate": promptstate,
            "askcov": askcov,
            "ttl": config.CACHE_TTL_SECONDS,
            "cache_entries": github.cache_size(),
            "banner": None,
            "repos": list(config.REPOS),
        },
    )


@router.get("/api/readiness.json")
async def owner_board_json(request: Request, _: None = Depends(require_owner)):
    # Authed JSON: unlike the public /api/readiness.json, this DOES carry the
    # secret names (under each row's secrets.names). Since the environments
    # rollup landed (backlog promotion of the #223 board chip), the payload is
    # an object — the board rows under "rows" plus the SAME envhub.board_rollup
    # dict the /owner HTML chip renders under "environments", so machine
    # consumers get the "N groups incomplete" signal without scraping HTML.
    # Same TTL-cached railway.live_overview read, zero new network surface;
    # the rollup's honest-unknown ladder passes through untouched. Shape
    # pinned in tests/test_owner_readiness_json_contract.py (the #217
    # /fleet.json precedent).
    rows, envcov = await asyncio.gather(
        readiness.board(refresh=_refresh(request), reveal_secrets=True),
        envhub.board_rollup(refresh=_refresh(request)),
    )
    return JSONResponse({"rows": rows, "environments": envcov})


@router.get("/briefing", response_class=HTMLResponse)
async def owner_briefing(request: Request, _: None = Depends(require_owner)):
    """ORDER 025 — THE MORNING BRIEFING: the owner's catch-up on one gated
    GET-only page. Five sections (SHIPPED / ORDERS / ASKS / FLEET /
    WATCHES) over a bounded window (default last 16h; ``?hours=`` clamped
    to 1–168, invalid values fall back to the default with the fallback
    noted on the page). All composition lives in the domain layer
    (``app/briefing.py``) over the existing TTL-cached github client —
    zero new network surface, zero state changes; a failed source renders
    "unknown — <reason>", never fabricated data, and the route always
    answers 200."""
    data = await briefing.overview(
        hours_raw=request.query_params.get("hours"),
        refresh=_refresh(request),
    )
    return templates.TemplateResponse(
        request, "owner_briefing.html", {"b": data}
    )


@router.get("/environments", response_class=HTMLResponse)
async def owner_environments(request: Request, _: None = Depends(require_owner)):
    """Live-env-visibility page (ORDER 015, plan slice 1 —
    docs/planning/live-env-visibility-plan-2026-07-11.md). Read-only GET
    behind the same gate as the rest of /owner: committed per-service env
    facts always; live Railway variable NAMES (never values) when the
    project-scoped RAILWAY_TOKEN is configured; an honest owner-errand
    banner while it is not.

    Name-drift check (the captured backlog bullet, promoted): the documented
    names and the live names are additionally DIFFED (app/envdrift.py, the
    PR #216 annotate idiom) — documented-but-missing-live /
    live-but-undocumented chips per service + a page-level rollup, with the
    honest unknown-with-reason state whenever Railway is unreachable; never
    a fabricated match. Names only — values never exist past the client
    boundary in app/railway.py.

    Code-vs-declared drift (B6, Q1=a): additionally the NAMES each service's
    runtime code reads (statically scanned into the committed
    app/data/env_coderefs.json) are diffed against the declared manifest
    (app/codedrift.py) — referenced-but-undeclared / declared-but-unreferenced
    chips per service + a page rollup, honest unknown if the snapshot is
    missing. Static + names only: no source scan and no network at request
    time."""
    data = await railway.overview(refresh=_refresh(request))
    envdrift.annotate(data)
    codedrift.annotate(data)
    return templates.TemplateResponse(
        request,
        "owner_environments.html",
        {"env": data, "ttl": config.CACHE_TTL_SECONDS},
    )


@router.get("/environments-hub", response_class=HTMLResponse)
async def owner_environments_hub(request: Request, _: None = Depends(require_owner)):
    """ORDER 021 slice 1 — the fleet-wide environments hub: every environment
    surface (Railway projects/services, GitHub Actions secret stores,
    claude.ai cloud envs) grouped per project-group, each row = name · the
    variable NAMES it holds (never values) · a deep link to where it is
    managed. Committed registry (app/data/environments.json) + a live
    variable-NAME merge for the superbot-websites group via the existing
    project-scoped RAILWAY_TOKEN read. Read-only GET — no state changes.

    DISCORD-OAUTH SEAM (do not build yet — ORDER 021 stages it later):
    auth is exactly this route's `require_owner` dependency (HTTP Basic on
    SITE_PASSWORD, like all of /owner). When the Discord OAuth app the
    dashboard/mineverse instances already use is provisioned, swap the
    dependency here for the OAuth-session equivalent — the page itself
    needs no other change (it is read-only and auth-agnostic; see
    app/envhub.py's docstring).
    """
    data = await envhub.overview(refresh=_refresh(request))
    state = listfilter.parse(envhub.FILTER_SPEC, request.query_params)
    fl = listfilter.apply(envhub.FILTER_SPEC, data["rows"], state)
    sections = envhub.group_sections(data["groups"], fl["items"])
    return templates.TemplateResponse(
        request,
        "owner_environments_hub.html",
        {"hub": data, "lf": fl, "sections": sections},
    )


@router.get("/environments-hub/manifest/{group_id}", response_class=HTMLResponse)
async def owner_envhub_manifest(
    group_id: str, request: Request, _: None = Depends(require_owner)
):
    """ORDER 021 slice 2 — the env-creation plan/manifest generator: for one
    project group, the complete-environment manifest generated from the
    committed registry (app/data/environments.json): service definitions,
    the env-var SCHEMA (variable NAMES + placeholders, never values), and
    copyable setup commands the OWNER executes by hand.

    Completeness diff (the slice-2 card's captured idea, promoted): every
    schema row is additionally badged set-live / missing-live against the
    slice-1 live variable-NAME read (railway.live_overview — project-scoped
    RAILWAY_TOKEN, values dropped at the client boundary, never rendered),
    with the honest unknown state whenever the live truth is not knowable —
    the manifest doubles as the owner's "what's left to finish this
    environment" checklist.

    Read-only GET behind the exact same gate as the hub (same Discord-OAuth
    seam: swap the dependency, nothing else). It performs NO provisioning —
    per docs/RAILWAY-SAFETY.md agents make no Railway mutations and
    RAILWAY_API_KEY never lives on an app service; the ONLY network call is
    the existing read-only names query in app/railway.py (queries only — no
    mutation strings exist in that module).
    """
    data = envhub.manifest(group_id)
    if data is None:
        raise HTTPException(
            status_code=404, detail=f"unknown project group {group_id!r}"
        )
    envhub.annotate_completeness(
        data, await railway.live_overview(refresh=_refresh(request))
    )
    return templates.TemplateResponse(
        request, "owner_envhub_manifest.html", {"m": data}
    )


async def _render_with_banner(request: Request, banner: dict) -> HTMLResponse:
    rows, envcov, promptstate, askcov = await asyncio.gather(
        readiness.board(reveal_secrets=True),
        envhub.board_rollup(),
        prompts.console_rollup(),
        briefing.asks(),
    )
    return templates.TemplateResponse(
        request,
        "owner.html",
        {
            "rows": rows,
            "envcov": envcov,
            "promptstate": promptstate,
            "askcov": askcov,
            "ttl": config.CACHE_TTL_SECONDS,
            "cache_entries": github.cache_size(),
            "banner": banner,
            "repos": list(config.REPOS),
        },
    )


# ---------------------------------------------------------------------------
# ORDER 020 — owner writeback console (/owner/queue).
#
# The PUBLIC /queue stays read-only for anonymous visitors; this gated twin
# adds the write half: per owner-action MARK COMPLETE / REQUEST ASSISTANCE /
# ADD NOTE-CORRECTION-IDEA forms (server-rendered, no JS), the AI drafting
# assist (draft only — the owner approves before anything is stored), and
# the local audit log with retry. Every state change goes through
# require_owner_action (auth → same-origin → rate limit), exactly like the
# ORDER 013 actions above.
# ---------------------------------------------------------------------------


async def _render_owner_queue(
    request: Request,
    banner: dict | None = None,
    draft: dict | None = None,
) -> HTMLResponse:
    data = await owner_queue.overview(refresh=_refresh(request))
    # Durable ask id (C15): overview() already attaches ``uid`` to every ask;
    # this setdefault is the belt-and-braces guarantee that the per-ask
    # writeback forms on this LIVE surface always carry a resolvable
    # identifier (never a blank hidden field), independent of how the items
    # were built.
    for it in data["items"]:
        it.setdefault("uid", owner_queue.ask_uid(it))
    # Launch preflight verdicts (2026-07-15): annotate the GATED view only —
    # the public /queue renders the exact same overview() untouched (pinned
    # byte-identical by test). Read-only probes, TTL-cached, honest-unknown.
    data["verify"] = await askverify.annotate(
        data["items"], refresh=_refresh(request)
    )
    # Release-drift chip (2026-07-16): reuse #365's registry-blocker ↔ probe
    # verdict (app/release_drift.py) to flag, per open ask, the done-detected
    # -but-still-gated drift the healthcheck pass surfaces only in CI. Chip is
    # None when the ask is not drifting, so the template omits it. Read-only:
    # the SAME probe verdicts annotate already attached, no new fetch.
    for item in data["items"]:
        item["drift"] = release_drift.chip(item.get("verify"))
    # Reverse-join enrichment (read-only, disk-only): for each open ask,
    # count and list the public product cards its ask_id gates across the
    # four botsite registries — rendered as the "unblocks N cards" chip
    # beside the verify chip. Gated view only; the public /queue never runs
    # this (its overview() stays byte-identical). No network, no state.
    card_gating.annotate_unblocks(data["items"])
    # C14 self-cleaning owner queue (2026-07-17): partition the annotated asks
    # so an ask whose underlying condition askverify POSITIVELY re-verified as
    # resolved (the done-detected rung only) drops out of the active nag list
    # into a separate "self-cleaned this pass" section. Fail-soft lives in
    # askverify.split_self_cleaned: still-open / unknown / probe-error / any
    # ambiguous or unreachable state keeps the ask active. Gated view only —
    # the public /queue overview() is untouched (byte-identical, contract-pinned).
    data["active_items"], data["auto_cleared_items"] = (
        askverify.split_self_cleaned(data["items"])
    )
    return templates.TemplateResponse(
        request,
        "owner_queue.html",
        {
            "q": data,
            "entries": writeback.list_entries(),
            "wb": writeback.state_summary(),
            "assist": owner_assist.state_summary(),
            "banner": banner,
            "draft": draft,
        },
    )


@router.get("/queue", response_class=HTMLResponse)
async def owner_queue_console(
    request: Request, _: None = Depends(require_owner)
):
    return await _render_owner_queue(request)


def _entry_banner(entry: dict) -> dict:
    """One honest line per submission outcome — a SHA link only for a
    commit that verifiably landed; the exact error class otherwise."""
    if entry["status"] == "committed":
        pr_bit = (
            f" — PR #{entry['pr_number']} opened (auto-merging on green)"
            if entry.get("pr_number")
            else ""
        )
        return {
            "ok": True,
            "text": (
                f"{entry['action']} committed to {entry['path']} on "
                f"{entry.get('branch') or '?'} (commit "
                f"{entry['commit_sha'][:8]}){pr_bit}"
            ),
            "url": entry.get("pr_url") or entry["commit_url"],
        }
    return {
        "ok": False,
        "text": (
            f"{entry['action']} stored locally as entry #{entry['id']} "
            f"({entry['status']}) — {entry['error']}"
        ),
    }


async def _handle_writeback(request: Request, action: str, target: str, text: str):
    try:
        entry = await writeback.submit(action, target, text)
    except ValueError as exc:
        return await _render_owner_queue(
            request, banner={"ok": False, "text": f"rejected: {exc}"}
        )
    return await _render_owner_queue(request, banner=_entry_banner(entry))


# ---------------------------------------------------------------------------
# Queue writeback PREFLIGHT (2026-07-15, PR B of the launch-console pair).
#
# The three writeback actions used to fire a repo write from a one-step
# form. Now the /owner/queue forms POST to a STATELESS preview first
# (payloads run up to writeback.TEXT_MAX_CHARS=4000 chars, so this is a
# POST, not a GET with the text in the URL): the exact composed block
# (writeback's own render_* functions — one renderer, two surfaces), the
# target file + branch, the write-token state, for assist the PROVISIONAL
# ORDER number (never pinned — commit-time numbering is the module's own
# race-safe convention), and for complete the ask's askverify verdict chip.
# The preview stores NOTHING (no SQLite row, no commit); its confirm
# re-POSTs the same action/target/text verbatim to the UNCHANGED firing
# routes. One minimal confirm-side change: complete re-finds the targeted
# ask by headline and fails closed when every source read fine and the ask
# is gone (unreadable sources stay honest-unknown and never fake a "gone").
#
# Deliberate preview exemptions (documented on the queue page too): retry
# re-fires an entry ALREADY stored and shown in the audit log (pinned by
# entry_id), and draft stores nothing at all (it only pre-fills a form).
# ---------------------------------------------------------------------------

_QUEUE_ACTION_LABELS = {
    "complete": "mark complete",
    "assist": "file assistance ORDER",
    "note": "add note",
}


def _sources_fully_readable(data: dict) -> bool:
    """True only when EVERY ask source read successfully this pass — the
    precondition for concluding a targeted ask is GONE. An unreadable
    source keeps absence honest-unknown (never a fabricated 'gone')."""
    return (
        not data.get("unreadable_lanes")
        and data.get("fleet_manager", {}).get("state") == "ok"
    )


async def _find_ask(
    target: str, uid: str = "", refresh: bool = False
) -> tuple[dict, dict | None]:
    """The queue overview + the targeted ask (or None).

    C15: resolution is by DURABLE content id when the form carried one — an
    ask's ``ask_uid`` is stable across a reorder of the ledger, so the id
    always points at the intended ask (and an unknown/stale id resolves to
    None, never to some other ask). Only when no uid is supplied (legacy
    forms, the general writeback) does this fall back to the old exact-headline
    match."""
    data = await owner_queue.overview(refresh=refresh)
    if uid:
        item = owner_queue.resolve_uid(data["items"], uid)
    else:
        item = next(
            (it for it in data["items"] if owner_queue.headline(it) == target),
            None,
        )
    return data, item


def _token_state_fact() -> dict:
    wb = writeback.state_summary()
    if wb["token_set"]:
        value = (
            f"{wb['token_env']} present — the confirm commits to a "
            f"{wb['branch_prefix']}<n> branch and opens an auto-merging PR "
            f"into {wb['base']} (claimed only with the verified SHA + open PR)"
        )
    else:
        value = (
            f"{wb['token_env']} not set — the confirm stores the entry "
            "locally (queued, retryable); nothing lands in git until the "
            "token is pasted"
        )
    return {"label": "write token", "value": value}


async def _render_queue_preview(
    request: Request,
    action: str,
    target: str,
    text: str,
    uid: str = "",
    banner: dict | None = None,
) -> HTMLResponse:
    """The stateless writeback preflight page — pure composition + reads.

    Stores NOTHING: no SQLite row, no commit, no github.api_post /
    api_request. The only network here is read-only (the inbox raw read
    for assist's provisional ORDER number; askverify's read-only probe for
    complete) — all TTL-cache-honest like every other preview."""
    wb = writeback.state_summary()
    entry = {"id": "pending", "action": action, "target": target, "text": text}
    p: dict = {
        "title": f"{_QUEUE_ACTION_LABELS[action]} — preflight",
        "lede": (
            "Preview of exactly what this writeback would land — nothing is "
            "stored or committed until you confirm below. The console audit "
            "entry # and the timestamp in the block are assigned when you "
            "confirm."
        ),
        "banner": banner,
        "chip": None,
        "facts": None,
        "block": None,
        "block_label": "the exact block that will land",
        "block_note": None,
        "empty": None,
        "confirm": None,
        "cancel": {
            "href": "/owner/queue",
            "label": "← cancel — back to the owner queue",
        },
    }
    problem = writeback.validate(action, target, text)
    if problem:
        p["empty"] = (
            f"this submission would be rejected: {problem} — nothing to "
            "confirm"
        )
        return templates.TemplateResponse(request, "owner_preflight.html", {"p": p})

    facts = [
        {"label": "action", "value": _QUEUE_ACTION_LABELS[action]},
        {
            "label": "target",
            "value": target or "— (general, not tied to a queue item)",
        },
        {
            "label": "lands in",
            "value": (
                f"{wb['repo']} · {writeback.target_path(action)} → "
                f"auto-PR into {wb['base']} "
                f"(branch {wb['branch_prefix']}<n>)"
            ),
            "code": True,
        },
        _token_state_fact(),
    ]

    if action == "assist":
        # Read-only raw read of the CURRENT inbox, only to show a
        # provisional number — the commit path re-reads and re-numbers at
        # commit time (the module's own race-safe convention), so the
        # number is deliberately NOT pinned into the confirm.
        inbox = await github.fetch_file(
            writeback.WRITEBACK_REPO,
            writeback.INBOX_PATH,
            ref=wb["branch"],
            refresh=True,
        )
        if inbox["ok"] and isinstance(inbox["data"], str):
            inbox_text = inbox["data"]
            nnn = writeback.next_order_number(inbox_text)
            facts.append(
                {
                    "label": "provisional ORDER number",
                    "value": (
                        f"ORDER {nnn:03d} — provisional: the number is "
                        "re-read from the file's then-current maximum at "
                        "commit time, so a concurrent ORDER renumbers this"
                    ),
                }
            )
        else:
            inbox_text = ""
            reason = inbox.get("error") or f"HTTP {inbox.get('status')}"
            facts.append(
                {
                    "label": "provisional ORDER number",
                    "value": (
                        f"unknown — {writeback.INBOX_PATH} could not be read "
                        f"({reason}); the real number is read at commit time. "
                        "The ORDER number in the block below is a placeholder"
                    ),
                }
            )
        p["block"] = writeback.render_assist_block(entry, inbox_text)
    else:
        p["block"] = writeback.render_note_block(entry)

    if action == "complete":
        data, item = await _find_ask(target, uid)
        if item is not None:
            # The ask's live verdict — the SAME askverify probe the gated
            # queue page runs (read-only, TTL-cached, honest-unknown).
            await askverify.annotate([item])
            p["chip"] = item["verify"]
        elif _sources_fully_readable(data):
            p["empty"] = (
                f"nothing to confirm — the ask {target!r} is not in the "
                "readable sources right now (every source read "
                "successfully); it may already be resolved upstream"
            )
            p["facts"] = facts
            return templates.TemplateResponse(
                request, "owner_preflight.html", {"p": p}
            )
        else:
            p["chip"] = {
                "css": "unknown",
                "label": "ask not found — sources partially unreadable",
                "probe": "queue overview re-read (read-only)",
                "detail": (
                    "the ask was not found, but not every source could be "
                    "read — absence is not proven; the confirm proceeds and "
                    "stays honest the same way"
                ),
                "url": "",
            }

    p["facts"] = facts
    p["confirm"] = {
        "action": f"/owner/queue/actions/{action}",
        # uid is the durable ask id (C15) — the confirm re-POSTs it so the
        # firing route resolves the SAME ask the preview targeted, immune to a
        # ledger reorder between preview and confirm. '' for the general
        # writeback (no ask); the firing routes read it absent-safe.
        "fields": {
            "action": action, "target": target, "text": text, "uid": uid,
        },
        "label": f"confirm — {_QUEUE_ACTION_LABELS[action]}",
        "note": (
            "re-POSTs exactly this action/target/text to the unchanged "
            "firing route (auth → same-origin → rate limit, same floor)"
        ),
    }
    return templates.TemplateResponse(request, "owner_preflight.html", {"p": p})


@router.post("/queue/actions/preview", response_class=HTMLResponse)
async def action_queue_preview(
    request: Request,
    action: str = Form(...),
    target: str = Form(""),
    text: str = Form(""),
    uid: str = Form(""),
    _: None = Depends(require_owner_action),
):
    """Stateless POST-to-preview for the three writeback actions. Stores
    NOTHING — the audit row and the commit both happen only on the
    confirm's re-POST to the unchanged firing route."""
    target = target.strip()
    text = text.strip()
    uid = uid.strip()
    if action not in writeback.ACTIONS:
        return await _render_owner_queue(
            request, banner={"ok": False, "text": f"unknown action {action!r}"}
        )
    return await _render_queue_preview(request, action, target, text, uid)


@router.post("/queue/actions/complete", response_class=HTMLResponse)
async def action_queue_complete(
    request: Request,
    target: str = Form(...),
    text: str = Form(""),
    uid: str = Form(""),
    _: None = Depends(require_owner_action),
):
    # The one confirm-side preflight change (PR B): re-find the targeted
    # ask; POSITIVELY observed gone (every source readable, ask absent) →
    # fail closed with nothing stored, nothing committed. Unreadable sources
    # never fake a "gone" — the owner's assertion proceeds exactly as before
    # (the 17 ORDER-020 tests pin that path). C15: the re-find resolves by the
    # DURABLE ask id when the confirm carried one, so a ledger reorder between
    # preview and confirm can never point the fail-closed check at the wrong
    # ask; an unknown/stale id resolves to None (rejected safely, same as a
    # vanished ask).
    stripped = target.strip()
    uid = uid.strip()
    if not writeback.validate("complete", stripped, text.strip()):
        data, item = await _find_ask(stripped, uid)
        if item is None and _sources_fully_readable(data):
            banner = {
                "ok": False,
                "text": (
                    f"nothing stored, nothing committed — the ask "
                    f"{stripped!r} is no longer in the readable sources "
                    "(every source read successfully); it may already be "
                    "resolved upstream"
                ),
            }
            return await _render_queue_preview(
                request, "complete", stripped, text.strip(), uid,
                banner=banner,
            )
    return await _handle_writeback(request, "complete", target, text)


@router.post("/queue/actions/assist", response_class=HTMLResponse)
async def action_queue_assist(
    request: Request,
    target: str = Form(""),
    text: str = Form(""),
    _: None = Depends(require_owner_action),
):
    return await _handle_writeback(request, "assist", target, text)


@router.post("/queue/actions/note", response_class=HTMLResponse)
async def action_queue_note(
    request: Request,
    target: str = Form(""),
    text: str = Form(""),
    _: None = Depends(require_owner_action),
):
    return await _handle_writeback(request, "note", target, text)


@router.post("/queue/actions/retry", response_class=HTMLResponse)
async def action_queue_retry(
    request: Request,
    entry_id: int = Form(...),
    _: None = Depends(require_owner_action),
):
    entry = writeback.get_entry(entry_id)
    if entry is None:
        return await _render_owner_queue(
            request,
            banner={"ok": False, "text": f"unknown writeback entry #{entry_id}"},
        )
    entry = await writeback.attempt_commit(entry_id)
    return await _render_owner_queue(request, banner=_entry_banner(entry))


@router.post("/queue/actions/draft", response_class=HTMLResponse)
async def action_queue_draft(
    request: Request,
    action: str = Form(...),
    target: str = Form(""),
    text: str = Form(""),
    _: None = Depends(require_owner_action),
):
    """AI drafting assist: returns the page with a pre-filled, editable
    draft form. NOTHING is stored or committed here — the AI never writes
    back; only the owner's explicit submit on the draft form does."""
    target = target.strip()[: writeback.TARGET_MAX_CHARS]
    text = text.strip()[: writeback.TEXT_MAX_CHARS]
    if action not in writeback.ACTIONS:
        return await _render_owner_queue(
            request, banner={"ok": False, "text": f"unknown action {action!r}"}
        )
    # Grounding: the item's own details, found server-side by headline —
    # never client-supplied context beyond the target name itself.
    data = await owner_queue.overview(refresh=False)
    item = next(
        (it for it in data["items"] if owner_queue.headline(it) == target),
        None,
    )
    try:
        drafted = owner_assist.draft(action, item, text)
    except owner_assist.AssistUnavailable as exc:
        return await _render_owner_queue(
            request,
            banner={"ok": False, "text": f"AI draft unavailable: {exc}"},
        )
    return await _render_owner_queue(
        request,
        banner={
            "ok": True,
            "text": (
                "draft ready below — edit it, then submit; nothing is "
                "stored until you do"
            ),
        },
        draft={"action": action, "target": target, "text": drafted},
    )


@router.post("/actions/refresh", response_class=HTMLResponse)
async def action_refresh(request: Request, _: None = Depends(require_owner_action)):
    dropped = github.clear_cache()
    banner = {
        "ok": True,
        "text": (
            f"cache cleared — {dropped} entr{'y' if dropped == 1 else 'ies'} "
            "dropped; the board below is re-fetched live"
        ),
    }
    return await _render_with_banner(request, banner)


# ---------------------------------------------------------------------------
# Owner-action PREFLIGHT (2026-07-15) — the "see the target before firing"
# half of the launch console. The rerun-ci action used to resolve "the newest
# failed run on main" AT FIRE TIME, so the owner fired blind. Now:
#
#   GET  /owner/actions/rerun-ci/preview   read-only (plain require_owner,
#        like every other /owner GET): resolves the newest failed run with
#        refresh=True and renders its facts + a confirm form carrying the
#        PINNED run id. Never writes anything.
#   POST /owner/actions/rerun-ci           REQUIRES the pinned run_id,
#        re-resolves with refresh=True and fires ONLY when the pin is still
#        the newest failed run — anything moved (no pin, run vanished, no
#        longer failed, newer failed appeared) FAILS CLOSED: zero fires, an
#        honest banner naming exactly what moved, the preview re-rendered.
#        After a real fire, a verification chip re-GETs the run so the owner
#        sees it actually started (honest-unknown when the re-GET fails).
#
# The refresh action gets the same cheap preview on the same generic
# template; its POST contract is deliberately untouched (ORDER 013 security
# tests POST it directly). The require_owner_action floor (auth → strict
# Origin/Referer → per-route rate limit) stays exactly as-is.
# ---------------------------------------------------------------------------

RERUN_BRANCH = "main"

# GitHub run `status` values that mean "the rerun really started".
_RUN_STARTED_STATUSES = ("queued", "in_progress", "waiting", "requested", "pending")


def _run_facts(run: dict) -> list[dict]:
    """The preview facts table for one workflow run — id, workflow, branch,
    head sha, created + age (fleet's freshness math, honest 'age unknown'
    on an unparseable timestamp), and the run's own page as evidence."""
    created = run.get("created_at") or ""
    age = fleet.freshness(created)
    return [
        {"label": "run id", "value": f"#{run.get('id')}", "code": True},
        {"label": "workflow", "value": run.get("name") or "unknown"},
        {"label": "title", "value": run.get("display_title") or "—"},
        {"label": "branch", "value": run.get("head_branch") or "unknown", "code": True},
        {"label": "head sha", "value": (run.get("head_sha") or "unknown")[:8], "code": True},
        {
            "label": "created",
            "value": f"{created or 'unknown'} ({age['age_human']})",
        },
        {
            "label": "run page",
            "value": "open on GitHub",
            "url": run.get("html_url", ""),
        },
    ]


def _jobs_fact(jobs_res: dict) -> dict:
    """The "jobs that will re-run" facts row — names the exact subset
    ``rerun-failed-jobs`` fires at, from an already-fetched jobs listing.
    Honest on every degraded shape; never blocks the preview."""
    label = "jobs that will re-run"
    if not jobs_res.get("ok"):
        return {
            "label": label,
            "value": (
                f"unknown — {jobs_res.get('message') or 'could not list jobs'}"
                " (the re-run itself is unaffected)"
            ),
        }
    failed = github.failed_jobs(jobs_res.get("jobs") or [])
    total = jobs_res.get("total") or 0
    if not failed:
        return {
            "label": label,
            "value": (
                f"none listed as failed right now (0 of {total} "
                f"job{'s' if total != 1 else ''}) — the run may have moved; "
                "the confirm re-checks"
            ),
        }
    names = ", ".join(j.get("name") or "unnamed job" for j in failed)
    return {
        "label": label,
        "value": (
            f"{names} ({len(failed)} of {total} "
            f"job{'s' if total != 1 else ''})"
        ),
        "code": True,
    }


async def _preview_jobs(repo: str, resolved: dict) -> dict | None:
    """Fetch the resolved run's jobs for the preview row (read-only,
    refresh=True — same live-truth rule as the pin itself). ``None`` when
    there is no resolved run to list jobs for."""
    run = resolved.get("run")
    if not resolved.get("ok") or run is None:
        return None
    return await github.run_jobs(repo, run.get("id"), refresh=True)


def _render_rerun_preview(
    request: Request,
    repo: str,
    resolved: dict,
    banner: dict | None = None,
    chip: dict | None = None,
    fired: bool = False,
    jobs: dict | None = None,
) -> HTMLResponse:
    """Render the rerun-ci preflight page from an already-resolved read.

    Pure view — performs NO fetch and NO write itself; the caller supplies
    the (refresh=True) resolution. After a real fire (``fired=True``) the
    confirm form is deliberately omitted so the result page cannot invite a
    double-fire."""
    p: dict = {
        "title": f"re-run failed CI on {repo} — preflight",
        "lede": (
            "Preview of exactly which failed run the re-run would fire at — "
            "nothing fires until you confirm below, and the confirm fails "
            "closed if the picture moves in between."
        ),
        "banner": banner,
        "chip": chip,
        "facts": None,
        "empty": None,
        "confirm": None,
    }
    run = resolved.get("run")
    if not resolved.get("ok"):
        p["empty"] = (
            f"could not resolve the latest failed run on {repo}@{RERUN_BRANCH} — "
            f"{resolved.get('message') or 'unknown error'} — nothing to confirm"
        )
    elif run is None:
        p["empty"] = (
            f"nothing to re-run — no failed run on {RERUN_BRANCH} for {repo} "
            "right now"
        )
    else:
        p["facts"] = _run_facts(run)
        if jobs is not None:
            # right after the workflow row — the run's identity first, then
            # exactly which of its jobs the fire would re-run
            p["facts"].insert(2, _jobs_fact(jobs))
        if not fired:
            p["confirm"] = {
                "action": "/owner/actions/rerun-ci",
                "fields": {"repo": repo, "run_id": run.get("id")},
                "label": f"re-run failed jobs of run #{run.get('id')}",
                "note": (
                    "fires at exactly this pinned run — if a newer failed run "
                    "appears first, the confirm refuses and re-previews"
                ),
            }
    return templates.TemplateResponse(request, "owner_preflight.html", {"p": p})


@router.get("/actions/rerun-ci/preview", response_class=HTMLResponse)
async def rerun_ci_preview(
    request: Request, repo: str = "", _: None = Depends(require_owner)
):
    """Read-only preflight for the rerun-ci action (plain require_owner —
    this GET changes nothing). Resolves the newest failed run with
    refresh=True so the pin is minted from live truth, never the TTL cache."""
    if repo not in config.REPOS:
        p = {
            "title": "re-run failed CI — preflight",
            "lede": (
                "Preview of exactly which failed run a re-run would fire at — "
                "nothing fires from this page."
            ),
            "banner": (
                {"ok": False, "text": f"unknown repo: {repo!r} — pick one on the owner board"}
                if repo
                else None
            ),
            "empty": (
                "no repo selected — use the re-run form on the owner board "
                "to choose one"
            ),
            "facts": None,
            "chip": None,
            "confirm": None,
        }
        return templates.TemplateResponse(request, "owner_preflight.html", {"p": p})
    resolved = await github.latest_failed_run(repo, branch=RERUN_BRANCH, refresh=True)
    jobs = await _preview_jobs(repo, resolved)
    return _render_rerun_preview(request, repo, resolved, jobs=jobs)


async def _stale_pin_banner(repo: str, pinned_id: int, newest: dict | None) -> dict:
    """Name exactly what moved between preview and confirm — re-GETs the
    pinned run itself so the owner learns WHICH invariant broke, never a
    generic 'something changed'. Always fail-closed copy: nothing fired."""
    info = await github.run_info(repo, pinned_id, refresh=True)
    if info["status"] == 404:
        what = f"the pinned run #{pinned_id} no longer exists on GitHub"
    elif info["ok"] and isinstance(info["data"], dict):
        conclusion = info["data"].get("conclusion")
        status = info["data"].get("status")
        if conclusion == "failure":
            if newest is not None:
                what = (
                    f"a newer failed run (#{newest.get('id')}) appeared on "
                    f"{RERUN_BRANCH} after run #{pinned_id} was pinned"
                )
            else:
                what = (
                    f"run #{pinned_id} is still failed but is no longer listed "
                    f"as the newest failed run on {RERUN_BRANCH}"
                )
        else:
            what = (
                f"run #{pinned_id} is no longer failed "
                f"(now {conclusion or status or 'unknown'})"
            )
    else:
        reason = info["error"] or f"HTTP {info['status']}"
        what = f"could not re-check the pinned run #{pinned_id} ({reason})"
    return {
        "ok": False,
        "text": (
            f"nothing fired — {what}; the preview below shows what is "
            "newest-failed now"
        ),
    }


async def _post_fire_chip(
    repo: str, run_id: int, failed_before: list | None = None
) -> dict:
    """Post-action verification: report whether the rerun really started
    (the askverify chip idiom — honest-unknown when the re-GET fails, never
    an assumed success).

    When the confirm handler pinned the FAILED JOBS before firing
    (``failed_before``), verify at the job level: re-GET the run's jobs and
    check that each previously-failed job now reports a started status —
    the precise claim, since ``rerun-failed-jobs`` re-runs exactly that
    subset. Falls back to the original run-level check when the jobs
    listing is unavailable on either side of the fire."""
    if failed_before:
        after = await github.run_jobs(repo, run_id, refresh=True)
        if after.get("ok"):
            probe = (
                f"re-GET of run #{run_id}'s jobs immediately after the fire "
                "(read-only)"
            )
            by_name = {
                j.get("name"): j
                for j in after.get("jobs") or []
                if isinstance(j, dict)
            }
            states = []
            all_started = True
            url = ""
            for j in failed_before:
                name = j.get("name") or "unnamed job"
                cur = by_name.get(name)
                if cur is None:
                    states.append(f"{name}: not listed")
                    all_started = False
                    continue
                status = cur.get("status") or "unknown"
                started = (
                    status in _RUN_STARTED_STATUSES
                    and not cur.get("conclusion")
                )
                all_started = all_started and started
                states.append(f"{name}: {status}")
                url = url or cur.get("html_url", "")
            detail = "; ".join(states)
            if all_started:
                return {
                    "css": "ok",
                    "label": "failed jobs re-queued",
                    "probe": probe,
                    "detail": detail,
                    "url": url,
                }
            return {
                "css": "warn",
                "label": "failed jobs not all re-queued yet",
                "probe": probe,
                "detail": (
                    f"{detail} — a fresh attempt can take a moment to "
                    "register; check the run page"
                ),
                "url": url,
            }
        # jobs re-GET failed → the run-level check below is the honest
        # fallback (never an assumed success)
    info = await github.run_info(repo, run_id, refresh=True)
    probe = f"re-GET of run #{run_id} immediately after the fire (read-only)"
    if info["ok"] and isinstance(info["data"], dict):
        status = info["data"].get("status") or "unknown"
        url = info["data"].get("html_url", "")
        if status in _RUN_STARTED_STATUSES:
            return {
                "css": "ok",
                "label": f"rerun started — {status}",
                "probe": probe,
                "detail": f"run #{run_id} re-checked live after the fire",
                "url": url,
            }
        return {
            "css": "warn",
            "label": f"run status: {status}",
            "probe": probe,
            "detail": (
                f"run #{run_id} did not report queued/in_progress yet — "
                "check the run page"
            ),
            "url": url,
        }
    reason = info["error"] or f"HTTP {info['status']}"
    return {
        "css": "unknown",
        "label": "rerun not verified",
        "probe": probe,
        "detail": (
            f"the fire was accepted but re-checking run #{run_id} failed "
            f"({reason}) — outcome unknown, check the run page"
        ),
        "url": "",
    }


@router.get("/actions/refresh/preview", response_class=HTMLResponse)
async def refresh_preview(request: Request, _: None = Depends(require_owner)):
    """Read-only preflight for the cache-refresh action, riding the same
    generic template: how many cache entries the POST would drop, and the
    confirm form POSTing the UNCHANGED /owner/actions/refresh contract."""
    n = github.cache_size()
    p = {
        "title": "force cache refresh — preflight",
        "lede": (
            "Preview of what the cache-refresh action would do — nothing is "
            "cleared until you confirm below. Reversible and cheap: the cache "
            "re-fills on demand from live fetches."
        ),
        "banner": None,
        "chip": None,
        "facts": [
            {
                "label": "cache entries that will drop",
                "value": str(n),
                "code": True,
            },
            {"label": "cache TTL", "value": f"{config.CACHE_TTL_SECONDS}s"},
            {
                "label": "reversibility",
                "value": "full — the next page load re-fetches live",
            },
        ],
        "empty": None,
        "confirm": {
            "action": "/owner/actions/refresh",
            "fields": {},
            "label": f"clear the cache now ({n} entr{'y' if n == 1 else 'ies'})",
            "note": (
                "POSTs the existing refresh action — same gate "
                "(auth → same-origin → rate limit), unchanged contract"
            ),
        },
    }
    return templates.TemplateResponse(request, "owner_preflight.html", {"p": p})


@router.post("/actions/rerun-ci", response_class=HTMLResponse)
async def action_rerun_ci(
    request: Request,
    repo: str = Form(...),
    run_id: str = Form(""),
    _: None = Depends(require_owner_action),
):
    """The PINNED confirm. Requires the run_id the preview minted; re-resolves
    the newest failed run with refresh=True and fires ONLY on an exact match —
    every mismatch fails closed with an honest banner and a fresh preview.
    NEVER falls back to firing at 'whatever is newest failed now'."""
    if repo not in config.REPOS:
        banner = {"ok": False, "text": f"unknown repo: {repo!r}"}
        return await _render_with_banner(request, banner)
    resolved = await github.latest_failed_run(repo, branch=RERUN_BRANCH, refresh=True)
    pinned = run_id.strip()
    if not pinned.isdigit():
        banner = {
            "ok": False,
            "text": (
                "nothing fired — the confirm carried no pinned run id; this "
                "action never falls back to \"whatever is newest failed\". "
                "Confirm from the preview below"
            ),
        }
        jobs = await _preview_jobs(repo, resolved)
        return _render_rerun_preview(
            request, repo, resolved, banner=banner, jobs=jobs
        )
    pinned_id = int(pinned)
    if not resolved["ok"]:
        banner = {
            "ok": False,
            "text": (
                f"nothing fired — could not re-verify the pinned run "
                f"#{pinned_id}: {resolved['message']}"
            ),
        }
        return _render_rerun_preview(request, repo, resolved, banner=banner)
    newest = resolved["run"]
    if newest is None or newest.get("id") != pinned_id:
        banner = await _stale_pin_banner(repo, pinned_id, newest)
        jobs = await _preview_jobs(repo, resolved)
        return _render_rerun_preview(
            request, repo, resolved, banner=banner, jobs=jobs
        )
    # one extra read pins the JOB NAMES the fire will re-run — the chip then
    # verifies exactly those; a failed listing degrades to run-level verify
    jobs_before = await github.run_jobs(repo, pinned_id, refresh=True)
    failed_before = (
        github.failed_jobs(jobs_before.get("jobs") or [])
        if jobs_before.get("ok")
        else None
    )
    fired = await github.rerun_run(
        repo, pinned_id, run=newest, branch=RERUN_BRANCH
    )
    if not fired["ok"]:
        banner = {
            "ok": False,
            "text": fired["message"],
            "url": fired.get("url") or newest.get("html_url", ""),
        }
        return _render_rerun_preview(
            request, repo, resolved, banner=banner, jobs=jobs_before
        )
    chip = await _post_fire_chip(repo, pinned_id, failed_before=failed_before)
    banner = {
        "ok": True,
        "text": fired["message"],
        "url": fired.get("url") or newest.get("html_url", ""),
    }
    return _render_rerun_preview(
        request,
        repo,
        resolved,
        banner=banner,
        chip=chip,
        fired=True,
        jobs=jobs_before,
    )
