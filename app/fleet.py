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

# The manager's canonical lane registry — the single source of truth for WHICH
# lanes exist (one row per Project). `/fleet` parses this live so a lane added to
# the manifest auto-appears on the page (no hand-kept copy to drift). superbot is
# READ-ONLY here: the file is fetched at request time via the shared TTL-cached
# github layer; nothing in superbot is written.
MANIFEST_REPO = "superbot"
MANIFEST_PATH = "docs/eap/fleet-manifest.md"

# Extract every `menno420/<repo>` reference from a manifest Repo(s) cell.
_MANIFEST_REPO_RE = re.compile(rf"{re.escape(OWNER)}/([A-Za-z0-9._-]+)")

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
    return {
        "ok": bool(acked or done),
        "acked": acked,
        "done": done,
        "outstanding": outstanding,
        "claimed": claimed,
    }


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
    now = now or datetime.now(timezone.utc)
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


# --------------------------------------------------------------------------- #
# Live lane set from the manager's fleet-manifest
# --------------------------------------------------------------------------- #
# The manifest (menno420/superbot -> docs/eap/fleet-manifest.md) is a markdown
# table, one row per Project:
#     | Project | Repo(s) | Model | Routine cadence | Last-seen | Notes |
# We parse the table (mapping columns by HEADER NAME so a reorder can't shift a
# cell), then turn rows into the same lane dicts `config.FLEET_LANES` holds:
#   {lane, repo, status_path, model, note}.
# Two shapes need expanding beyond a plain single-repo row:
#   * a row naming MORE THAN ONE repo (the SuperBot coordinator spans
#     superbot + superbot-next; its heartbeat is written to superbot-next, so the
#     bare superbot lane 404s as an honest absence) -> one lane per repo;
#   * a repo SHARED by >1 row (the superbot-games cohabitation lanes) -> the
#     lane reads `control/status-<slug>.md`, slug derived from the Project name.
# The `manager` row (which builds nothing / owns no concrete repo) is skipped.


def _strip_md(cell: str) -> str:
    """Strip markdown emphasis + a trailing link target from a table cell."""
    return cell.replace("**", "").replace("*", "").strip()


def _lane_slug(project: str) -> str:
    """Distinguishing slug for a shared-repo lane, from its Project name.

    ``game-mining`` -> ``mining``; ``game-exploration`` -> ``exploration`` (the
    segment after the first hyphen). A hyphen-less name slugifies whole. Drives
    the ``control/status-<slug>.md`` path shared-repo cohabitation lanes use.
    """
    p = project.strip().lower()
    tail = p.split("-", 1)[1] if "-" in p else p
    return re.sub(r"[^a-z0-9]+", "-", tail).strip("-") or "lane"


def _clean_model(model: str) -> str:
    """Normalize a manifest Model cell to a display value.

    ``—`` / empty -> ``unknown`` (the template hides an ``unknown`` model). Any
    other value (``Fable 5``, ``default (Opus 4.8)``) is passed through trimmed.
    """
    m = _strip_md(model).strip()
    if not m or m in {"—", "-", "–"}:
        return "unknown"
    return m


def parse_manifest(text: str) -> list[dict[str, Any]]:
    """Parse the fleet-manifest markdown table into raw Project rows.

    Returns one dict per data row: ``{project, repos, model, cadence, last_seen,
    notes}`` where ``repos`` is the list of ``menno420/<repo>`` names in the
    Repo(s) cell (empty for the ``manager`` row, which names no concrete repo).
    Columns are located by HEADER NAME, so a column reorder in the manifest does
    not silently shift a value into the wrong field.
    """
    rows: list[list[str]] = []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("|") and s.endswith("|"):
            # Split on unescaped pipes; drop the empty edges from the outer bars.
            cells = [c.strip() for c in s.strip("|").split("|")]
            rows.append(cells)
    if not rows:
        return []

    # Locate the header row (has both a Project and a Repo column).
    header_i = None
    header: list[str] = []
    for i, cells in enumerate(rows):
        low = [c.lower() for c in cells]
        if any("project" in c for c in low) and any(c.startswith("repo") for c in low):
            header_i, header = i, low
            break
    if header_i is None:
        return []

    def col(*needles: str) -> Optional[int]:
        for idx, name in enumerate(header):
            if any(n in name for n in needles):
                return idx
        return None

    ci = {
        "project": col("project"),
        "repos": col("repo"),
        "model": col("model"),
        "cadence": col("cadence"),
        "last_seen": col("last-seen", "last seen"),
        "notes": col("note"),
    }
    if ci["project"] is None or ci["repos"] is None:
        return []

    def get(cells: list[str], key: str) -> str:
        idx = ci[key]
        if idx is None or idx >= len(cells):
            return ""
        return cells[idx]

    out: list[dict[str, Any]] = []
    for cells in rows[header_i + 1 :]:
        # Skip the header separator row (all cells are dashes) and short rows.
        joined = "".join(cells).replace("|", "")
        if joined and set(joined) <= set("-: "):
            continue
        project = _strip_md(get(cells, "project"))
        if not project:
            continue
        repos_cell = get(cells, "repos")
        repos = _MANIFEST_REPO_RE.findall(repos_cell)
        out.append(
            {
                "project": project,
                "repos": repos,
                "repos_cell": repos_cell,
                "model": get(cells, "model"),
                "cadence": get(cells, "cadence"),
                "last_seen": get(cells, "last_seen"),
                "notes": _strip_md(get(cells, "notes")),
            }
        )
    return out


