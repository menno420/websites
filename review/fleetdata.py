"""Fleet + stats domain layer for the review service — committed mirrors only.

Runtime-network-free, same as ``story.py``: the two data sources are the
committed ``data/fleet.json`` (registry + heartbeat mirror, baked by
``gen_fleet.py``) and ``data/stats.json`` (per-repo REST numbers, baked by
``gen_stats.py`` — absent until the scheduled bake's first successful run).
Every loader degrades honestly (missing/corrupt file → banner text, never
invented lanes or numbers), and every age-measuring function takes an
injectable ``now=`` (the repo's clock-freeze discipline — the 08:45Z
time-bomb lesson, PR #111/#114).

Fleet size is NEVER hardcoded here: the pages render the registry's own
counts (total seats vs repo-backed seats vs registry-only seats) as baked.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

BASE_DIR = Path(__file__).resolve().parent
FLEET_PATH = BASE_DIR / "data" / "fleet.json"
STATS_PATH = BASE_DIR / "data" / "stats.json"

# The bake is scheduled daily (best-effort cron, ±hours — the capability
# ledger's standing finding). A mirror older than this banners as stale.
STALE_HOURS = 48

_ISO_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2})(?::(\d{2}))?")


# ---------------------------------------------------------------------------
# Loading — honest degradation (mirrors story.load_snapshot).
# ---------------------------------------------------------------------------
def load_fleet(path: Path | None = None) -> dict[str, Any]:
    """``{ok, error, data}`` for the committed fleet mirror."""
    if path is None:
        path = FLEET_PATH
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"ok": False, "error": "fleet mirror missing (data/fleet.json)", "data": {}}
    except (json.JSONDecodeError, OSError) as exc:
        return {"ok": False, "error": f"fleet mirror unreadable: {exc}", "data": {}}
    if not isinstance(data, dict) or "lanes" not in data or "registry" not in data:
        return {"ok": False, "error": "fleet mirror malformed (missing lanes/registry)", "data": {}}
    return {"ok": True, "error": "", "data": data}


def load_stats(path: Path | None = None) -> dict[str, Any]:
    """``{ok, error, data}`` for the committed stats mirror. Absence is the
    NORMAL state until the scheduled bake's first successful run — the error
    text says so rather than alarming."""
    if path is None:
        path = STATS_PATH
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {
            "ok": False,
            "error": "no stats mirrored yet — the scheduled bake (review-bake workflow) commits data/stats.json on its first successful run",
            "data": {},
        }
    except (json.JSONDecodeError, OSError) as exc:
        return {"ok": False, "error": f"stats mirror unreadable: {exc}", "data": {}}
    if not isinstance(data, dict) or "repos" not in data:
        return {"ok": False, "error": "stats mirror malformed (missing repos)", "data": {}}
    return {"ok": True, "error": "", "data": data}


# ---------------------------------------------------------------------------
# Time — injectable clock, honest unknowns.
# ---------------------------------------------------------------------------
def parse_iso(ts: str) -> Optional[datetime]:
    """Best-effort UTC parse of the fleet's ISO-ish stamps; None if unparseable."""
    m = _ISO_RE.search(ts or "")
    if not m:
        return None
    y, mo, d, h, mi, se = m.groups()
    try:
        return datetime(int(y), int(mo), int(d), int(h), int(mi), int(se or 0), tzinfo=timezone.utc)
    except ValueError:
        return None


def _human_age(hours: float) -> str:
    if hours < 0:
        return "just now"
    if hours < 1:
        return f"{int(hours * 60)}m ago"
    if hours < 48:
        return f"{int(hours)}h ago"
    return f"{int(hours / 24)}d ago"


