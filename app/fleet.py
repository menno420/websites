"""Fleet heartbeat view: every lane's ``control/status*.md`` on one screen.

The fleet-coordination protocol (menno420/superbot →
``docs/planning/fleet-coordination-protocol-2026-07-09.md`` §1) has each Project
write a ``control/status.md`` heartbeat in its OWN repo, overwritten every
session. The claude.ai UI cannot show which agents are running or how far along
they are (session activity is invisible), so those committed heartbeat files are
the truth. ``/fleet`` fetches every lane's status file (cache-backed) and renders
it as one glanceable page — the owner's single control glance over the whole
fleet.

Each lane carries its parsed heartbeat fields (updated-age + a stale badge,
phase, health with a green / red / red-by-design indicator, last-shipped,
blockers, ⚑ needs-owner), the repo's last-commit age + open-PR count, and the
full status body rendered as markdown (reusing ``journal.render_markdown``).
Every fetch degrades honestly per-lane: a repo with no status file shows an
absence card, a fetch failure shows an error banner — never a faked value.
"""

from __future__ import annotations

import asyncio
import re
from datetime import datetime, timezone
from typing import Any, Optional

from . import config, github, journal

OWNER = config.OWNER

# Documented status.md field keys (control/README.md format block). A line is
# only treated as a NEW field when its leading token (before the first colon) is
# one of these — so a colon INSIDE a value (an ISO timestamp "12:07Z", a URL,
# a "#PR — text" line) never spuriously starts a field. ``kit`` is the optional
# substrate-kit self-report line (adopter-visibility band, kit v1.3.0).
KNOWN_KEYS = {
    "updated",
    "phase",
    "health",
    "last-shipped",
    "blockers",
    "orders",
    "needs-owner",
    "notes",
    "kit",
}

_ISO_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2})(?::(\d{2}))?")


def _norm_key(raw: str) -> str:
    """Normalize a field key: drop a leading ``⚑`` flag + whitespace, lowercase.
    ``⚑ needs-owner`` → ``needs-owner``; ``Updated`` → ``updated``."""
    return raw.strip().lstrip("⚑").strip().lower()


def parse_status(text: str, fallback_project: str) -> dict[str, Any]:
    """Parse a ``control/status.md`` heartbeat into project name + fields.

    The project name is the first ``# <project> · status`` heading (the trailing
    "· status" is stripped). Fields are the documented ``key: value`` lines; a
    line whose leading token is NOT a known key is treated as a continuation of
    the current field (so a wrapped value is preserved, never lost). Returns a
    ``{project, fields}`` dict where ``fields`` maps normalized keys → values.
    """
    project = fallback_project
    have_heading = False
    fields: dict[str, str] = {}
    cur: Optional[str] = None

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if not have_heading and stripped.startswith("#"):
            name = re.sub(r"^#+\s*", "", stripped)
            name = re.sub(r"·\s*status\s*$", "", name).strip()
            if name:
                project = name
            have_heading = True
            continue
        if ":" in stripped:
            raw_key, _, value = stripped.partition(":")
            nk = _norm_key(raw_key)
            if nk in KNOWN_KEYS:
                fields[nk] = value.strip()
                cur = nk
                continue
        if cur is not None:
            fields[cur] = f"{fields[cur]} {stripped}".strip()

    return {"project": project, "fields": fields}


def classify_health(health: str) -> dict[str, str]:
    """Collapse a ``health:`` value into a display kind + badge class.

    kinds: ``ok`` (green), ``design`` (red-by-design — purple, NOT broken),
    ``broken`` (red), ``unknown`` (unparseable / empty). Badge classes map to
    the base.html pills (``b ok`` / ``b design`` / ``b bad`` / ``b unknown``).
    """
    h = (health or "").strip().lower()
    if h.startswith("green"):
        return {"kind": "ok", "badge": "ok", "label": "green"}
    if h.startswith("red-by-design") or h.startswith("red by design"):
        return {"kind": "design", "badge": "design", "label": "red-by-design"}
    if h.startswith("broken") or h.startswith("red"):
        return {"kind": "broken", "badge": "bad", "label": "broken"}
    if not h:
        return {"kind": "unknown", "badge": "unknown", "label": "unknown"}
    return {"kind": "unknown", "badge": "unknown", "label": h.split()[0]}


