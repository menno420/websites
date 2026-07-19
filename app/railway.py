"""Railway read layer for the gated /owner/environments page.

Executes slice 1 of the owner-directed plan
``docs/planning/live-env-visibility-plan-2026-07-11.md`` (ORDER 015): show
what is configured where across the four Railway services, live where
possible, honest where not.

Two data halves, deliberately separated:

1. **Committed facts** (``SERVICES``): what the repo itself proves about each
   service — package, Dockerfile, public URL, and the env-var NAMES each
   service documents (names + one-line purpose + a per-variable "manage →"
   deep link, matched by name prefix per the plan). No network, always
   available. The control-plane can additionally report set/unset for its OWN
   documented vars straight from its runtime environment — presence only,
   never a value.

2. **Live Railway reads** (``live_overview``): variable NAMES per service via
   the Railway GraphQL API, authenticated by a **project-scoped**
   ``RAILWAY_TOKEN`` (superbot-websites only). This is the plan's option (A):
   names + presence, **never values** — ``_names_only`` drops the values at
   the client boundary so no secret value ever reaches a template or cache.
   Degradation is honest: ``not-configured`` while the token is unset (the
   documented state until the owner mints it — an owner errand, not a bug)
   and ``unavailable`` with the exact reason on any fetch failure. Never a
   500, never fabricated liveness.

RAILWAY SAFETY (docs/RAILWAY-SAFETY.md, binding): this module never reads the
ambient production-bot Railway IDs and never touches the account key. The one
project it can see is pinned by the token's own scope; the explicit SAFE
project id below is the documented superbot-websites literal, used only to
build console deep links. Read-only: the only GraphQL operations issued are
queries — no mutation strings exist in this module.
"""

from __future__ import annotations

import asyncio
import os
import time
from typing import Any

import httpx

from . import config
from .github import short_reason

GRAPHQL_URL = "https://backboard.railway.app/graphql/v2"

# The dedicated superbot-websites project — explicit SAFE literals from
# docs/RAILWAY-SAFETY.md / docs/deployment.md (never read from the ambient
# environment). Used only for console deep links.
PROJECT_NAME = "superbot-websites"
PROJECT_ID = "70198ece-cbc0-484e-86d9-f8a1eca4f045"
PROJECT_URL = f"https://railway.app/project/{PROJECT_ID}"

# Per-variable "manage →" deep links, matched by name prefix (the plan's
# console-link table, seeded from fleet-manager environments/env-grant-policy
# targets; anything unmatched manages at the project's Railway variables UI).
MANAGE_LINKS: list[tuple[str, str, str]] = [
    ("DISCORD_", "Discord developer portal", "https://discord.com/developers/applications"),
    ("STRIPE_", "Stripe dashboard", "https://dashboard.stripe.com/apikeys"),
    ("GITHUB_", "GitHub token settings", "https://github.com/settings/tokens"),
    ("GH_", "GitHub token settings", "https://github.com/settings/tokens"),
    ("ANTHROPIC_", "Anthropic console", "https://console.anthropic.com/settings/keys"),
    ("PAYPAL_", "PayPal developer dashboard", "https://developer.paypal.com/dashboard/"),
    ("RAILWAY_", "Railway project", PROJECT_URL),
]
_DEFAULT_MANAGE = (f"Railway variables — {PROJECT_NAME}", PROJECT_URL)


def manage_link(name: str) -> dict[str, str]:
    """The manage-here deep link for one variable name (prefix-matched)."""
    upper = name.upper()
    for prefix, label, url in MANAGE_LINKS:
        if upper.startswith(prefix):
            return {"label": label, "url": url}
    label, url = _DEFAULT_MANAGE
    return {"label": label, "url": url}


def _var(name: str, purpose: str) -> dict[str, Any]:
    return {"name": name, "purpose": purpose, "manage": manage_link(name)}