def manifest_to_lanes(manifest_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Turn parsed manifest rows into `/fleet` lane dicts (FLEET_LANES shape).

    Rows naming no concrete repo (the ``manager`` control chair) are skipped.
    A multi-repo row expands to one lane per repo; a repo shared by >1 row reads
    ``control/status-<slug>.md``. Everything else is a single ``control/status.md``
    lane named for its repo — matching the hand-kept `config.FLEET_LANES` set.
    """
    # A repo shared across rows (or flagged "shared" in its cell) needs per-lane
    # status files, so count repo occurrences across the whole manifest first.
    repo_rows: dict[str, int] = {}
    for row in manifest_rows:
        for repo in row["repos"]:
            repo_rows[repo] = repo_rows.get(repo, 0) + 1

    lanes: list[dict[str, Any]] = []
    for row in manifest_rows:
        repos = row["repos"]
        if not repos:
            continue  # manager / no concrete repo -> not a lane
        model = _clean_model(row["model"])
        notes = row["notes"]
        project = row["project"]
        shared = "shared" in row["repos_cell"].lower()

        if len(repos) > 1:
            # Multi-repo Project (SuperBot coordinator): one lane per repo. Each
            # reads its OWN control/status.md and degrades honestly — the repo
            # that doesn't hold the heartbeat 404s as an absence, never a fake.
            siblings = ", ".join(repos)
            for repo in repos:
                others = [r for r in repos if r != repo]
                note = (
                    f"{project} Project (spans {siblings})."
                    + (f" Heartbeat may live in {', '.join(others)}." if others else "")
                    + (f" {notes}" if notes else "")
                ).strip()
                lanes.append(
                    {
                        "lane": repo,
                        "repo": repo,
                        "status_path": "control/status.md",
                        "model": model,
                        "note": note,
                    }
                )
            continue

        repo = repos[0]
        if shared or repo_rows.get(repo, 0) > 1:
            # Shared-repo cohabitation lane (superbot-games): the Project name
            # distinguishes which status-<slug>.md file it writes.
            slug = _lane_slug(project)
            lanes.append(
                {
                    "lane": f"{repo} · {slug}",
                    "repo": repo,
                    "status_path": f"control/status-{slug}.md",
                    "model": model,
                    "note": notes or f"{project} lane ({repo} shared-repo cohabitation).",
                }
            )
        else:
            lanes.append(
                {
                    "lane": repo,
                    "repo": repo,
                    "status_path": "control/status.md",
                    "model": model,
                    "note": notes,
                }
            )
    return lanes


async def resolve_lanes(
    refresh: bool = False,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """The lane set for `/fleet`, live from the manifest with an honest fallback.

    PRIMARY: fetch + parse the manager's fleet-manifest so a lane added there
    auto-appears. FALLBACK: on any fetch/parse failure (or a parse that yields
    zero lanes) return the hand-kept ``config.FLEET_LANES`` and a ``source`` dict
    the page renders as a visible "using the cached fallback list" notice — it
    never silently pretends the manifest was live.
    """
    manifest_url = _gh_blob(MANIFEST_REPO, MANIFEST_PATH)
    try:
        fetch = await github.fetch_file(MANIFEST_REPO, MANIFEST_PATH, refresh=refresh)
    except Exception as exc:  # pragma: no cover - defensive
        return list(config.FLEET_LANES), {
            "source": "fallback",
            "ok": False,
            "reason": f"manifest fetch raised: {type(exc).__name__}",
            "manifest_url": manifest_url,
        }

    if not (fetch["ok"] and isinstance(fetch["data"], str) and fetch["data"].strip()):
        reason = fetch.get("error") or f"HTTP {fetch.get('status')}"
        return list(config.FLEET_LANES), {
            "source": "fallback",
            "ok": False,
            "reason": f"manifest unavailable ({reason})",
            "manifest_url": manifest_url,
        }

    try:
        lanes = manifest_to_lanes(parse_manifest(fetch["data"]))
    except Exception as exc:  # pragma: no cover - defensive
        return list(config.FLEET_LANES), {
            "source": "fallback",
            "ok": False,
            "reason": f"manifest parse failed: {type(exc).__name__}",
            "manifest_url": manifest_url,
        }

    if not lanes:
        return list(config.FLEET_LANES), {
            "source": "fallback",
            "ok": False,
            "reason": "manifest parsed to zero lanes",
            "manifest_url": manifest_url,
        }

    return lanes, {
        "source": "manifest",
        "ok": True,
        "reason": "",
        "count": len(lanes),
        "manifest_url": manifest_url,
    }


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
        # The manifest may name a lane whose repo the app's token cannot read
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


async def overview(refresh: bool = False) -> dict[str, Any]:
    """Every fleet lane's heartbeat, attention-sorted, with a fleet summary.

    The lane SET is resolved live from the manager's fleet-manifest (an added
    lane auto-appears), falling back to ``config.FLEET_LANES`` with an honest
    ``lane_source`` notice when the manifest can't be fetched/parsed. Fetches all
    lanes concurrently (cache-backed) against a single ``now`` so every age is
    measured from the same instant. Returns the lane list plus roll-up counts
    (total / live / stale / broken / errored / no-file) so the page can show one
    glanceable header line."""
    now = datetime.now(timezone.utc)
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
    }
    return {
        "lanes": lanes,
        "summary": summary,
        "stale_hours": config.FLEET_STALE_HOURS,
        "lane_source": lane_source,
        "manifest_url": lane_source.get("manifest_url")
        or _gh_blob(MANIFEST_REPO, MANIFEST_PATH),
    }
