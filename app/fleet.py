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
from urllib.parse import quote

from . import clock, config, github, journal

OWNER = config.OWNER

# The manager's canonical lane registry — the single source of truth for WHICH
# lanes exist. Since 2026-07-11 (fleet-manager PR #59) that is the ``LANES``
# list inside fleet-manager's roster generator: the old hand-kept superbot
# fleet-manifest went `historical` (its table removed — healthcheck run 2
# caught the break live), and the generated roster (docs/roster.md) is a
# STATUS snapshot whose table carries no repo column, so the generator's own
# registry literal is the one machine-readable lane→repo mapping. `/fleet`
# parses it live so a lane added there auto-appears. fleet-manager is
# READ-ONLY here: fetched at request time via the shared TTL-cached github
# layer; nothing upstream is written.
REGISTRY_REPO = "fleet-manager"
REGISTRY_PATH = "scripts/gen_roster.py"

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
    # Enriched machine-readable heartbeat lines (D-0028, retro G3) — all
    # OPTIONAL: a lane that doesn't write them renders exactly as before.
    "routine",
    "landing",
    "deployed",
    # Ladder-rung telemetry (backlog, 2026-07-11): one `rung:` token per wake
    # (order / queue / backlog / self / upkeep-dry) so the manager sees
    # whether a lane lives off orders or self-generated work. Recognized here
    # so it can never leak into the previous field as a continuation (the
    # routine:-into-blockers incident class).
    "rung",
    # Tooling capability token (backlog, 2026-07-11): a fired session stamps
    # its mandated landing-tools probe result (`pr-capable | ritual-only`) so
    # a PR-tooling wall (the 04:03Z ritual-only fire) is visible on /fleet
    # without branch archaeology, and a cross-lane tooling regression shows
    # as a trend. Recognized here for the same leak-guard reason as rung.
    "tooling",
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


# --------------------------------------------------------------------------- #
# Enriched machine-readable heartbeat fields (D-0028, retro G3)
# --------------------------------------------------------------------------- #
# The `orders:` line has always been machine-ish (`acked=… done=…`); these
# helpers actually parse it — plus the OPTIONAL `routine:` / `landing:` lines —
# so `/fleet` (and `/fleet.json` consumers, e.g. the manager) can compute
# "what's left" per lane without diffing inbox vs status vs git. Every parse is
# tolerant and honest: unparseable input yields ok=False / kind "unknown",
# never an invented value.

_ID_RANGE_RE = re.compile(r"^(\d+)\s*[-–]\s*(\d+)$")
_MAX_ID_RANGE = 500  # refuse to expand an absurd range (typo guard)


def _expand_ids(spec: str) -> list[str]:
    """Expand an order-id spec: ``001-004,006`` → ``['001','002','003','004','006']``.

    Ranges keep the zero-padding width of their left edge; a malformed or
    absurdly wide part is skipped (never guessed). Order is preserved,
    duplicates dropped.
    """
    out: list[str] = []
    seen: set[str] = set()

    def add(token: str) -> None:
        if token not in seen:
            seen.add(token)
            out.append(token)

    for part in (spec or "").split(","):
        part = part.strip()
        if not part:
            continue
        m = _ID_RANGE_RE.match(part)
        if m:
            lo_s, hi_s = m.group(1), m.group(2)
            lo, hi = int(lo_s), int(hi_s)
            if lo <= hi and hi - lo <= _MAX_ID_RANGE:
                width = len(lo_s)
                for i in range(lo, hi + 1):
                    add(str(i).zfill(width))
            continue
        if part.isdigit():
            add(part)
    return out


