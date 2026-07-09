"""Public data layer for the bot site.

The site is **decoupled** from the bot exactly as superbot's ``botsite/`` is: it
reads only the committed public subset ``botsite/data/site.json`` from the superbot
repo — fetched live over **raw.githubusercontent.com** (no token, public file) — and
**never** imports any bot code. That subset is redaction-by-construction (a top-level
whitelist: ``meta``/``counts``/``catalogue``/``commands``/``bot_changelog``), so
dev-only families (env, settings, access, ideas, raw bugs) physically cannot appear.

Core inherited principle: **never fake data.** If the feed can't be fetched, pages
render an honest "data temporarily unavailable" lane — not stale invented content.

This module is pure-Python and holds **no secret**. The one env knob is
``SITE_JSON_URL`` (defaults to superbot@main), so a fork/branch can be pointed at a
different committed export without a code change.
"""

from __future__ import annotations

import os
import time
from typing import Any, Optional

import httpx

# The committed public subset in the superbot repo. Overridable for testing / forks.
SITE_JSON_URL = os.environ.get(
    "SITE_JSON_URL",
    "https://raw.githubusercontent.com/menno420/superbot/main/botsite/data/site.json",
)
# The bot's public install link (Discord "Add App" OAuth URL). Single-sourced here.
ADD_TO_DISCORD_URL = os.environ.get(
    "ADD_TO_DISCORD_URL",
    "https://discord.com/oauth2/authorize?client_id=1403818430758654132",
)
CACHE_TTL_SECONDS = int(os.environ.get("SITE_CACHE_TTL_SECONDS", "180"))

# ---------------------------------------------------------------------------
# Live fetch with a small in-memory TTL cache (mirrors the control-plane's model:
# cache successes; never poison the cache with a transient failure).
# ---------------------------------------------------------------------------
_client: Optional[httpx.AsyncClient] = None
_cache: dict[str, Any] = {}  # {"expires": float, "result": dict}


def make_client() -> httpx.AsyncClient:
    # No Authorization header: raw.githubusercontent.com serves public repos
    # anonymously; a bad/foreign bearer makes it 404 (verified in the control-plane).
    return httpx.AsyncClient(
        headers={"User-Agent": "superbot-botsite"},
        timeout=20.0,
        trust_env=True,
    )


def set_client(client: httpx.AsyncClient) -> None:
    global _client
    _client = client


def _get_client() -> httpx.AsyncClient:
    assert _client is not None, "client not initialised (app lifespan)"
    return _client


async def fetch_site(refresh: bool = False) -> dict[str, Any]:
    """Fetch ``site.json`` and return an honest result envelope.

    ``{"ok", "data", "error", "fetched_at", "cached", "url"}`` — templates render
    partial failure honestly instead of 500ing, matching the control-plane's
    degrade-per-cell posture.
    """
    now = time.monotonic()
    if not refresh:
        hit = _cache.get(SITE_JSON_URL)
        if hit and hit["expires"] > now:
            out = dict(hit["result"])
            out["cached"] = True
            return out
    try:
        resp = await _get_client().get(SITE_JSON_URL)
        if resp.status_code == 200:
            data = resp.json()
            result = {
                "ok": True,
                "data": data,
                "error": "",
                "fetched_at": time.strftime("%H:%M:%S UTC", time.gmtime()),
                "cached": False,
                "url": SITE_JSON_URL,
            }
        else:
            result = {
                "ok": False,
                "data": {},
                "error": f"HTTP {resp.status_code} fetching site.json",
                "fetched_at": time.strftime("%H:%M:%S UTC", time.gmtime()),
                "cached": False,
                "url": SITE_JSON_URL,
            }
    except Exception as exc:  # never 500 the public site on a data hiccup
        result = {
            "ok": False,
            "data": {},
            "error": f"{type(exc).__name__}: {exc}",
            "fetched_at": time.strftime("%H:%M:%S UTC", time.gmtime()),
            "cached": False,
            "url": SITE_JSON_URL,
        }
    # Cache only successes: a transient error must not blank the site for a full TTL.
    if result["ok"]:
        _cache[SITE_JSON_URL] = {"expires": now + CACHE_TTL_SECONDS, "result": result}
    return result