def freshness(
    ts: str, *, now: Optional[datetime] = None, stale_hours: float = STALE_HOURS
) -> dict[str, Any]:
    """``{ok, iso, age_hours, age_human, stale}`` for any timestamp string.

    Unparseable → ``ok=False`` / "age unknown" (never faked fresh). ``now``
    is injectable so tests with fixed stamps stay deterministic.
    """
    if now is None:
        now = datetime.now(timezone.utc)
    dt = parse_iso(ts)
    if dt is None:
        return {"ok": False, "iso": (ts or "").strip(), "age_hours": None,
                "age_human": "age unknown", "stale": False}
    age_hours = (now - dt).total_seconds() / 3600
    return {
        "ok": True,
        "iso": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "age_hours": age_hours,
        "age_human": _human_age(age_hours),
        "stale": age_hours >= stale_hours,
    }


# ---------------------------------------------------------------------------
# Heartbeat-field readers (parsed at render time from the mirrored verbatim
# fields — unit-testable pure functions).
# ---------------------------------------------------------------------------
_ID_RANGE_RE = re.compile(r"^(\d+)\s*[-–]\s*(\d+)$")
_MAX_ID_RANGE = 500


def _expand_ids(spec: str) -> list[str]:
    """``001-004,006`` → ``['001','002','003','004','006']`` (typo-guarded)."""
    out: list[str] = []
    seen: set[str] = set()
    for part in (spec or "").split(","):
        part = part.strip()
        if not part:
            continue
        m = _ID_RANGE_RE.match(part)
        if m:
            lo_s, hi_s = m.group(1), m.group(2)
            lo, hi = int(lo_s), int(hi_s)
            if lo <= hi and hi - lo <= _MAX_ID_RANGE:
                for i in range(lo, hi + 1):
                    tok = str(i).zfill(len(lo_s))
                    if tok not in seen:
                        seen.add(tok)
                        out.append(tok)
            continue
        if part.isdigit() and part not in seen:
            seen.add(part)
            out.append(part)
    return out


def orders_summary(value: str) -> dict[str, Any]:
    """``acked=001-011 done=001-009`` → counts + outstanding ids. ``ok=False``
    when nothing parsed (free-text orders line) — render the raw value only."""
    v = value or ""

    def ids_of(key: str) -> list[str]:
        m = re.search(rf"{key}\s*=\s*([0-9,\s–-]+)", v)
        return _expand_ids(m.group(1).strip()) if m else []

    acked = ids_of("acked")
    done = ids_of("done")
    done_set = set(done)
    outstanding = [i for i in acked if i not in done_set]
    return {
        "ok": bool(acked or done),
        "acked": len(acked),
        "done": len(done),
        "outstanding": outstanding,
    }


_KIT_VERSION_RE = re.compile(r"\bv\d+(?:\.\d+)*\b")


def kit_version(value: str) -> str:
    """The version token out of a ``kit:`` line; ``""`` when absent."""
    m = _KIT_VERSION_RE.search(value or "")
    return m.group(0) if m else ""


def health_kind(value: str) -> str:
    """``green`` / ``red-by-design`` / ``broken`` / ``unknown`` (same reading
    the control-plane fleet page uses)."""
    h = (value or "").strip().lower()
    if h.startswith("green"):
        return "green"
    if h.startswith("red-by-design") or h.startswith("red by design"):
        return "red-by-design"
    if h.startswith("broken") or h.startswith("red"):
        return "broken"
    return "unknown"


# ---------------------------------------------------------------------------
# Page-facing views
# ---------------------------------------------------------------------------
def lane_view(
    lane: dict[str, Any],
    stats_repos: dict[str, Any],
    *,
    now: Optional[datetime] = None,
) -> dict[str, Any]:
    """One lane's merged view: registry entry + parsed heartbeat + stats."""
    repo = lane.get("repo")
    hb = lane.get("heartbeat") or {}
    fields = hb.get("fields") or {}
    view: dict[str, Any] = {
        "lane": lane.get("lane", "?"),
        "repo": repo,
        "slug": repo or "",
        "disposition": lane.get("disposition", ""),
        "repo_url": lane.get("repo_url", ""),
        "heartbeat_available": bool(hb.get("available")),
        "heartbeat_reason": hb.get("reason", ""),
        "heartbeat_source_url": hb.get("source_url", ""),
        "fields": fields,
        "health": health_kind(fields.get("health", "")),
        "freshness": freshness(fields.get("updated", ""), now=now, stale_hours=12),
        "orders": orders_summary(fields.get("orders", "")),
        "kit": kit_version(fields.get("kit", "")),
        "stats": stats_repos.get(repo or "", {}) if repo else {},
        # latest committed state, probed over anonymous git transport at
        # bake time (absent in pre-probe mirrors — templates guard on it)
        "head": lane.get("head") or {},
    }
    return view