# Committed per-service facts. Hand-kept like config.REPOS — the source of
# truth is each service's own config module + Dockerfile + docs/deployment.md.
SERVICES: list[dict[str, Any]] = [
    {
        "name": "control-plane",
        "package": "app/",
        "dockerfile": "Dockerfile",
        "requirements": "requirements.txt",
        "url": "https://control-plane-production-abb0.up.railway.app",
        "self": True,  # THIS app — can report its own env presence live.
        "env_vars": [
            _var("GITHUB_TOKEN", "PAT for GitHub REST reads (board cells; admin scope un-masks secrets counts)"),
            _var("SITE_PASSWORD", "gates the /owner area (HTTP Basic; unset → /owner fails closed 503)"),
            _var("RAILWAY_TOKEN", "project-scoped Railway read token for THIS page's live section (set on the deployed service 2026-07-12, ORDER 022)"),
            _var("PORT", "bind port (Railway injects it)"),
            _var("GITHUB_API_BASE", "REST base override (testing behind restricted egress)"),
            _var("GITHUB_RAW_BASE", "raw-content base override"),
            _var("CACHE_TTL_SECONDS", "server-side GitHub cache TTL (default 180)"),
            _var("AUTOREFRESH_SECONDS", "board//fleet live-monitoring poll interval (default 45)"),
            _var("FLEET_STALE_HOURS", "heartbeat staleness threshold on /fleet (default 12)"),
            _var("CLAIM_STALE_HOURS", "order-claim staleness threshold on /orders (default 24)"),
            _var("ANTHROPIC_API_KEY", "Claude API key for the owner-console drafting assistant (app/owner_assist.py; optional — unset degrades to manual drafting)"),
            _var("OWNER_ASSIST_MODEL", "drafting-assistant model override (default pinned in app/owner_assist.py)"),
            _var("OWNER_ASSIST_DAILY_CAP", "drafting-assistant daily call cap (default 30)"),
            _var("WRITEBACK_BRANCH", "owner-writeback target branch (default main)"),
            _var("WRITEBACK_BRANCH_PREFIX", "owner-writeback PR branch-name prefix (optional; default claude/owner-writeback- — the claude/* prefix is what arms the auto-merge-enabler)"),
            _var("WRITEBACK_DB_PATH", "SQLite path for the writeback audit log (default app/writeback.sqlite3 — ephemeral on Railway, stated in the UI)"),
            _var("DISCORD_CLIENT_ID", "Discord OAuth owner login — client id, reused from the existing SuperBot Discord app (app/discord_auth.py; ASK-0002; unset → /owner/login says not-configured and the gate falls back to SITE_PASSWORD)"),
            _var("DISCORD_CLIENT_SECRET", "Discord OAuth owner login — client secret from the SuperBot app (app/discord_auth.py; ASK-0002; name only, never a value)"),
            _var("OWNER_DISCORD_ID", "Discord OAuth owner login — the owner's Discord user id; the callback mints a session only when the returned id matches (app/discord_auth.py; ASK-0002)"),
            _var("OWNER_SESSION_SECRET", "Discord OAuth owner login — HMAC secret signing the owner session cookie (app/discord_auth.py; ASK-0002; name only, never a value)"),
            _var("DISCORD_REDIRECT_URI", "Discord OAuth owner login — optional redirect-URI override; unset derives it from the request base URL + /owner/auth/callback (app/discord_auth.py; ASK-0002)"),
        ],
    },
    {
        "name": "botsite",
        "package": "botsite/",
        "dockerfile": "botsite/Dockerfile",
        "requirements": "botsite/requirements.txt",
        "url": "https://botsite-production-cfd7.up.railway.app",
        "self": False,
        "env_vars": [
            _var("SITE_JSON_URL", "committed site.json content source (raw.githubusercontent)"),
            _var("ADD_TO_DISCORD_URL", "the bot's OAuth invite link"),
            _var("SITE_CACHE_TTL_SECONDS", "content cache TTL (default 180)"),
            _var("ANTHROPIC_API_KEY", "Claude API key for the tester-program AI exit review (botsite/testing_ai.py; set on the service 2026-07-12, ORDER 022 — docs/owner/OWNER-ACTIONS.md row K)"),
            _var("TESTING_AI_MODEL", "exit-review + guide model override (default pinned in botsite/testing_ai.py)"),
            _var("TESTING_AI_DAILY_CAP", "daily AI-call spend cap shared by exit reviews + guide (default 50)"),
            _var("TESTING_AI_GUIDE_CAP", "per-claim guide-message cap, chat + screen frames (default 20)"),
            _var("SITE_PASSWORD", "OPTIONAL fallback gate for the tester-program owner queue (HTTP Basic; a Discord owner session is preferred — ORDER 037; with NEITHER configured the queue fails closed 503)"),
            _var("DISCORD_CLIENT_ID", "Discord OAuth owner login — client id, reused from the existing SuperBot Discord app (botsite/discord_auth.py; ORDER 037; unset → /owner/login says not-configured and the gate falls back to SITE_PASSWORD)"),
            _var("DISCORD_CLIENT_SECRET", "Discord OAuth owner login — client secret from the SuperBot app (botsite/discord_auth.py; ORDER 037; name only, never a value)"),
            _var("OWNER_DISCORD_ID", "Discord OAuth owner login — the owner's Discord user id; the callback mints a session only when the returned id matches (botsite/discord_auth.py; ORDER 037)"),
            _var("OWNER_SESSION_SECRET", "Discord OAuth owner login — HMAC secret signing the owner session cookie (botsite/discord_auth.py; ORDER 037; name only, never a value)"),
            _var("DISCORD_REDIRECT_URI", "Discord OAuth owner login — optional redirect-URI override; unset derives it from the request base URL + /owner/auth/callback (botsite/discord_auth.py; ORDER 037)"),
            _var("TESTING_DB_PATH", "SQLite path for the tester-program store (default botsite/testing.sqlite3 — ephemeral on Railway, stated in the UI)"),
            _var("DATABASE_URL", "Postgres/SQLite URL for the durable /submit intake store (botsite/submissions_store.py; unset → intake reports not-live — ORDER 034 / ASK-0004)"),
            _var("TESTING_BOUNTY_CAP_USD", "outstanding-bounty exposure cap (default 200)"),
            _var("TESTING_AUTOPAY_ENABLED", "auto-payout kill switch — absent/false is OFF (v1 payouts are dry-run regardless)"),
            _var("TESTING_AUTOPAY_MIN_SCORE", "AI exit-review score threshold for autopay eligibility (default 80)"),
            _var("TESTING_PAYOUT_DAILY_CAP_USD", "payout daily cap (default 60)"),
            _var("TESTING_PAYOUT_MONTHLY_CAP_USD", "payout monthly cap (default 300)"),
            _var("PAYPAL_CLIENT_ID", "PayPal Payouts credential, name only (v1 adapter is dry-run — botsite/testing_payouts.py)"),
            _var("PAYPAL_CLIENT_SECRET", "PayPal Payouts credential, name only (v1 adapter is dry-run — botsite/testing_payouts.py)"),
            _var("PORT", "bind port (Railway injects it)"),
        ],
    },
    {
        "name": "dashboard",
        "package": "dashboard/",
        "dockerfile": "dashboard/Dockerfile",
        "requirements": "dashboard/requirements.txt",
        "url": "https://dashboard-production-a91b.up.railway.app",
        "self": False,
        "env_vars": [
            _var("DASHBOARD_JSON_URL", "committed dashboard.json data source (raw.githubusercontent)"),
            _var("ARCADE_JSON_URL", "committed arcade.json counts source for the fleet arcade (raw.githubusercontent; optional, default menno420/websites@main)"),
            _var("RELEASES_JSON_URL", "committed release-drift mirror source for the /status release-drift card, baked by the review service (raw.githubusercontent; optional, default menno420/websites@main)"),
            _var("CONSOLE_JSON_URL", "committed console feed data source"),
            _var("DATA_CACHE_TTL_SECONDS", "data cache TTL (default 180)"),
            _var("SUPERBOT_REPO", "upstream repo for committed JSON (default menno420/superbot)"),
            _var("SUPERBOT_REF", "upstream ref (default main)"),
            _var("BOTSITE_GAMES_URL", "consolidation-redirect target for /games — the re-homed games surface on the botsite service (optional; default botsite-production-cfd7/games — env-overridable for cutover)"),
            _var("REVIEW_REVIEWS_URL", "consolidation-redirect target for /reviews — the re-homed reviews surface on the review service (optional; default review-production-fc91/reviews — env-overridable for cutover)"),
            _var("DISCORD_CLIENT_ID", "Discord OAuth owner login — client id, reused from the existing SuperBot Discord app (dashboard/discord_auth.py; ORDER 038; unset → /admin/login says not-configured and the admin actions stay locked — Discord-only, no SITE_PASSWORD)"),
            _var("DISCORD_CLIENT_SECRET", "Discord OAuth owner login — client secret from the SuperBot app (dashboard/discord_auth.py; ORDER 038; name only, never a value)"),
            _var("OWNER_DISCORD_ID", "Discord OAuth owner login — the owner's Discord user id; the callback mints a session only when the returned id matches (dashboard/discord_auth.py; ORDER 038)"),
            _var("OWNER_SESSION_SECRET", "Discord OAuth owner login — HMAC secret signing the owner session cookie (dashboard/discord_auth.py; ORDER 038; name only, never a value)"),
            _var("DISCORD_REDIRECT_URI", "Discord OAuth owner login — optional redirect-URI override; unset derives it from the request base URL + /admin/auth/callback (dashboard/discord_auth.py; ORDER 038)"),
            _var("PORT", "bind port (Railway injects it)"),
        ],
    },
    {
        # Was omitted while the review service had no Railway deployment;
        # the owner created + verified it live 2026-07-12
        # (docs/owner/OWNER-ACTIONS.md row J) — ORDER 021 adds the row.
        "name": "review",
        "package": "review/",
        "dockerfile": "review/Dockerfile",
        "requirements": "review/requirements.txt",
        "url": "https://review-production-fc91.up.railway.app",
        "self": False,
        "env_vars": [
            _var("ANTHROPIC_API_KEY", "Claude API key for the /ask live assistant (set on the service 2026-07-12, ORDER 022)"),
            _var("REVIEW_AI_MODEL", "assistant model override (default pinned in review/ai.py)"),
            _var("REVIEW_AI_LOG_SALT", "salt for the assistant's hashed rate-limit keys (random per boot when unset)"),
            _var("PORT", "bind port (Railway injects it)"),
        ],
    },
]