def parse_orders(value: str) -> dict[str, Any]:
    """Parse an ``orders:`` heartbeat value into acked/done/outstanding ids.

    ``acked=001-008 done=001-006`` → outstanding ``['007','008']`` — the ids a
    lane has SEEN but not yet finished, computable from the heartbeat alone.
    An optional ``claimed-by: …`` annotation (the order-claim ritual) is
    captured verbatim. ``ok`` is False when no ``acked=``/``done=`` token
    parsed (free-text orders line) — the caller renders the raw value only.
    """
    v = value or ""
    claimed = None
    m = re.search(r"claimed-by:\s*(.+)$", v)
    if m:
        claimed = m.group(1).strip()
        v = v[: m.start()].strip()

    def ids_of(key: str) -> list[str]:
        mm = re.search(rf"{key}\s*=\s*([0-9,\s–-]+)", v)
        return _expand_ids(mm.group(1).strip()) if mm else []

    acked = ids_of("acked")
    done = ids_of("done")
    done_set = set(done)
    outstanding = [i for i in acked if i not in done_set]

    # The claim's own timestamp (`claimed-by: <ids> <lane> <ISO8601>`) — the
    # claim ritual expires a claim with no visible activity after ~24h, so
    # consumers (/orders claim-aging, /fleet.json) need the WHEN, not just
    # the text. ISO-8601 UTC or None; never guessed.
    claimed_at = None
    if claimed:
        dt = _parse_iso(claimed)
        if dt is not None:
            claimed_at = dt.isoformat()

    return {
        "ok": bool(acked or done),
        "acked": acked,
        "done": done,
        "outstanding": outstanding,
        "claimed": claimed,
        "claimed_at": claimed_at,
    }


_KIT_VERSION_RE = re.compile(r"\bv\d+(?:\.\d+)*\b")


def kit_version(value: str) -> str:
    """The version token out of a ``kit:`` heartbeat line.

    ``v1.7.1 · check: green · engaged: yes`` → ``v1.7.1``; no token → ``""``
    (an honest absence — never guessed from prose).
    """
    m = _KIT_VERSION_RE.search(value or "")
    return m.group(0) if m else ""


