"""Repo freshness view: which fleet repos are moving, and which are stale.

`/fleet` answers "what does each lane SAY it is doing" (the heartbeat
files); this page answers the colder question "is each repo actually
MOVING?" — one row per fleet repo with the four movement signals:

* last commit — short sha + age (the repo's hardest movement proof),
* last session card — newest dated ``.sessions/YYYY-MM-DD-*.md`` filename
  on main + its age (the fleet's session-trail convention),
* open PR count — in-flight work,
* heartbeat age — the ``updated:`` stamp of ``control/status.md``.

Staleness classification (amber): heartbeat older than
``config.FLEET_STALE_HOURS`` (the existing /fleet threshold — fleet seats
heartbeat at least daily, so a missed wake shows within the same day) OR
last commit older than ``COMMIT_STALE_DAYS`` (a weekly cadence floor so
low-traffic-but-alive seats don't false-alarm). Exactly AT a threshold is
not stale; strictly past it is. A lane the registry marks archived/hub is
exempt — its old ages are honest history, rendered as a dim note, never
amber.

Honest degradation everywhere: any not-ok fetch renders
"unknown — <reason>", never a fabricated freshness and never a 500. The
lane set resolves live from the fleet-manager registry with the same
visible fallback notice `/fleet` shows (``fleet.resolve_lanes``).

Layering: domain module — imports the ``fleet`` + ``github`` primitives,
never routes or templates. ``now`` is injectable (``clock.now()``
fallback), per the time-discipline convention.
"""

from __future__ import annotations

import asyncio
import re
from datetime import datetime, timezone
from typing import Any, Optional

from . import clock, config, fleet, github

OWNER = config.OWNER

# Commit-staleness floor: a repo whose last commit is older than this many
# days badges stale. One week — the fleet's low-traffic seats land work in
# weekly rhythm at the slowest, so anything quieter than that is genuinely
# dark; a tighter floor would false-alarm alive-but-quiet seats.
COMMIT_STALE_DAYS = 7

# A dated session card: the fleet-wide `.sessions/YYYY-MM-DD-<slug>.md`
# convention. Anything else in the directory (README, stubs) is ignored.
_CARD_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-.+\.md$")


def _unknown(reason: str) -> dict[str, Any]:
    """The honest empty signal — ok=False plus WHY, never a guessed value."""
    return {"ok": False, "reason": reason}