# One-snapshot TTL cache for the live read (mirrors app/github.py's shape:
# in-memory, TTL = config.CACHE_TTL_SECONDS, ?refresh=1 bypasses). Only OK
# snapshots are cached — failures retry on the next request.
_cache: dict[str, tuple[float, dict]] = {}
_cache_lock = asyncio.Lock()
_CACHE_KEY = "railway-live"


def clear_cache() -> int:
    """Drop the live snapshot (test isolation + the owner refresh path)."""
    n = len(_cache)
    _cache.clear()
    return n


def _make_client() -> httpx.AsyncClient:
    """The one-shot client ``_graphql`` posts through.

    A seam, not a feature: tests hand the REAL ``_graphql`` an
    ``httpx.MockTransport`` client here (the #240 idiom — stubbing
    ``_graphql`` itself would bypass the reason-bounding under test).
    """
    return httpx.AsyncClient(timeout=15.0, trust_env=True)


async def _graphql(query: str, variables: dict | None = None) -> dict[str, Any]:
    """One GraphQL query against Railway. Returns {ok, data, error}.

    Sends the project-scoped token as ``Project-Access-Token`` (Railway's
    documented header for project tokens). Read-only by construction: callers
    only pass query strings. Query shapes VERIFIED 2026-07-12 against the live
    API (backboard.railway.app/graphql/v2): ``projectToken`` exposes
    ``projectId``/``environmentId``; ``project(id:)`` returns ``name`` +
    ``services.edges[].node{id,name}``; ``variables(projectId:,
    environmentId:, serviceId:)`` returns a name→value JSON map (names kept,
    values dropped in ``_names_only``). Any future shape/auth mismatch still
    surfaces as an honest ``unavailable`` reason, never a 500 — and every
    reason minted here rides ``app.github.short_reason`` (the PR #240
    envelope bound: 140 chars, single line, markup bodies replaced), so the
    owner environments/envhub/envdrift pages can never render an upstream
    error DOCUMENT as a banner.
    """
    headers = {
        "Project-Access-Token": config.RAILWAY_TOKEN,
        "Content-Type": "application/json",
        "User-Agent": "websites-control-plane",
    }
    payload: dict[str, Any] = {"query": query}
    if variables:
        payload["variables"] = variables
    try:
        async with _make_client() as client:
            resp = await client.post(GRAPHQL_URL, json=payload, headers=headers)
    except httpx.HTTPError as exc:
        # Exception text is upstream-shaped (may be long/multiline) — same
        # 140-char single-line bound as the GitHub envelopes (PR #240).
        return {
            "ok": False,
            "data": None,
            "error": short_reason(f"{type(exc).__name__}: {exc}"),
        }
    try:
        body = resp.json()
    except ValueError:
        # The body is an upstream document, not a reason — as before, only
        # the status is exposed (never body text); short_reason keeps the
        # phrase on the same single-line bounded contract as the rest.
        return {
            "ok": False,
            "data": None,
            "error": short_reason(f"HTTP {resp.status_code}: non-JSON response"),
        }
    if resp.status_code >= 300 or (isinstance(body, dict) and body.get("errors")):
        errors = body.get("errors") if isinstance(body, dict) else None
        msg = (
            # Replaces the old bare [:300] cap: the joined GraphQL error
            # messages ride the same short_reason bound as every GitHub
            # envelope (140 chars, single line, markup stripped).
            short_reason(
                "; ".join(str(e.get("message", e)) for e in errors),
                status=resp.status_code if resp.status_code >= 300 else None,
            )
            if isinstance(errors, list)
            else short_reason(f"HTTP {resp.status_code}")
        )
        return {"ok": False, "data": None, "error": msg}
    return {"ok": True, "data": body.get("data") if isinstance(body, dict) else None, "error": ""}