def kit_rollup(lanes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Version → lane-count rollup over parsed ``kit:`` lines.

    Counts only lanes with a READABLE heartbeat (missing/errored lanes say
    nothing about kit adoption); a readable heartbeat without a parseable
    kit version lands in the ``none`` bucket. Returns
    ``[{version, count}, …]`` sorted most-common-first, ``none`` always last.
    """
    counts: dict[str, int] = {}
    for lane in lanes:
        if lane.get("missing") or lane.get("fetch_error"):
            continue
        if not lane.get("fields"):
            continue
        v = kit_version(lane["fields"].get("kit", "")) or "none"
        counts[v] = counts.get(v, 0) + 1
    versions = sorted(
        (k for k in counts if k != "none"),
        key=lambda k: (-counts[k], k),
    )
    out = [{"version": v, "count": counts[v]} for v in versions]
    if "none" in counts:
        out.append({"version": "none", "count": counts["none"]})
    return out


_CRON_RE = re.compile(r"cron[:\s]+([\d*/,\- ]+?)(?:\s*[·;|]|$)")


def classify_routine(value: str, now: Optional[datetime] = None) -> dict[str, Any]:
    """Classify a ``routine:`` heartbeat value (the lane's wake clock).

    ``armed`` when the value says so; ``last-fired`` is the last ISO timestamp
    found after a "fired" mention (``last-fired 2026-07-10T16:01Z`` or prose
    like ``last_fired_at 2026-07-10T16:01:32Z``). **silent** flags the failure
    mode this field exists for: a routine that claims armed but whose last
    fire is older than ``config.FLEET_STALE_HOURS`` — armed but silently dead.
    An armed routine with NO parseable fire yet is ``no_fire_recorded`` (an
    honest unknown, not silent — it may simply be freshly armed).
    """
    now = now or clock.now()
    v = (value or "").strip()
    low = v.lower()
    if not v:
        return {"present": False, "armed": False, "silent": False,
                "no_fire_recorded": False, "cron": "", "fired_age_human": ""}
    armed = "armed" in low and "not armed" not in low and "unarmed" not in low
    cron_m = _CRON_RE.search(low)
    cron = cron_m.group(1).strip() if cron_m else ""
    fired_dt = None
    fired_i = low.rfind("fired")
    if fired_i != -1:
        fired_dt = _parse_iso(v[fired_i:])
    silent = False
    fired_age_human = ""
    if fired_dt is not None:
        age_hours = (now - fired_dt).total_seconds() / 3600
        fired_age_human = _human_age(age_hours)
        silent = armed and age_hours >= config.FLEET_STALE_HOURS
    return {
        "present": True,
        "armed": armed,
        "silent": silent,
        "no_fire_recorded": armed and fired_dt is None,
        "cron": cron,
        "fired_age_human": fired_age_human,
    }


def classify_landing(value: str) -> dict[str, Any]:
    """Classify a ``landing:`` heartbeat value (where the session's work IS).

    kinds: ``clean`` (all-merged), ``pushed`` (branch pushed but unmerged —
    a PR-less rescue candidate), ``local`` (LOCAL-ONLY — stranded work, the
    2026-07-10 16:01Z incident class), ``unknown`` (free text / absent).
    ``attention`` is True for pushed/local — `/fleet` sorts those lanes up.
    """
    v = (value or "").strip()
    low = v.lower()
    if not v:
        return {"present": False, "kind": "unknown", "attention": False, "branch": ""}
    branch_m = re.search(r"`?([A-Za-z0-9._/-]*claude/[A-Za-z0-9._-]+)`?", v)
    branch = branch_m.group(1) if branch_m else ""
    if "local-only" in low or "local only" in low:
        kind = "local"
    elif "unmerged" in low or ("pushed" in low and "merged" not in low.replace("unmerged", "")):
        kind = "pushed"
    elif "all-merged" in low or "all merged" in low or low.startswith("clean"):
        kind = "clean"
    else:
        kind = "unknown"
    return {
        "present": True,
        "kind": kind,
        "attention": kind in ("local", "pushed"),
        "branch": branch,
    }


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
    now = now or clock.now()
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


async def heartbeat_freshness(
    repo: str, refresh: bool = False, now: Optional[datetime] = None
) -> Optional[dict[str, Any]]:
    """One repo's heartbeat freshness — the cheap chip for the board rows.

    Fetches ONLY ``control/status.md`` (TTL-cached; deliberately NOT the
    full ``overview()`` fan-out — the board needs one number per repo, not
    18 lanes × commits × pulls). Returns the ``freshness`` dict when the
    heartbeat exists and its ``updated:`` parses; ``None`` for a repo with
    no readable/parseable heartbeat — the board shows no chip rather than
    a guessed age (/fleet stays the honest home for lane errors). ``now``
    is injectable (module convention) so fixed-stamp test fixtures stay
    deterministic.
    """
    res = await github.fetch_file(repo, "control/status.md", refresh=refresh)
    if not (res["ok"] and isinstance(res["data"], str) and res["data"].strip()):
        return None
    fields = parse_status(res["data"], repo)["fields"]
    fresh = freshness(fields.get("updated", ""), now=now)
    return fresh if fresh["ok"] else None


def _envelope_reason(res: dict) -> str:
    """A human reason out of a not-ok result envelope (never empty)."""
    return res.get("error") or (
        f"HTTP {res.get('status')}" if res.get("status") else "unreachable"
    )


def _commit_age(commits_res: dict, now: datetime) -> dict[str, Any]:
    """Last-commit age from a ``/commits?per_page=1`` result (honest on miss).

    Carries the short sha + numeric ``age_hours`` (and a ``reason`` on miss)
    so /freshness can classify commit staleness without re-parsing.
    """
    miss = {"ok": False, "age_human": "unknown", "sha": "", "age_hours": None}
    if not commits_res["ok"] or not isinstance(commits_res["data"], list):
        return {**miss, "reason": _envelope_reason(commits_res)}
    data = commits_res["data"]
    if not data:
        return {**miss, "reason": "no commits returned"}
    sha = str(data[0].get("sha") or "")[:7]
    date = (
        ((data[0].get("commit") or {}).get("committer") or {}).get("date")
        or ((data[0].get("commit") or {}).get("author") or {}).get("date")
        or ""
    )
    dt = _parse_iso(date)
    if dt is None:
        return {**miss, "sha": sha, "reason": "commit date unparseable"}
    age_hours = (now - dt).total_seconds() / 3600
    return {
        "ok": True,
        "age_human": _human_age(age_hours),
        "sha": sha,
        "age_hours": age_hours,
        "reason": "",
    }


def _open_pr_count(pulls_res: dict) -> dict[str, Any]:
    """Open-PR count from a ``/pulls?state=open`` result (honest on miss)."""
    if not pulls_res["ok"] or not isinstance(pulls_res["data"], list):
        return {
            "ok": False,
            "count": None,
            "display": "?",
            "reason": _envelope_reason(pulls_res),
        }
    n = len(pulls_res["data"])
    # per_page caps at 100 — show "100+" rather than an undercount lie.
    return {
        "ok": True,
        "count": n,
        "display": f"{n}+" if n >= 100 else str(n),
        "reason": "",
    }


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


def _file_view_url(repo: str, path: str) -> Optional[str]:
    """In-app /journal/{repo}/file deep-link, or None when the repo is outside
    the render allow-set (config.JOURNAL_RENDER_REPOS — a registry lane the
    file route would 404 gets no dead link)."""
    if repo not in config.JOURNAL_RENDER_REPOS:
        return None
    return f"/journal/{repo}/file?path={quote(path, safe='/')}"


# --------------------------------------------------------------------------- #
# Live lane set from the fleet-manager registry
# --------------------------------------------------------------------------- #
# The registry is the ``LANES = [...]`` literal inside
# fleet-manager/scripts/gen_roster.py — the roster generator's ONE
# hand-maintained input (its own header says "Add a lane here when a seat is
# born"). Each entry: {lane, repo (None for registry-only seats),
# disposition ("live" | "hub" | "archived" | "registry-only"), tokens}.
# We extract the literal with ast.literal_eval (pure data, never executed)
# and map entries to the same lane dicts ``config.FLEET_LANES`` holds:
# {lane, repo, status_path, model, note}. Registry-only seats (no repo) are
# skipped — nothing to fetch; archived/hub dispositions are kept and noted
# (an archived lane's stale heartbeat is honest history, not an error).

_REGISTRY_LANES_RE = re.compile(r"^LANES\s*=\s*(\[.*?\n\])", re.DOTALL | re.MULTILINE)


def parse_registry(text: str) -> list[dict[str, Any]]:
    """Extract the registry's ``LANES`` literal from gen_roster.py source.

    ``ast.literal_eval`` on the captured list — pure data, never executed
    code. Returns [] (never a guess) when the literal is absent or not a
    list of dicts; a malformed literal raises to the caller's honest
    fallback path.
    """
    import ast

    m = _REGISTRY_LANES_RE.search(text or "")
    if not m:
        return []
    data = ast.literal_eval(m.group(1))
    if not isinstance(data, list):
        return []
    return [e for e in data if isinstance(e, dict)]


def registry_to_lanes(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Registry entries → `/fleet` lane dicts (FLEET_LANES shape).

    Registry-only seats (``repo: None``) are skipped — there is no heartbeat
    file to fetch. Every lane reads ``control/status.md`` (the fleet's
    current convention; a lane without one renders as an honest absence).
    The disposition travels in the note so archived/hub lanes read honestly.
    """
    lanes: list[dict[str, Any]] = []
    for e in entries:
        repo = e.get("repo")
        if not repo:
            continue
        disposition = (e.get("disposition") or "").strip()
        note = ""
        if disposition == "hub":
            note = "hub seat — no control/status.md by design (honest absence)."
        elif disposition == "archived":
            note = "archived seat (stale-by-design)."
        elif disposition == "registry-only":  # defensive: repo-less already skipped
            continue
        lanes.append(
            {
                "lane": str(e.get("lane") or repo),
                "repo": str(repo),
                "status_path": "control/status.md",
                "model": "unknown",
                "note": note,
            }
        )
    return lanes


async def resolve_lanes(
    refresh: bool = False,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """The lane set for `/fleet`, live from the registry with an honest fallback.

    PRIMARY: fetch + parse the fleet-manager registry (the ``LANES`` literal
    in gen_roster.py) so a lane added there auto-appears. FALLBACK: on any
    fetch/parse failure (or a parse that yields zero lanes) return the
    hand-kept ``config.FLEET_LANES`` and a ``source`` dict the page renders
    as a visible "using the cached fallback list" notice — it never silently
    pretends the registry was live.
    """
    registry_url = _gh_blob(REGISTRY_REPO, REGISTRY_PATH)
    try:
        fetch = await github.fetch_file(REGISTRY_REPO, REGISTRY_PATH, refresh=refresh)
    except Exception as exc:  # pragma: no cover - defensive
        return list(config.FLEET_LANES), {
            "source": "fallback",
            "ok": False,
            "reason": f"registry fetch raised: {type(exc).__name__}",
            "registry_url": registry_url,
        }

    if not (fetch["ok"] and isinstance(fetch["data"], str) and fetch["data"].strip()):
        reason = fetch.get("error") or f"HTTP {fetch.get('status')}"
        return list(config.FLEET_LANES), {
            "source": "fallback",
            "ok": False,
            "reason": f"registry unavailable ({reason})",
            "registry_url": registry_url,
        }

    try:
        lanes = registry_to_lanes(parse_registry(fetch["data"]))
    except Exception as exc:
        return list(config.FLEET_LANES), {
            "source": "fallback",
            "ok": False,
            "reason": f"registry parse failed: {type(exc).__name__}",
            "registry_url": registry_url,
        }

    if not lanes:
        return list(config.FLEET_LANES), {
            "source": "fallback",
            "ok": False,
            "reason": "registry parsed to zero lanes",
            "registry_url": registry_url,
        }

    return lanes, {
        "source": "registry",
        "ok": True,
        "reason": "",
        "count": len(lanes),
        "registry_url": registry_url,
    }


async def lane_status(
    lane: dict, now: Optional[datetime] = None, refresh: bool = False
) -> dict[str, Any]:
    """One lane's rendered heartbeat: fetch its ``control/status*.md``, parse the
    documented fields, classify health + freshness, render the body markdown, and
    attach the repo's last-commit age + open-PR count. Honest per-lane state:
    ``missing`` (no status file — absence, not error) or ``fetch_error`` (an
    honest banner) when the fetch does not return a body."""
    now = now or clock.now()
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
        # In-app deep-links through the widened /journal/{repo}/file renderer
        # (PR #177 allows every FLEET_LANES repo): the lane's status source and
        # its current-state ledger, readable without leaving the console. None
        # for a registry-only lane outside the render allow-set — the template
        # simply omits the links; the GitHub links above stay the fallback.
        "status_file_url": _file_view_url(repo, path),
        "current_state_url": _file_view_url(repo, "docs/current-state.md"),
        "last_commit": meta["last_commit"],
        "open_prs": meta["open_prs"],
        "missing": False,
        "fetch_error": None,
        "unreadable": False,
        "project": lane["lane"],
        "fields": {},
        "health": classify_health(""),
        "freshness": freshness("", now=now),
        "orders_info": parse_orders(""),
        "routine_info": classify_routine("", now=now),
        "landing_info": classify_landing(""),
        "body_html": "",
    }

    if fetch["ok"] and isinstance(fetch["data"], str) and fetch["data"].strip():
        parsed = parse_status(fetch["data"], lane["lane"])
        fields = parsed["fields"]
        out["project"] = parsed["project"]
        out["fields"] = fields
        out["health"] = classify_health(fields.get("health", ""))
        out["freshness"] = freshness(fields.get("updated", ""), now=now)
        out["orders_info"] = parse_orders(fields.get("orders", ""))
        out["routine_info"] = classify_routine(fields.get("routine", ""), now=now)
        out["landing_info"] = classify_landing(fields.get("landing", ""))
        out["body_html"] = journal.render_markdown(fetch["data"])
    elif fetch["status"] == 404:
        # A 404 is a legitimate "this lane has no status file yet" — an absence,
        # never an error banner. (The bare `superbot` lane is expected here.)
        out["missing"] = True
    elif fetch["status"] in (401, 403):
        # The registry may name a lane whose repo the app's token cannot read
        # (private / not granted / rate limited). Render it honestly as
        # "unreadable" — never drop it — so the owner sees the lane exists but
        # its state is hidden. The underlying reason is preserved in the banner.
        reason = fetch.get("error") or f"HTTP {fetch['status']}"
        out["unreadable"] = True
        out["fetch_error"] = (
            f"unreadable — the board's token cannot read {OWNER}/{repo}: {reason}"
        )
    else:
        out["fetch_error"] = fetch.get("error") or f"HTTP {fetch.get('status')}"

    return out


def _sort_key(lane: dict) -> tuple:
    """Attention-first ordering: lanes that need a look rise to the top.

    rank 0 fetch error · 1 broken · 2 stale heartbeat / stranded landing /
    silently-dead routine · 3 unknown/absent · 4 red-by-design · 5 healthy.
    Within a rank, freshest heartbeat first (unknown age sorts last). Keeps
    problems glanceable at the top of the page.
    """
    if lane["fetch_error"]:
        rank = 0
    elif lane["health"]["kind"] == "broken":
        rank = 1
    elif (
        lane["freshness"].get("stale")
        or lane["landing_info"]["attention"]
        or lane["routine_info"]["silent"]
    ):
        rank = 2
    elif lane["missing"] or lane["health"]["kind"] == "unknown":
        rank = 3
    elif lane["health"]["kind"] == "design":
        rank = 4
    else:
        rank = 5
    age = lane["freshness"].get("age_hours")
    return (rank, age if age is not None else float("inf"))


async def overview(
    refresh: bool = False, now: datetime | None = None
) -> dict[str, Any]:
    """Every fleet lane's heartbeat, attention-sorted, with a fleet summary.

    The lane SET is resolved live from the fleet-manager registry (an added
    lane auto-appears), falling back to ``config.FLEET_LANES`` with an honest
    ``lane_source`` notice when the registry can't be fetched/parsed. Fetches all
    lanes concurrently (cache-backed) against a single ``now`` so every age is
    measured from the same instant. Returns the lane list plus roll-up counts
    (total / live / stale / broken / errored / no-file) so the page can show one
    glanceable header line. ``now`` is injectable (defaults to wall clock,
    same convention as every other age-measuring function here) so tests
    with fixed heartbeat stamps stay deterministic instead of time-bombing
    when the fixtures cross the stale threshold."""
    now = now or clock.now()
    lane_defs, lane_source = await resolve_lanes(refresh=refresh)
    lanes = list(
        await asyncio.gather(
            *[lane_status(lane, now=now, refresh=refresh) for lane in lane_defs]
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
        # Enriched-field roll-ups (0 when no lane writes the optional lines).
        "stranded": sum(1 for lane in lanes if lane["landing_info"]["attention"]),
        "silent_routines": sum(1 for lane in lanes if lane["routine_info"]["silent"]),
        "outstanding_orders": sum(
            len(lane["orders_info"]["outstanding"]) for lane in lanes
        ),
        # kit-version rollup (idea: kit rollup on /fleet) — pure presentation
        # over the already-parsed `kit:` lines: version → lane count, plus a
        # `none` bucket for readable lanes whose heartbeat carries no kit
        # line. Sorted most-common-first for the header badge.
        "kit_versions": kit_rollup(lanes),
    }
    return {
        "lanes": lanes,
        "summary": summary,
        "stale_hours": config.FLEET_STALE_HOURS,
        "lane_source": lane_source,
        "registry_url": lane_source.get("registry_url")
        or _gh_blob(REGISTRY_REPO, REGISTRY_PATH),
    }