def prime_cache(data: dict[str, Any]) -> None:
    """Seed the cache directly (used by tests to avoid the network)."""
    _cache[SITE_JSON_URL] = {
        "expires": time.monotonic() + CACHE_TTL_SECONDS,
        "result": {
            "ok": True,
            "data": data,
            "error": "",
            "fetched_at": "test",
            "cached": False,
            "url": SITE_JSON_URL,
        },
    }


def clear_cache() -> None:
    _cache.clear()


# ---------------------------------------------------------------------------
# Editorial metadata per command category. Every category present in the feed
# resolves; an unknown future category folds into a neutral default rather than
# breaking (same "never crash on new data" rule as superbot's site_data.py).
# Colors are ds semantic accent tokens; icons are ds icon names.
# ---------------------------------------------------------------------------
_CATEGORY_META: dict[str, dict[str, str]] = {
    "admin": {"label": "Administration", "color": "var(--sb-indigo)", "icon": "shield"},
    "moderation": {"label": "Moderation", "color": "var(--sb-rose)", "icon": "shield"},
    "community": {"label": "Community", "color": "var(--sb-pink)", "icon": "comment"},
    "economy": {"label": "Economy", "color": "var(--sb-amber)", "icon": "coins"},
    "utility": {"label": "Utility", "color": "var(--sb-sky)", "icon": "layers"},
    "progression": {"label": "Progression", "color": "var(--sb-sky)", "icon": "chart"},
    "management": {"label": "Management", "color": "var(--sb-indigo)", "icon": "layers"},
    "games": {"label": "Games", "color": "var(--sb-brand)", "icon": "gamepad"},
}
# The order categories appear across the site (present ones only, in this order).
_CATEGORY_ORDER = [
    "community",
    "economy",
    "progression",
    "games",
    "utility",
    "moderation",
    "admin",
    "management",
]

_PERMS = {
    "user": "Anyone",
    "": "Anyone",
    "moderator": "Moderators",
    "staff": "Staff",
    "administrator": "Admins",
}

_STATUS = {"finished": "stable", "in-progress": "in progress"}


def category_meta(cat: str) -> dict[str, str]:
    return _CATEGORY_META.get(
        cat,
        {"label": (cat or "other").replace("_", " ").title(), "color": "var(--sb-sky)", "icon": "layers"},
    )


def _norm(s: Any) -> str:
    return " ".join(str(s or "").split())


# ---------------------------------------------------------------------------
# Shaping helpers — pure functions over the loaded site.json dict.
# ---------------------------------------------------------------------------
def build_meta(site: dict[str, Any]) -> dict[str, Any]:
    return (site.get("meta", {}) or {}).get("build", {}) or {}


def counts(site: dict[str, Any]) -> dict[str, int]:
    c = site.get("counts", {}) or {}
    return {
        "commands": int(c.get("commands", 0) or 0),
        "features": int(c.get("features", 0) or 0),
        "games": int(c.get("games", 0) or 0),
    }


def features(site: dict[str, Any]) -> list[dict[str, Any]]:
    """The full public catalogue — one entry per subsystem (43)."""
    out: list[dict[str, Any]] = []
    for c in site.get("catalogue", []) or []:
        key = c.get("key")
        if not key:
            continue
        cat = c.get("category") or "other"
        meta = category_meta(cat)
        out.append(
            {
                "key": key,
                "name": c.get("display_name") or key.replace("_", " ").title(),
                "emoji": c.get("emoji") or "",
                "category": cat,
                "category_label": meta["label"],
                "color": meta["color"],
                "icon": meta["icon"],
                "description": _norm(c.get("description")),
                "tags": list(c.get("tags") or []),
                "is_game": bool(c.get("is_game")),
            }
        )
    return out


def feature_by_key(site: dict[str, Any], key: str) -> Optional[dict[str, Any]]:
    for f in features(site):
        if f["key"] == key:
            return f
    return None


def games(site: dict[str, Any]) -> list[dict[str, Any]]:
    return [f for f in features(site) if f["is_game"]]