def seats_view(
    fleet_data: dict[str, Any],
    *,
    now: Optional[datetime] = None,
) -> dict[str, Any]:
    """The 8-standing-seats view baked by ``gen_fleet.bake_seats`` — each
    member repo's heartbeat stamp turned into a freshness reading, and a
    seat-level "last heartbeat" = the freshest member. Mirrors without a
    ``seats`` section (pre-consolidation bakes) yield ``ok=False`` and the
    page skips the section rather than inventing a structure."""
    seats_raw = (fleet_data or {}).get("seats") or []
    if not seats_raw:
        return {"ok": False, "seats": [], "consolidation": {}, "sources": []}
    seats = []
    for s in seats_raw:
        members = []
        best: Optional[dict[str, Any]] = None
        for m in s.get("repos", []):
            fr = freshness(m.get("updated", ""), now=now, stale_hours=12)
            member = {
                "repo": m.get("repo", "?"),
                "repo_url": m.get("repo_url", ""),
                "heartbeat_available": bool(m.get("heartbeat_available")),
                "reason": m.get("reason", ""),
                "freshness": fr,
            }
            members.append(member)
            if fr["ok"] and (best is None or fr["age_hours"] < best["age_hours"]):
                best = fr
        seats.append({
            "seat": s.get("seat", "?"),
            "role": s.get("role", ""),
            "repos": members,
            # honest seat-level reading: freshest member heartbeat, or none
            "last_heartbeat": best,
        })
    return {
        "ok": True,
        "seats": seats,
        "consolidation": (fleet_data or {}).get("consolidation") or {},
        "sources": (fleet_data or {}).get("seats_sources") or [],
    }


_DISPOSITION_ORDER = {"live": 0, "hub": 1, "registry-only": 2, "archived": 3}


def fleet_overview(
    fleet_data: dict[str, Any],
    stats_data: dict[str, Any],
    *,
    now: Optional[datetime] = None,
) -> dict[str, Any]:
    """Everything the /fleet index page needs, honestly counted."""
    stats_repos = (stats_data or {}).get("repos") or {}
    lanes = [lane_view(ln, stats_repos, now=now) for ln in (fleet_data or {}).get("lanes", [])]
    lanes.sort(key=lambda v: (_DISPOSITION_ORDER.get(v["disposition"], 9), v["lane"].lower()))
    registry = (fleet_data or {}).get("registry") or {}
    return {
        "lanes": lanes,
        "registry": registry,
        "counts": {
            "total_seats": registry.get("total_seats", len(lanes)),
            "repo_seats": registry.get("repo_seats", sum(1 for v in lanes if v["repo"])),
            "registry_only": len(registry.get("registry_only_seats", []) or []),
            "live": sum(1 for v in lanes if v["disposition"] == "live"),
            "archived": sum(1 for v in lanes if v["disposition"] == "archived"),
            "hub": sum(1 for v in lanes if v["disposition"] == "hub"),
            "heartbeats_mirrored": sum(1 for v in lanes if v["heartbeat_available"]),
        },
    }


def lane_detail(
    fleet_data: dict[str, Any],
    stats_data: dict[str, Any],
    repo: str,
    *,
    now: Optional[datetime] = None,
) -> Optional[dict[str, Any]]:
    """One repo-backed lane's detail view, or None (→ 404)."""
    stats_repos = (stats_data or {}).get("repos") or {}
    for ln in (fleet_data or {}).get("lanes", []):
        if ln.get("repo") == repo:
            return lane_view(ln, stats_repos, now=now)
    return None
