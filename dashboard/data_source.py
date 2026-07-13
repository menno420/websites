"""Data layer for the developer dashboard.

The dashboard is **decoupled** from the bot exactly as superbot's ``dashboard/`` is: it
reads only the committed generated artifacts from the superbot repo — fetched live over
**raw.githubusercontent.com** (no token, public files) — and **never** imports any bot
code.

Two feeds:

* ``dashboard.json`` — the full read-only oversight payload (subsystem catalogue, cogs +
  commands, settings, access ladder, env-var usage map, ideas, bugs, updates, synonyms).
  Produced by superbot's ``scripts/export_dashboard_data.py`` (pure stdlib static scan).
* ``console.json`` — the owner's one-glance program console (sessions, ideas, bugs,
  changelog). A small complementary feed.

Core inherited principle: **never fake data.** If a feed can't be fetched, pages render
an honest "data temporarily unavailable" banner and only what the feed provides — not
stale invented content. ``?refresh=1`` on any page busts the cache.

This module is pure-Python and holds **no secret**. The env knobs are just the feed URLs
(defaulting to superbot@main), so a fork/branch can point at a different committed export
without a code change.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Optional

import httpx

# The committed artifacts in the superbot repo. Overridable for testing / forks.
DASHBOARD_JSON_URL = os.environ.get(
    "DASHBOARD_JSON_URL",
    "https://raw.githubusercontent.com/menno420/superbot/main/dashboard/data/dashboard.json",
)
CONSOLE_JSON_URL = os.environ.get(
    "CONSOLE_JSON_URL",
    "https://raw.githubusercontent.com/menno420/superbot/main/botsite/data/console.json",
)
def _env_int(name: str, default: int) -> int:
    """Parse an integer env var, falling back to ``default``.

    Unset, empty-string and malformed values ALL fall back. On Railway an
    empty entry is NOT "unset" — a bare module-level ``int("")`` would crash
    the whole service at import (docs/CAPABILITIES.md, 2026-07-13 ORDER 026
    finding). Local by design: services share code by convention, never by
    cross-service import.
    """
    try:
        return int(os.environ.get(name) or default)
    except ValueError:
        return default


CACHE_TTL_SECONDS = _env_int("DATA_CACHE_TTL_SECONDS", 180)

# Link back to the bot repo for "view source" affordances (env map locations, etc.).
SUPERBOT_REPO = os.environ.get("SUPERBOT_REPO", "menno420/superbot")
SUPERBOT_REF = os.environ.get("SUPERBOT_REF", "main")

# ---------------------------------------------------------------------------
# Live fetch with a small in-memory TTL cache (mirrors the control-plane's model:
# cache successes; never poison the cache with a transient failure).
# ---------------------------------------------------------------------------
_client: Optional[httpx.AsyncClient] = None
_cache: dict[str, Any] = {}  # {url: {"expires": float, "result": dict}}


def make_client() -> httpx.AsyncClient:
    # No Authorization header: raw.githubusercontent.com serves public repos
    # anonymously; a bad/foreign bearer makes it 404 (verified in the control-plane).
    return httpx.AsyncClient(
        headers={"User-Agent": "superbot-dashboard"},
        timeout=20.0,
        trust_env=True,
    )


def set_client(client: httpx.AsyncClient) -> None:
    global _client
    _client = client


def _get_client() -> httpx.AsyncClient:
    assert _client is not None, "client not initialised (app lifespan)"
    return _client


async def _fetch(url: str, refresh: bool = False) -> dict[str, Any]:
    """Fetch a JSON feed and return an honest result envelope.

    ``{"ok", "data", "error", "fetched_at", "cached", "url"}`` — templates render
    partial failure honestly instead of 500ing, matching the control-plane's
    degrade posture.
    """
    now = time.monotonic()
    if not refresh:
        hit = _cache.get(url)
        if hit and hit["expires"] > now:
            out = dict(hit["result"])
            out["cached"] = True
            return out
    stamp = time.strftime("%H:%M:%S UTC", time.gmtime())
    try:
        resp = await _get_client().get(url)
        if resp.status_code == 200:
            result = {
                "ok": True,
                "data": resp.json(),
                "error": "",
                "fetched_at": stamp,
                "cached": False,
                "url": url,
            }
        else:
            result = {
                "ok": False,
                "data": {},
                "error": f"HTTP {resp.status_code} fetching {url.rsplit('/', 1)[-1]}",
                "fetched_at": stamp,
                "cached": False,
                "url": url,
            }
    except Exception as exc:  # never 500 on a data hiccup
        result = {
            "ok": False,
            "data": {},
            "error": f"{type(exc).__name__}: {exc}",
            "fetched_at": stamp,
            "cached": False,
            "url": url,
        }
    # Cache only successes: a transient error must not blank the site for a full TTL.
    if result["ok"]:
        _cache[url] = {"expires": now + CACHE_TTL_SECONDS, "result": result}
    return result


async def fetch_dashboard(refresh: bool = False) -> dict[str, Any]:
    return await _fetch(DASHBOARD_JSON_URL, refresh=refresh)


async def fetch_console(refresh: bool = False) -> dict[str, Any]:
    return await _fetch(CONSOLE_JSON_URL, refresh=refresh)


# ---------------------------------------------------------------------------
# console.json shape contract (cross-repo pin).
#
# The console feed's shape is a CONTRACT between two repos: superbot produces the
# committed botsite/data/console.json and pins its shape in a committed, versioned
# botsite/data/console_data_contract.json (superbot PR #1884; producer parity +
# fail-closed checks run in superbot's CI). This service is the second consumer, so
# it pins the version it was built against (dashboard/console_data_contract.json —
# a copy of contract v1) and verifies the fetched feed at render time: version
# match + every contracted top-level family present. A mismatch renders an honest
# schema-drift banner on /console (never-fake-data posture) instead of a silently
# wrong/blank page — a producer-side rename becomes visible the moment it lands.
# ---------------------------------------------------------------------------
CONSOLE_CONTRACT_FILE = Path(__file__).resolve().parent / "console_data_contract.json"


def load_console_contract() -> dict[str, Any]:
    """The pinned copy of the console.json shape contract this consumer expects."""
    return json.loads(CONSOLE_CONTRACT_FILE.read_text(encoding="utf-8"))


def console_contract_issue(data: dict[str, Any]) -> str:
    """Human-readable schema-drift message for a fetched console feed ('' = ok).

    Checks the two cheap, load-bearing promises: ``meta.schema_version`` equals
    the pinned contract ``version``, and every contracted top-level family is
    present. Field-level enforcement lives producer-side in superbot's CI; this
    render-time check exists to make a cross-repo drift *visible* on the page.
    """
    try:
        contract = load_console_contract()
    except (OSError, json.JSONDecodeError) as exc:  # pragma: no cover - repo file
        return f"pinned console contract unreadable ({exc})"
    meta = data.get("meta") if isinstance(data.get("meta"), dict) else {}
    version = meta.get("schema_version")
    pinned = contract.get("version")
    if version != pinned:
        return (
            f"feed schema_version={version!r} but this dashboard was built against "
            f"contract v{pinned} — the shape may have changed upstream"
        )
    missing = [k for k in contract.get("top_level", []) if k not in data]
    if missing:
        return (
            f"feed is missing contracted famil{'y' if len(missing) == 1 else 'ies'} "
            f"{', '.join(missing)} — parts of this page may render empty"
        )
    return ""


# ---------------------------------------------------------------------------
# dashboard.json schema version pin (cross-repo).
#
# The main feed's producer (superbot's ``scripts/export_dashboard_data.py``) stamps
# ``meta.schema_version`` into every committed ``dashboard/data/dashboard.json``
# (the live feed ships the integer 1). Until now only console.json was checked at
# render time; the main feed was consumed unverified. This pin closes that gap:
# a fetched feed whose version doesn't match what this consumer was built against
# renders an honest schema-drift banner on every page (never-fake-data posture)
# instead of silently misrendering. Read-only, forward-only — no producer change.
# ---------------------------------------------------------------------------
DASHBOARD_SCHEMA_VERSION = 1


def dashboard_schema_issue(data: dict[str, Any]) -> str:
    """Human-readable schema-drift message for a fetched dashboard feed ('' = ok).

    Accepts the pinned version whether the producer ships it as an int (``1``,
    the value observed live) or a numeric string (``"1"``). Anything else —
    missing, non-numeric, newer, older — degrades to an explicit message; this
    function never raises on feed content.
    """
    meta = data.get("meta") if isinstance(data.get("meta"), dict) else {}
    version = meta.get("schema_version")
    if version is None:
        return (
            "feed carries no meta.schema_version — cannot confirm the shape; this "
            f"dashboard was built against schema v{DASHBOARD_SCHEMA_VERSION}"
        )
    try:
        numeric = int(str(version).strip())
    except (TypeError, ValueError):
        return (
            f"feed schema_version={version!r} is not a version this dashboard "
            f"understands — built against schema v{DASHBOARD_SCHEMA_VERSION}"
        )
    if numeric > DASHBOARD_SCHEMA_VERSION:
        return (
            f"feed schema_version={version!r} — data schema newer than this consumer "
            f"(built against v{DASHBOARD_SCHEMA_VERSION}); the shape may have changed upstream"
        )
    if numeric < DASHBOARD_SCHEMA_VERSION:
        return (
            f"feed schema_version={version!r} — data schema older than this consumer "
            f"(built against v{DASHBOARD_SCHEMA_VERSION})"
        )
    return ""


def prime_cache(url: str, data: dict[str, Any]) -> None:
    """Seed the cache directly (used by tests to avoid the network)."""
    _cache[url] = {
        "expires": time.monotonic() + CACHE_TTL_SECONDS,
        "result": {
            "ok": True,
            "data": data,
            "error": "",
            "fetched_at": "test",
            "cached": False,
            "url": url,
        },
    }


def clear_cache() -> None:
    _cache.clear()


# ---------------------------------------------------------------------------
# Editorial metadata per subsystem category (ds semantic accent tokens + icons).
# Every category present in the feed resolves; an unknown future category folds
# into a neutral default rather than breaking.
# ---------------------------------------------------------------------------
_CATEGORY_META: dict[str, dict[str, str]] = {
    "admin": {"label": "Administration", "color": "var(--sb-indigo)", "icon": "shield"},
    "moderation": {"label": "Moderation", "color": "var(--sb-rose)", "icon": "shield"},
    "community": {"label": "Community", "color": "var(--sb-pink)", "icon": "comment"},
    "economy": {"label": "Economy", "color": "var(--sb-amber)", "icon": "coins"},
    "utility": {"label": "Utility", "color": "var(--sb-sky)", "icon": "layers"},
    "progression": {"label": "Progression", "color": "var(--sb-sky)", "icon": "chart"},
    "management": {"label": "Management", "color": "var(--sb-indigo)", "icon": "layers"},
    "diagnostic": {"label": "Diagnostics", "color": "var(--sb-sky)", "icon": "activity"},
    "games": {"label": "Games", "color": "var(--sb-brand)", "icon": "gamepad"},
    "other": {"label": "Other", "color": "var(--sb-sky)", "icon": "layers"},
}
_CATEGORY_ORDER = [
    "community",
    "economy",
    "progression",
    "games",
    "utility",
    "moderation",
    "admin",
    "management",
    "diagnostic",
]


def category_meta(cat: str) -> dict[str, str]:
    return _CATEGORY_META.get(
        cat,
        {
            "label": (cat or "other").replace("_", " ").title(),
            "color": "var(--sb-sky)",
            "icon": "layers",
        },
    )


def _norm(s: Any) -> str:
    return " ".join(str(s or "").split())


# ---------------------------------------------------------------------------
# Shaping helpers — pure functions over the loaded dashboard.json dict. Kept small
# and defensive: missing keys degrade to empty, never raise.
# ---------------------------------------------------------------------------
def meta(data: dict[str, Any]) -> dict[str, Any]:
    return data.get("meta", {}) or {}


def counts(data: dict[str, Any]) -> dict[str, int]:
    return dict(meta(data).get("counts", {}) or {})


def build(data: dict[str, Any]) -> dict[str, Any]:
    return meta(data).get("build", {}) or {}


def catalogue(data: dict[str, Any]) -> list[dict[str, Any]]:
    return list(data.get("catalogue", []) or [])


def catalogue_by_category(data: dict[str, Any]) -> list[tuple[str, dict[str, str], list[dict[str, Any]]]]:
    """Subsystems grouped by category, in editorial order, with category meta."""
    grouped: dict[str, list[dict[str, Any]]] = {}
    for entry in catalogue(data):
        grouped.setdefault(entry.get("category") or "other", []).append(entry)
    ordered = [c for c in _CATEGORY_ORDER if c in grouped]
    ordered += sorted(k for k in grouped if k not in _CATEGORY_ORDER)
    return [(cat, category_meta(cat), grouped[cat]) for cat in ordered]


def all_commands(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Flattened command list across every cog, each tagged with its cog + subsystem."""
    out: list[dict[str, Any]] = []
    for cog in data.get("cogs", []) or []:
        for cmd in cog.get("commands", []) or []:
            item = dict(cmd)
            item["cog"] = cog.get("cog") or ""
            item["subsystem"] = cog.get("subsystem") or ""
            item["file"] = cog.get("file") or ""
            out.append(item)
    return out