def commands(site: dict[str, Any]) -> list[dict[str, Any]]:
    """Deduped-by-name, sorted command list shaped for the reference pages."""
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for c in sorted(site.get("commands", []) or [], key=lambda x: x.get("name") or ""):
        name = c.get("name")
        if not name or name in seen:
            continue
        seen.add(name)
        cat = c.get("category") or "other"
        meta = category_meta(cat)
        summary = _norm(c.get("usage") or c.get("description")) or f"The {name} command."
        out.append(
            {
                "name": name,
                "usage": f"!{name}",
                "category": cat,
                "category_label": meta["label"],
                "color": meta["color"],
                "aliases": list(c.get("aliases") or []),
                "permissions": _PERMS.get(str(c.get("permissions") or ""), str(c.get("permissions"))),
                "summary": summary[:160],
                "description": _norm(c.get("description") or c.get("usage")) or summary,
                "examples": list(c.get("examples") or []),
                "status": _STATUS.get(str(c.get("status") or ""), str(c.get("status") or "")),
                "linked_ideas": [
                    {"title": _norm(li.get("title"))[:80]}
                    for li in (c.get("linked_ideas") or [])
                ][:4],
            }
        )
    return out


def present_categories(site: dict[str, Any]) -> list[dict[str, Any]]:
    """Categories that actually appear, in editorial order, with feature+command counts."""
    feats = features(site)
    cmds = commands(site)
    present = {f["category"] for f in feats}
    ordered = [c for c in _CATEGORY_ORDER if c in present]
    ordered += sorted(present - set(_CATEGORY_ORDER))
    result = []
    for cat in ordered:
        meta = category_meta(cat)
        result.append(
            {
                "id": cat,
                "label": meta["label"],
                "color": meta["color"],
                "icon": meta["icon"],
                "feature_count": sum(1 for f in feats if f["category"] == cat),
                "command_count": sum(1 for c in cmds if c["category"] == cat),
            }
        )
    return result


_CHANGE_KIND = {"feature": "added", "improvement": "improved", "fix": "fixed"}


def changelog(site: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    build = build_meta(site)
    for e in site.get("bot_changelog", []) or []:
        iso = e.get("date") or ""
        out.append(
            {
                "date": iso,
                "version": iso.replace("-", ".") if iso else "",
                "build": str(build.get("commit") or ""),
                "title": e.get("title") or "Update",
                "kind": _CHANGE_KIND.get(str(e.get("kind") or "").lower(), "improved"),
                "summary": _norm(e.get("summary") or e.get("title")),
            }
        )
    return out


def systems(site: dict[str, Any]) -> list[dict[str, Any]]:
    """Honest status rows: derived from real areas, stated 'as of last deploy'.

    No fabricated incident history or per-second uptime — the row set mirrors the
    real subsystem areas + core infra, all reported operational as of the build.
    """
    rows = [{"name": "Core gateway", "desc": "Command routing & Discord connection", "color": "var(--sb-ok)"}]
    for c in present_categories(site):
        rows.append({"name": c["label"], "desc": f"{c['command_count']} commands", "color": c["color"]})
    rows.append({"name": "Database", "desc": "Persistence for XP, economy, tags & settings", "color": "var(--sb-ok)"})
    return rows


def palette_items(site: dict[str, Any]) -> list[dict[str, str]]:
    """Command-palette index: pages + features + games + commands."""
    items: list[dict[str, str]] = [
        {"group": "Pages", "label": "Home", "href": "/"},
        {"group": "Pages", "label": "Features", "href": "/features"},
        {"group": "Pages", "label": "Commands", "href": "/commands"},
        {"group": "Pages", "label": "Games", "href": "/games"},
        {"group": "Pages", "label": "Changelog", "href": "/changelog"},
        {"group": "Pages", "label": "Status", "href": "/status"},
    ]
    for f in features(site):
        if not f["is_game"]:
            items.append(
                {"group": "Features", "label": f["name"], "sub": f["category_label"], "href": f"/features/{f['key']}"}
            )
    for g in games(site):
        items.append({"group": "Games", "label": g["name"], "href": "/games"})
    for c in commands(site):
        items.append(
            {"group": "Commands", "label": c["summary"], "code": c["usage"], "sub": c["category_label"], "href": "/commands"}
        )
    return items