def _parse_iso(ts: str) -> Optional[datetime]:
    """Best-effort parse of the fleet's ISO-ish timestamps as UTC.

    Handles ``2026-07-09T15:25Z`` (no seconds), ``2026-07-09T15:26:00Z``, and a
    space separator. Every fleet heartbeat writes UTC (``Z`` / ``+00``), so we
    treat the wall-clock as UTC for freshness math. Returns None if unparseable.
    """
    m = _ISO_RE.search(ts or "")
    if not m:
        return None
    y, mo, d, h, mi, se = m.groups()
    try:
        return datetime(
            int(y), int(mo), int(d), int(h), int(mi), int(se or 0),
            tzinfo=timezone.utc,
        )
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


def freshness(updated: str, now: Optional[datetime] = None) -> dict[str, Any]:
    """Heartbeat freshness for an ``updated:`` timestamp.

    Returns ``{ok, iso, age_hours, age_human, stale}``. ``stale`` is True when
    the heartbeat is older than ``config.FLEET_STALE_HOURS`` — the manager reads
    a stale heartbeat as a dark Project. An unparseable timestamp is ``ok=False``
    (rendered honestly as "age unknown", never faked fresh).
    """
    now = now or datetime.now(timezone.utc)
    dt = _parse_iso(updated)
    if dt is None:
        return {"ok": False, "iso": (updated or "").strip(), "age_hours": None,
                "age_human": "age unknown", "stale": False}
    age_hours = (now - dt).total_seconds() / 3600
    return {
        "ok": True,
        "iso": dt.isoformat(),
        "age_hours": age_hours,
        "age_human": _human_age(age_hours),
        "stale": age_hours >= config.FLEET_STALE_HOURS,
    }


def _commit_age(commits_res: dict, now: datetime) -> dict[str, Any]:
    """Last-commit age from a ``/commits?per_page=1`` result (honest on miss)."""
    if not commits_res["ok"] or not isinstance(commits_res["data"], list):
        return {"ok": False, "age_human": "unknown"}
    data = commits_res["data"]
    if not data:
        return {"ok": False, "age_human": "unknown"}
    date = (
        ((data[0].get("commit") or {}).get("committer") or {}).get("date")
        or ((data[0].get("commit") or {}).get("author") or {}).get("date")
        or ""
    )
    dt = _parse_iso(date)
    if dt is None:
        return {"ok": False, "age_human": "unknown"}
    return {"ok": True, "age_human": _human_age((now - dt).total_seconds() / 3600)}


def _open_pr_count(pulls_res: dict) -> dict[str, Any]:
    """Open-PR count from a ``/pulls?state=open`` result (honest on miss)."""
    if not pulls_res["ok"] or not isinstance(pulls_res["data"], list):
        return {"ok": False, "count": None, "display": "?"}
    n = len(pulls_res["data"])
    # per_page caps at 100 — show "100+" rather than an undercount lie.
    return {"ok": True, "count": n, "display": f"{n}+" if n >= 100 else str(n)}


async def repo_meta(repo: str, now: datetime, refresh: bool = False) -> dict[str, Any]:
    """Per-repo signals the status file can't give: last-commit age + open-PR
    count. Cache-backed; both degrade to an honest "unknown" on fetch failure."""
    commits_res, pulls_res = await asyncio.gather(
        github.repo_api(repo, "/commits?per_page=1", refresh=refresh),
        github.repo_api(repo, "/pulls?state=open&per_page=100", refresh=refresh),
    )
    return {
        "last_commit": _commit_age(commits_res, now),
        "open_prs": _open_pr_count(pulls_res),
    }


def _gh_blob(repo: str, path: str) -> str:
    return f"https://github.com/{OWNER}/{repo}/blob/main/{path}"