async def last_card(
    repo: str, now: datetime, refresh: bool = False
) -> dict[str, Any]:
    """Newest dated session card on main: list ``.sessions/`` via the
    contents API, take the max ``YYYY-MM-DD-*.md`` filename date.

    Returns ``{ok, date, age_days, age_human}`` or an honest
    ``{ok: False, reason}`` (404 = the repo keeps no session trail on main;
    that is an absence to report, not an error to hide)."""
    res = await github.repo_api(repo, "/contents/.sessions", refresh=refresh)
    if not res["ok"]:
        if res["status"] == 404:
            return _unknown("no .sessions/ on main (HTTP 404)")
        return _unknown(fleet._envelope_reason(res))
    if not isinstance(res["data"], list):
        return _unknown("unexpected .sessions/ listing payload")
    dates: list[str] = []
    for entry in res["data"]:
        m = _CARD_RE.match(str(entry.get("name") or ""))
        if m:
            dates.append(m.group(1))
    if not dates:
        return _unknown("no dated session cards in .sessions/")
    latest = max(dates)
    try:
        dt = datetime.strptime(latest, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return _unknown(f"card date unparseable ({latest})")
    age_hours = (now - dt).total_seconds() / 3600
    return {
        "ok": True,
        "date": latest,
        "age_days": age_hours / 24,
        "age_human": fleet._human_age(age_hours),
    }


async def heartbeat(
    repo: str, now: datetime, refresh: bool = False
) -> dict[str, Any]:
    """The ``updated:`` age of ``control/status.md`` — ``{ok, iso,
    age_hours, age_human}`` or an honest ``{ok: False, reason}``.

    Reuses the fleet parser + freshness math; the STALE decision is made by
    the caller (this page's boundary is strict-past, `/fleet`'s is at)."""
    res = await github.fetch_file(repo, "control/status.md", refresh=refresh)
    if not res["ok"]:
        if res["status"] == 404:
            return _unknown("no control/status.md on main (HTTP 404)")
        return _unknown(fleet._envelope_reason(res))
    if not (isinstance(res["data"], str) and res["data"].strip()):
        return _unknown("empty status file")
    fields = fleet.parse_status(res["data"], repo)["fields"]
    fresh = fleet.freshness(fields.get("updated", ""), now=now)
    if not fresh["ok"]:
        return _unknown("updated: line missing or unparseable")
    return {
        "ok": True,
        "iso": fresh["iso"],
        "age_hours": fresh["age_hours"],
        "age_human": fresh["age_human"],
    }


def _exempt_note(note: str) -> bool:
    """True for a lane whose registry disposition marks it archived/hub —
    old ages there are honest history, not staleness."""
    low = (note or "").lower()
    return "archived" in low or "hub" in low


async def repo_row(
    lane: dict[str, Any], now: datetime, refresh: bool = False
) -> dict[str, Any]:
    """One repo's freshness row: the four signals + staleness state."""
    repo = lane["repo"]
    meta, beat, card = await asyncio.gather(
        fleet.repo_meta(repo, now, refresh=refresh),
        heartbeat(repo, now, refresh=refresh),
        last_card(repo, now, refresh=refresh),
    )
    last_commit = meta["last_commit"]
    exempt = _exempt_note(lane.get("note", ""))

    # Strictly PAST the threshold is stale; exactly at it is not.
    commit_stale = bool(
        last_commit["ok"]
        and last_commit["age_hours"] is not None
        and last_commit["age_hours"] > COMMIT_STALE_DAYS * 24
    )
    heartbeat_stale = bool(
        beat["ok"] and beat["age_hours"] > config.FLEET_STALE_HOURS
    )
    if exempt:
        # Archived/hub: keep the honest ages, drop the alarm.
        commit_stale = heartbeat_stale = False

    stale = commit_stale or heartbeat_stale
    if exempt:
        state = "exempt"
    elif stale:
        state = "stale"
    elif last_commit["ok"] or beat["ok"]:
        state = "moving"
    else:
        state = "unknown"

    return {
        "lane": lane["lane"],
        "repo": repo,
        "repo_url": f"https://github.com/{OWNER}/{repo}",
        "note": lane.get("note", ""),
        "exempt": exempt,
        "last_commit": last_commit,
        "commit_stale": commit_stale,
        "open_prs": meta["open_prs"],
        "card": card,
        "heartbeat": beat,
        "heartbeat_stale": heartbeat_stale,
        "stale": stale,
        "state": state,
    }


_STATE_RANK = {"stale": 0, "unknown": 1, "moving": 2, "exempt": 3}


def _sort_key(row: dict[str, Any]) -> tuple:
    """Attention-first: stale rows on top, then unknowns, moving, exempt;
    deterministic within a state by lane name."""
    return (_STATE_RANK.get(row["state"], 1), row["lane"])


async def overview(
    refresh: bool = False, now: Optional[datetime] = None
) -> dict[str, Any]:
    """Every fleet repo's freshness row, attention-sorted, with a summary.

    Lane set from ``fleet.resolve_lanes()`` (live registry, honest
    ``lane_source`` fallback notice). All rows fetch concurrently against a
    single injectable ``now`` so every age is measured from one instant.
    """
    now = now or clock.now()
    lane_defs, lane_source = await fleet.resolve_lanes(refresh=refresh)
    rows = list(
        await asyncio.gather(
            *[repo_row(lane, now, refresh=refresh) for lane in lane_defs]
        )
    )
    rows.sort(key=_sort_key)
    summary = {
        "total": len(rows),
        "moving": sum(1 for r in rows if r["state"] == "moving"),
        "stale": sum(1 for r in rows if r["state"] == "stale"),
        "unknown": sum(1 for r in rows if r["state"] == "unknown"),
        "exempt": sum(1 for r in rows if r["state"] == "exempt"),
    }
    return {
        "rows": rows,
        "summary": summary,
        "stale_hours": config.FLEET_STALE_HOURS,
        "commit_stale_days": COMMIT_STALE_DAYS,
        "lane_source": lane_source,
        "registry_url": lane_source.get("registry_url")
        or fleet._gh_blob(fleet.REGISTRY_REPO, fleet.REGISTRY_PATH),
    }