def command_names(data: dict[str, Any]) -> list[str]:
    return sorted({c["name"] for c in all_commands(data) if c.get("name")})


def cogs(data: dict[str, Any]) -> list[dict[str, Any]]:
    return list(data.get("cogs", []) or [])


def command_stats(data: dict[str, Any]) -> dict[str, int]:
    cmds = all_commands(data)
    return {
        "total": len(cmds),
        "top_prefix": sum(1 for c in cmds if c.get("type") in ("prefix", "both") and not c.get("parent")),
        "subcommands": sum(1 for c in cmds if c.get("parent")),
        "slash": sum(1 for c in cmds if c.get("type") == "slash" and not c.get("parent")),
        "button": sum(1 for c in cmds if c.get("button_backed")),
        "cogs": sum(1 for cog in cogs(data) if cog.get("is_cog")),
    }


def build_taken_map(data: dict[str, Any]) -> dict[str, str]:
    """Every token already in use -> a human label of what owns it.

    Synonyms first, then aliases, then command names last so the strongest owner
    (a real command) wins a tie. Powers the alias collision-checker.
    """
    taken: dict[str, str] = {}
    for syn in data.get("synonyms", []) or []:
        for token in syn.get("synonyms", []) or []:
            taken[str(token).lower()] = f"synonym of !{syn.get('canonical')}"
    for cmd in all_commands(data):
        for token in cmd.get("aliases") or []:
            taken[str(token).lower()] = f"alias of !{cmd.get('name')}"
    for name in command_names(data):
        taken[name.lower()] = "a command"
    return taken