def _names_only(varmap: Any) -> list[str]:
    """Variable NAMES from Railway's name→value map — the values are dropped
    HERE, at the client boundary, so they never reach a cache or template
    (plan option A: names + presence, never values)."""
    if not isinstance(varmap, dict):
        return []
    return sorted(varmap.keys())


async def live_overview(refresh: bool = False) -> dict[str, Any]:
    """Live variable NAMES per service, or an honest degraded state.

    ``state``: ``ok`` | ``not-configured`` (RAILWAY_TOKEN unset — the owner
    errand is pending) | ``unavailable`` (token present, read failed).
    """
    out: dict[str, Any] = {
        "state": "ok",
        "reason": "",
        "token_set": bool(config.RAILWAY_TOKEN),
        "services": [],
        "fetched_at": "",
        "cached": False,
    }
    if not config.RAILWAY_TOKEN:
        out["state"] = "not-configured"
        out["reason"] = (
            "RAILWAY_TOKEN is not set on this service — live Railway data "
            "unavailable; owner errand pending (mint a project-scoped token "
            "for superbot-websites per "
            "docs/planning/live-env-visibility-plan-2026-07-11.md)"
        )
        return out

    now = time.monotonic()
    if not refresh:
        hit = _cache.get(_CACHE_KEY)
        if hit and hit[0] > now:
            cached = dict(hit[1])
            cached["cached"] = True
            return cached

    # 1. The token tells us which project/environment it is scoped to.
    scope = await _graphql("query { projectToken { projectId environmentId } }")
    token_info = (scope.get("data") or {}).get("projectToken") if scope["ok"] else None
    if not (scope["ok"] and isinstance(token_info, dict)):
        out["state"] = "unavailable"
        out["reason"] = scope.get("error") or "projectToken query returned no scope"
        return out
    project_id = token_info.get("projectId", "")
    environment_id = token_info.get("environmentId", "")

    # 2. The project's services.
    proj = await _graphql(
        "query ($id: String!) { project(id: $id) "
        "{ name services { edges { node { id name } } } } }",
        {"id": project_id},
    )
    project = (proj.get("data") or {}).get("project") if proj["ok"] else None
    if not (proj["ok"] and isinstance(project, dict)):
        out["state"] = "unavailable"
        out["reason"] = proj.get("error") or "project query returned no project"
        return out
    nodes = [
        e.get("node", {})
        for e in (project.get("services", {}) or {}).get("edges", []) or []
        if isinstance(e, dict)
    ]

    # 3. Variable NAMES per service (values dropped in _names_only).
    async def one(node: dict) -> dict[str, Any]:
        res = await _graphql(
            "query ($projectId: String!, $environmentId: String!, $serviceId: String!) "
            "{ variables(projectId: $projectId, environmentId: $environmentId, "
            "serviceId: $serviceId) }",
            {
                "projectId": project_id,
                "environmentId": environment_id,
                "serviceId": node.get("id", ""),
            },
        )
        names = _names_only((res.get("data") or {}).get("variables"))
        return {
            "name": node.get("name", "?"),
            "variable_names": names,
            "count": len(names),
            "error": None if res["ok"] else (res.get("error") or "fetch failed"),
        }

    out["services"] = sorted(
        await asyncio.gather(*[one(n) for n in nodes]),
        key=lambda s: s["name"],
    )
    out["project_name"] = project.get("name", PROJECT_NAME)
    out["fetched_at"] = time.strftime("%H:%M:%S UTC", time.gmtime())
    async with _cache_lock:
        _cache[_CACHE_KEY] = (now + config.CACHE_TTL_SECONDS, out)
    return out


def _committed_services() -> list[dict[str, Any]]:
    """The SERVICES facts, with the control-plane's own env presence added.

    Presence only (set/unset), read from THIS process's environment at
    request time — never a value. Other services' runtime state is unknowable
    without the live Railway read and is honestly marked so.
    """
    out: list[dict[str, Any]] = []
    for svc in SERVICES:
        entry = {
            **svc,
            "env_vars": [
                {
                    **var,
                    # True/False for this very process; None = unknowable
                    # here (needs the live Railway read).
                    "set_here": bool(os.environ.get(var["name"]))
                    if svc["self"]
                    else None,
                }
                for var in svc["env_vars"]
            ],
        }
        out.append(entry)
    return out


async def overview(refresh: bool = False) -> dict[str, Any]:
    """Everything /owner/environments renders: committed facts + live half."""
    return {
        "services": _committed_services(),
        "live": await live_overview(refresh=refresh),
        "project_name": PROJECT_NAME,
        "project_url": PROJECT_URL,
        "plan_doc": "docs/planning/live-env-visibility-plan-2026-07-11.md",
    }