async def lane_status(
    lane: dict, now: Optional[datetime] = None, refresh: bool = False
) -> dict[str, Any]:
    """One lane's rendered heartbeat: fetch its ``control/status*.md``, parse the
    documented fields, classify health + freshness, render the body markdown, and
    attach the repo's last-commit age + open-PR count. Honest per-lane state:
    ``missing`` (no status file — absence, not error) or ``fetch_error`` (an
    honest banner) when the fetch does not return a body."""
    now = now or datetime.now(timezone.utc)
    repo = lane["repo"]
    path = lane["status_path"]

    fetch, meta = await asyncio.gather(
        github.fetch_file(repo, path, refresh=refresh),
        repo_meta(repo, now, refresh=refresh),
    )

    out: dict[str, Any] = {
        "lane": lane["lane"],
        "repo": repo,
        "status_path": path,
        "model": lane.get("model", "unknown"),
        "note": lane.get("note", ""),
        "github_url": _gh_blob(repo, path),
        "repo_url": f"https://github.com/{OWNER}/{repo}",
        "last_commit": meta["last_commit"],
        "open_prs": meta["open_prs"],
        "missing": False,
        "fetch_error": None,
        "project": lane["lane"],
        "fields": {},
        "health": classify_health(""),
        "freshness": freshness("", now=now),
        "body_html": "",
    }

    if fetch["ok"] and isinstance(fetch["data"], str) and fetch["data"].strip():
        parsed = parse_status(fetch["data"], lane["lane"])
        fields = parsed["fields"]
        out["project"] = parsed["project"]
        out["fields"] = fields
        out["health"] = classify_health(fields.get("health", ""))
        out["freshness"] = freshness(fields.get("updated", ""), now=now)
        out["body_html"] = journal.render_markdown(fetch["data"])
    elif fetch["status"] == 404:
        # A 404 is a legitimate "this lane has no status file yet" — an absence,
        # never an error banner. (The bare `superbot` lane is expected here.)
        out["missing"] = True
    else:
        out["fetch_error"] = fetch.get("error") or f"HTTP {fetch.get('status')}"

    return out


def _sort_key(lane: dict) -> tuple:
    """Attention-first ordering: lanes that need a look rise to the top.

    rank 0 fetch error · 1 broken · 2 stale heartbeat · 3 unknown/absent ·
    4 red-by-design · 5 healthy. Within a rank, freshest heartbeat first
    (unknown age sorts last). Keeps problems glanceable at the top of the page.
    """
    if lane["fetch_error"]:
        rank = 0
    elif lane["health"]["kind"] == "broken":
        rank = 1
    elif lane["freshness"].get("stale"):
        rank = 2
    elif lane["missing"] or lane["health"]["kind"] == "unknown":
        rank = 3
    elif lane["health"]["kind"] == "design":
        rank = 4
    else:
        rank = 5
    age = lane["freshness"].get("age_hours")
    return (rank, age if age is not None else float("inf"))


async def overview(refresh: bool = False) -> dict[str, Any]:
    """Every fleet lane's heartbeat, attention-sorted, with a fleet summary.

    Fetches all lanes concurrently (cache-backed) against a single ``now`` so
    every age is measured from the same instant. Returns the lane list plus
    roll-up counts (total / live / stale / broken / errored / no-file) so the
    page can show one glanceable header line."""
    now = datetime.now(timezone.utc)
    lanes = list(
        await asyncio.gather(
            *[lane_status(lane, now=now, refresh=refresh) for lane in config.FLEET_LANES]
        )
    )
    lanes.sort(key=_sort_key)

    summary = {
        "total": len(lanes),
        "healthy": sum(
            1
            for lane in lanes
            if lane["health"]["kind"] in ("ok", "design")
            and not lane["freshness"].get("stale")
            and not lane["fetch_error"]
        ),
        "stale": sum(1 for lane in lanes if lane["freshness"].get("stale")),
        "broken": sum(1 for lane in lanes if lane["health"]["kind"] == "broken"),
        "errored": sum(1 for lane in lanes if lane["fetch_error"]),
        "no_file": sum(1 for lane in lanes if lane["missing"]),
    }
    return {
        "lanes": lanes,
        "summary": summary,
        "stale_hours": config.FLEET_STALE_HOURS,
        "manifest_url": (
            f"https://github.com/{OWNER}/superbot/blob/main/docs/eap/fleet-manifest.md"
        ),
    }
