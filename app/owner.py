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
    config,
    envdrift,
    envhub,
    github,
    listfilter,
    nav,
    owner_assist,
    owner_queue,
    prompts,
    railway,
    readiness,
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


def _enforce_rate_limit(request: Request) -> None:
    """Sliding-window limiter per (route path, client host); 429 when tripped."""
    client_host = request.client.host if request.client else "unknown"
    key = f"{request.url.path}|{client_host}"
    now = time.monotonic()
    bucket = _rate_buckets[key]
    while bucket and now - bucket[0] > RATE_LIMIT_WINDOW_SECONDS:
        bucket.popleft()
    if len(bucket) >= RATE_LIMIT_MAX_REQUESTS:
        retry_after = max(1, int(RATE_LIMIT_WINDOW_SECONDS - (now - bucket[0])) + 1)
        raise HTTPException(
            status_code=429,
            detail="rate limit exceeded for owner actions — retry shortly",
            headers={"Retry-After": str(retry_after)},
        )
    bucket.append(now)


def require_owner(request: Request) -> None:
    """Dependency gating every /owner route. Raises 503 (unset) or 401 (bad)."""
    if not config.SITE_PASSWORD:
        # Fail closed: an unset password never means an open door. The public
        # site is unaffected — only this gated area 503s.
        raise HTTPException(
            status_code=503,
            detail="owner area unavailable: SITE_PASSWORD is not configured",
        )
    header = request.headers.get("authorization", "")
    supplied = ""
    if header.lower().startswith("basic "):
        try:
            decoded = base64.b64decode(header.split(" ", 1)[1]).decode("utf-8")
            _user, _, supplied = decoded.partition(":")
        except Exception:
            supplied = ""
    if not supplied or not secrets.compare_digest(supplied, config.SITE_PASSWORD):
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
    rows, envcov, promptstate = await asyncio.gather(
        readiness.board(refresh=_refresh(request), reveal_secrets=True),
        envhub.board_rollup(refresh=_refresh(request)),
        prompts.console_rollup(refresh=_refresh(request)),
    )
    return templates.TemplateResponse(
        request,
        "owner.html",
        {
            "rows": rows,
            "envcov": envcov,
            "promptstate": promptstate,
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
    boundary in app/railway.py."""
    data = await railway.overview(refresh=_refresh(request))
    envdrift.annotate(data)
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
    rows, envcov, promptstate = await asyncio.gather(
        readiness.board(reveal_secrets=True),
        envhub.board_rollup(),
        prompts.console_rollup(),
    )
    return templates.TemplateResponse(
        request,
        "owner.html",
        {
            "rows": rows,
            "envcov": envcov,
            "promptstate": promptstate,
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
        return {
            "ok": True,
            "text": (
                f"{entry['action']} committed to {entry['path']} — "
                f"commit {entry['commit_sha'][:8]}"
            ),
            "url": entry["commit_url"],
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


@router.post("/queue/actions/complete", response_class=HTMLResponse)
async def action_queue_complete(
    request: Request,
    target: str = Form(...),
    text: str = Form(""),
    _: None = Depends(require_owner_action),
):
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


@router.post("/actions/rerun-ci", response_class=HTMLResponse)
async def action_rerun_ci(
    request: Request, repo: str = Form(...), _: None = Depends(require_owner_action)
):
    if repo not in config.REPOS:
        banner = {"ok": False, "text": f"unknown repo: {repo!r}"}
        return await _render_with_banner(request, banner)
    result = await github.rerun_latest_failed(repo)
    banner = {
        "ok": bool(result.get("ok")),
        "text": result.get("message", "re-run attempted"),
        "url": result.get("url"),
    }
    return await _render_with_banner(request, banner)