def ideas(data: dict[str, Any]) -> list[dict[str, Any]]:
    return list(data.get("ideas", []) or [])


def bugs(data: dict[str, Any]) -> list[dict[str, Any]]:
    return list(data.get("bugs", []) or [])


def open_bugs(data: dict[str, Any]) -> list[dict[str, Any]]:
    return [b for b in bugs(data) if (b.get("status") or "").upper() == "OPEN"]


def updates(data: dict[str, Any]) -> list[dict[str, Any]]:
    return list(data.get("updates", []) or [])


def settings(data: dict[str, Any]) -> list[dict[str, Any]]:
    return list(data.get("settings", []) or [])


def env_usage(data: dict[str, Any]) -> list[dict[str, Any]]:
    return list(data.get("env_usage", []) or [])


def synonyms(data: dict[str, Any]) -> list[dict[str, Any]]:
    return list(data.get("synonyms", []) or [])


def access(data: dict[str, Any]) -> dict[str, Any]:
    return dict(data.get("access", {}) or {})


def bot_changelog(data: dict[str, Any]) -> list[dict[str, Any]]:
    return list(data.get("bot_changelog", []) or [])


def source_url(path: str, line: int | None = None) -> str:
    """GitHub blob URL for a bot-source path (env-map "view source" links)."""
    base = f"https://github.com/{SUPERBOT_REPO}/blob/{SUPERBOT_REF}/{path}"
    return f"{base}#L{line}" if line else base
