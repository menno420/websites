"""The morning briefing (/owner/briefing): one gated page answering "what
happened while I was away?" — what shipped, what's waiting on you, what's
stale, what's being watched.

ORDER 025. Six sections over a bounded time window (default: the last
16 hours; ``?hours=`` override clamped to 1–168, invalid values fall back
to the default with the fallback noted honestly on the page):

1. **SHIPPED** — PRs merged inside the window across the board repos
   (``config.REPOS``), via the same TTL-cached github client every other
   page rides.
2. **ORDERS** — the /orders cross-reference reused whole
   (``orders.overview``): open/claimed/done/unknown counts + the open ones
   listed.
3. **ASKS** — the open ``⚑ OWNER-ACTION`` blocks of this repo's
   ``docs/owner/OWNER-ACTIONS.md`` (parsed with the same
   ``owner_queue.parse_owner_actions`` the /queue page uses).
4. **FLEET** — the /freshness rollup filtered to the stale/amber rows
   only, plus the environments completeness rollup
   (``envhub.board_rollup``) filtered to incomplete/unknown groups.
   NAMES-NEVER-VALUES: group ids and variable NAMES only — live values
   were dropped at the client boundary and do not exist here.
5. **WATCHES** — the latest review-bake workflow run's conclusion, plus
   every open non-draft PR across the board repos with its head check
   state.
6. **REPORTS** — the newest ``## REPORT`` entry of this repo's
   ``control/outbox.md`` (the lane→manager channel), fetched over the same
   committed-file read path as ASKS. One briefing URL carries both the
   owner's morning read and the manager roll-up. The outbox is append-only
   with one writer, so the newest report is the LAST report heading in
   document order.

Honesty contract (the #240/#250 idiom): every section carries its own
``state`` (``ok`` | ``unknown``) and, when unknown, the exact bounded
``reason`` — a failed source renders "unknown — <reason>", never fabricated
data and never a silent omission; the route always answers 200.

Layering: domain module — imports the domain/data + client layers only
(``orders``, ``freshness``, ``envhub``, ``owner_queue``, ``github``),
never routes or templates. No new network surface: every fetch goes
through the existing TTL-cached ``github`` client. ``now`` is injectable
(``clock.now()`` fallback), per the time-discipline convention.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Any, Optional

from . import (
    clock,
    config,
    envhub,
    fleet,
    freshness,
    github,
    orders,
    owner_queue,
)

OWNER = config.OWNER

DEFAULT_WINDOW_HOURS = 16
MIN_WINDOW_HOURS = 1
MAX_WINDOW_HOURS = 168

OWNER_ACTIONS_REPO = "websites"
OWNER_ACTIONS_PATH = "docs/owner/OWNER-ACTIONS.md"
OWNER_ACTIONS_URL = (
    f"https://github.com/{OWNER}/{OWNER_ACTIONS_REPO}/blob/main/"
    f"{OWNER_ACTIONS_PATH}"
)

REVIEW_BAKE_REPO = "websites"
REVIEW_BAKE_WORKFLOW = "review-bake.yml"

OUTBOX_REPO = "websites"
OUTBOX_PATH = "control/outbox.md"
OUTBOX_URL = (
    f"https://github.com/{OWNER}/{OUTBOX_REPO}/blob/main/{OUTBOX_PATH}"
)

# Bounded fan-out: how many closed PRs to scan per repo for the SHIPPED
# window, how many open ⚑ asks to headline, how many open PRs to carry
# check states for, how many body lines of the newest outbox report to
# render before pointing at the full file. All fetches ride the shared
# TTL cache.
SHIPPED_SCAN_PER_REPO = 30
ASKS_TOP_LIMIT = 5
WATCH_PR_LIMIT = 12
OUTBOX_REPORT_MAX_LINES = 40

# Check-run conclusions that count as a red verdict (the readiness board's
# broken-run set — same taxonomy, no fork).
_RED_CONCLUSIONS = (
    "failure",
    "timed_out",
    "cancelled",
    "action_required",
    "startup_failure",
)


# --------------------------------------------------------------------------- #
# Window
# --------------------------------------------------------------------------- #
def parse_window(raw: Optional[str]) -> dict[str, Any]:
    """The briefing window from a raw ``?hours=`` value.

    Absent/empty → the 16h default, silently. A parseable number is clamped
    to [1, 168] — clamping is noted honestly. Anything unparseable falls
    back to the default WITH a visible note (never a silent correction,
    never a 4xx — the page always renders).
    """
    if raw is None or not str(raw).strip():
        return {"hours": DEFAULT_WINDOW_HOURS, "default_used": True, "note": ""}
    try:
        hours = int(str(raw).strip())
    except ValueError:
        return {
            "hours": DEFAULT_WINDOW_HOURS,
            "default_used": True,
            "note": (
                f"?hours={raw!r} is not a whole number — "
                f"using the default {DEFAULT_WINDOW_HOURS}h window"
            ),
        }
    if hours < MIN_WINDOW_HOURS:
        return {
            "hours": MIN_WINDOW_HOURS,
            "default_used": False,
            "note": (
                f"?hours={hours} clamped up to {MIN_WINDOW_HOURS}h "
                f"(sane range {MIN_WINDOW_HOURS}–{MAX_WINDOW_HOURS})"
            ),
        }
    if hours > MAX_WINDOW_HOURS:
        return {
            "hours": MAX_WINDOW_HOURS,
            "default_used": False,
            "note": (
                f"?hours={hours} clamped down to {MAX_WINDOW_HOURS}h "
                f"(sane range {MIN_WINDOW_HOURS}–{MAX_WINDOW_HOURS})"
            ),
        }
    return {"hours": hours, "default_used": False, "note": ""}


def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%MZ")


# --------------------------------------------------------------------------- #
# 1 · SHIPPED — merged PRs inside the window
# --------------------------------------------------------------------------- #
async def shipped(
    cutoff: datetime, refresh: bool = False
) -> dict[str, Any]:
    """Merged PRs across ``config.REPOS`` whose merge time is inside the
    window, newest first. Per-repo failures are listed with their bounded
    reason; the section is ``unknown`` only when EVERY repo failed."""
    repos = list(config.REPOS)
    results = await asyncio.gather(
        *[
            github.repo_api(
                r,
                "/pulls?state=closed&per_page="
                f"{SHIPPED_SCAN_PER_REPO}&sort=updated&direction=desc",
                refresh=refresh,
            )
            for r in repos
        ]
    )
    items: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for repo, res in zip(repos, results):
        if not (res["ok"] and isinstance(res["data"], list)):
            errors.append(
                {
                    "repo": repo,
                    "reason": github.short_reason(
                        res.get("error") or f"HTTP {res.get('status')}",
                        status=res.get("status"),
                    ),
                }
            )
            continue
        for p in res["data"]:
            merged_at = p.get("merged_at") or ""
            dt = fleet._parse_iso(merged_at)
            if dt is None or dt < cutoff:
                continue
            items.append(
                {
                    "repo": repo,
                    "number": p.get("number"),
                    "title": p.get("title") or "",
                    "merged_at": merged_at,
                    "url": p.get("html_url")
                    or f"https://github.com/{OWNER}/{repo}/pull/{p.get('number')}",
                }
            )
    items.sort(key=lambda i: i["merged_at"], reverse=True)
    state = "unknown" if errors and len(errors) == len(repos) else "ok"
    reason = (
        "; ".join(f"{e['repo']}: {e['reason']}" for e in errors)
        if state == "unknown"
        else ""
    )
    return {"state": state, "reason": reason, "rows": items, "errors": errors}


# --------------------------------------------------------------------------- #
# 2 · ORDERS — the /orders cross-reference, reused whole
# --------------------------------------------------------------------------- #
async def orders_digest(
    refresh: bool = False, now: Optional[datetime] = None
) -> dict[str, Any]:
    """Counts + the open/unknown-state orders, from ``orders.overview()``
    (the exact /orders parse — same cache, same classification)."""
    data = await orders.overview(refresh=refresh, now=now)
    cards = data["cards"]
    readable = [c for c in cards if not c["fetch_error"]]
    open_orders: list[dict[str, Any]] = []
    for card in cards:
        for o in card["orders"]:
            if o["state"] != "open":
                continue
            open_orders.append(
                {
                    "repo": card["repo"],
                    "id": o["id"],
                    "priority": orders.order_priority(o),
                    "issued": o.get("issued", ""),
                    "do": (o.get("fields", {}).get("do") or "")[:200],
                    "url": card["inbox_url"],
                }
            )

    def _newest(o: dict) -> tuple:
        dt = fleet._parse_iso(o.get("issued", ""))
        return (0, -dt.timestamp()) if dt is not None else (1, 0.0)

    open_orders.sort(key=_newest)
    if cards and not readable:
        reason = github.short_reason(
            "; ".join(
                f"{c['repo']}: {c['fetch_error']}" for c in cards[:3]
            )
        )
        return {
            "state": "unknown",
            "reason": f"no inbox was readable — {reason}",
            "summary": data["summary"],
            "open_orders": [],
        }
    return {
        "state": "ok",
        "reason": "",
        "summary": data["summary"],
        "open_orders": open_orders,
    }


# --------------------------------------------------------------------------- #
# 3 · ASKS — open ⚑ OWNER-ACTION blocks of docs/owner/OWNER-ACTIONS.md
# --------------------------------------------------------------------------- #
def open_section(text: str) -> tuple[str, str]:
    """The ledger's "Open — waiting on the owner" slice: from the level-2
    Open heading to the next level-2 heading (Decided asks are kept
    verbatim there and must not count as open). Returns ``(slice, note)``
    — no Open heading found scans the whole document with an honest note,
    never silently."""
    lines = (text or "").splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.startswith("## ") and "open" in line.lower():
            start = i
            break
    if start is None:
        return text or "", (
            "no '## … Open' heading found in the ledger — "
            "scanning the whole document"
        )
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if lines[j].startswith("## "):
            end = j
            break
    return "\n".join(lines[start:end]), ""


async def asks(refresh: bool = False) -> dict[str, Any]:
    """Open ⚑ rows parsed from the committed owner-actions ledger with the
    same block parser /queue uses (``owner_queue.parse_owner_actions``).
    Newest first = reverse document order (the ledger appends new asks at
    the end of its Open section)."""
    res = await github.fetch_file(
        OWNER_ACTIONS_REPO, OWNER_ACTIONS_PATH, refresh=refresh
    )
    if not (res["ok"] and isinstance(res["data"], str) and res["data"].strip()):
        return {
            "state": "unknown",
            "reason": github.short_reason(
                res.get("error") or f"HTTP {res.get('status')}",
                status=res.get("status"),
            ),
            "count": 0,
            "top": [],
            "note": "",
            "url": OWNER_ACTIONS_URL,
        }
    section, note = open_section(res["data"])
    _preamble, blocks = owner_queue.parse_owner_actions(section)
    items = [
        {
            "what": b.get("what")
            or next(iter(b.values()), "(unlabeled ask)"),
            "where": b.get("where", ""),
            "unblocks": b.get("unblocks", ""),
        }
        for b in blocks
    ]
    items.reverse()  # ledger appends newest last → newest first here
    return {
        "state": "ok",
        "reason": "",
        "count": len(items),
        "top": items[:ASKS_TOP_LIMIT],
        "note": note,
        "url": OWNER_ACTIONS_URL,
    }


# --------------------------------------------------------------------------- #
# 4 · FLEET — stale repos + incomplete environments only
# --------------------------------------------------------------------------- #
async def fleet_attention(
    refresh: bool = False, now: Optional[datetime] = None
) -> dict[str, Any]:
    """The /freshness rollup reduced to what needs a look: the stale
    (amber) rows, with the unknown rows counted honestly; plus the
    environments rollup reduced to incomplete/unknown groups. Group ids
    and variable NAMES only — never values."""
    fresh, env = await asyncio.gather(
        freshness.overview(refresh=refresh, now=now),
        envhub.board_rollup(refresh=refresh),
    )
    stale_rows = [r for r in fresh["rows"] if r["state"] == "stale"]
    unknown_rows = [r for r in fresh["rows"] if r["state"] == "unknown"]
    return {
        # freshness.overview degrades per-row, never raises: rows always
        # exist, so the freshness half is presented with its own summary
        # and the per-row unknown reasons rather than one section state.
        "state": "ok",
        "reason": "",
        "stale": stale_rows,
        "unknown_rows": unknown_rows,
        "summary": fresh["summary"],
        "lane_source": fresh["lane_source"],
        "env": {
            "state": env["state"],
            "reason": env.get("reason", ""),
            "groups": env.get("groups", 0),
            "incomplete_names": env.get("incomplete_names", []),
            "unknown_names": env.get("unknown_names", []),
        },
    }


# --------------------------------------------------------------------------- #
# 5 · WATCHES — review-bake conclusion + open non-draft PR check states
# --------------------------------------------------------------------------- #
def _checks_verdict(runs: list[dict]) -> str:
    """Collapse a head's check runs into one verdict: ``green`` (every run
    completed successfully/neutrally/skipped), ``failing`` (any red
    conclusion), ``pending`` (any run not completed), or ``none`` (no runs
    reported)."""
    if not runs:
        return "none"
    if any(
        r.get("status") == "completed"
        and (r.get("conclusion") or "") in _RED_CONCLUSIONS
        for r in runs
    ):
        return "failing"
    if any(r.get("status") != "completed" for r in runs):
        return "pending"
    return "green"


async def _pr_checks(repo: str, pr: dict, refresh: bool) -> dict[str, Any]:
    sha = (pr.get("head") or {}).get("sha") or ""
    row = {
        "repo": repo,
        "number": pr.get("number"),
        "title": pr.get("title") or "",
        "created_at": pr.get("created_at") or "",
        "url": pr.get("html_url")
        or f"https://github.com/{OWNER}/{repo}/pull/{pr.get('number')}",
        "checks": "unknown",
        "checks_reason": "",
        "checks_counts": {},
    }
    if not sha:
        row["checks_reason"] = "PR payload carries no head sha"
        return row
    res = await github.repo_api(
        repo, f"/commits/{sha}/check-runs?per_page=100", refresh=refresh
    )
    if not (res["ok"] and isinstance(res["data"], dict)):
        row["checks_reason"] = github.short_reason(
            res.get("error") or f"HTTP {res.get('status')}",
            status=res.get("status"),
        )
        return row
    runs = res["data"].get("check_runs", []) or []
    row["checks"] = _checks_verdict(runs)
    counts: dict[str, int] = {}
    for r in runs:
        key = (
            (r.get("conclusion") or r.get("status") or "unknown")
            if r.get("status") == "completed"
            else (r.get("status") or "pending")
        )
        counts[key] = counts.get(key, 0) + 1
    row["checks_counts"] = counts
    return row


async def watches(refresh: bool = False) -> dict[str, Any]:
    """The latest review-bake run's conclusion + every open non-draft PR
    across the board repos with its head check verdict, newest first
    (bounded to ``WATCH_PR_LIMIT`` rows, the cap noted when it bites)."""
    repos = list(config.REPOS)
    bake_res, *pulls_results = await asyncio.gather(
        github.repo_api(
            REVIEW_BAKE_REPO,
            f"/actions/workflows/{REVIEW_BAKE_WORKFLOW}/runs?per_page=1",
            refresh=refresh,
        ),
        *[
            github.repo_api(
                r,
                # Exact URL the readiness board fetches — a warm cache
                # serves this section for free.
                "/pulls?state=open&per_page=100&sort=created&direction=asc",
                refresh=refresh,
            )
            for r in repos
        ],
    )

    # --- review-bake ---
    if bake_res["ok"] and isinstance(bake_res["data"], dict):
        runs = bake_res["data"].get("workflow_runs") or []
        if runs:
            run = runs[0]
            concluded = run.get("status") == "completed"
            bake = {
                "state": "ok",
                "reason": "",
                "conclusion": (
                    (run.get("conclusion") or "unknown")
                    if concluded
                    else (run.get("status") or "pending")
                ),
                "completed": concluded,
                "event": run.get("event") or "",
                "started_at": run.get("run_started_at")
                or run.get("created_at")
                or "",
                "url": run.get("html_url") or "",
            }
        else:
            bake = {
                "state": "ok",
                "reason": "",
                "conclusion": "",
                "completed": False,
                "event": "",
                "started_at": "",
                "url": "",
            }
    else:
        bake = {
            "state": "unknown",
            "reason": github.short_reason(
                bake_res.get("error") or f"HTTP {bake_res.get('status')}",
                status=bake_res.get("status"),
            ),
            "conclusion": "",
            "completed": False,
            "event": "",
            "started_at": "",
            "url": "",
        }

    # --- open non-draft PRs ---
    candidates: list[tuple[str, dict]] = []
    errors: list[dict[str, str]] = []
    for repo, res in zip(repos, pulls_results):
        if not (res["ok"] and isinstance(res["data"], list)):
            errors.append(
                {
                    "repo": repo,
                    "reason": github.short_reason(
                        res.get("error") or f"HTTP {res.get('status')}",
                        status=res.get("status"),
                    ),
                }
            )
            continue
        for p in res["data"]:
            if p.get("draft"):
                continue
            candidates.append((repo, p))
    candidates.sort(key=lambda rp: rp[1].get("created_at") or "", reverse=True)
    capped = len(candidates) > WATCH_PR_LIMIT
    candidates = candidates[:WATCH_PR_LIMIT]
    prs = list(
        await asyncio.gather(
            *[_pr_checks(repo, p, refresh) for repo, p in candidates]
        )
    )
    prs_state = "unknown" if errors and len(errors) == len(repos) else "ok"
    prs_reason = (
        "; ".join(f"{e['repo']}: {e['reason']}" for e in errors)
        if prs_state == "unknown"
        else ""
    )
    return {
        "bake": bake,
        "prs": {
            "state": prs_state,
            "reason": prs_reason,
            "rows": prs,
            "errors": errors,
            "capped": capped,
            "limit": WATCH_PR_LIMIT,
        },
    }


# --------------------------------------------------------------------------- #
# 6 · REPORTS — the newest control/outbox.md REPORT entry
# --------------------------------------------------------------------------- #
def latest_report(text: str) -> dict[str, Any]:
    """The newest ``## REPORT`` entry of an outbox document.

    Entry grammar (``control/README.md`` + the file's own header): a
    level-2 heading ``## REPORT · <ISO8601> · <from → to> · <TITLE>``,
    body running to the next level-2 heading (``###`` subsections belong
    to the entry). The outbox is append-only with one writer, so the
    newest report is the LAST report heading in document order — no
    timestamp arithmetic, no guessing. Non-REPORT entries (PROPOSAL,
    SIM-REQUEST, markers) are ignored; a heading that starts ``## REPORT``
    but does not parse to the grammar is skipped and COUNTED honestly in
    ``note`` — never rendered as if it were a report, never fabricated
    around. No reports at all → ``found: False`` (the honest-empty state;
    the caller renders the absence explicitly).
    """
    lines = (text or "").splitlines()
    heading_idx = [i for i, ln in enumerate(lines) if ln.startswith("## ")]
    reports: list[dict[str, Any]] = []
    malformed = 0
    for pos, i in enumerate(heading_idx):
        if not lines[i].startswith("## REPORT"):
            continue
        parts = [p.strip() for p in lines[i][3:].split("·")]
        if (
            len(parts) < 4
            or parts[0] != "REPORT"
            or not parts[1]
            or "→" not in parts[2]
        ):
            malformed += 1
            continue
        end = (
            heading_idx[pos + 1]
            if pos + 1 < len(heading_idx)
            else len(lines)
        )
        body = lines[i + 1 : end]
        while body and not body[0].strip():
            body.pop(0)
        while body and not body[-1].strip():
            body.pop()
        reports.append(
            {
                "issued": parts[1],
                "route": parts[2],
                "title": " · ".join(parts[3:]),
                "body": body,
            }
        )
    note = (
        f"{malformed} REPORT-like heading(s) skipped — "
        "not in the entry grammar"
        if malformed
        else ""
    )
    if not reports:
        return {
            "found": False,
            "issued": "",
            "route": "",
            "title": "",
            "lines": [],
            "truncated": False,
            "limit": OUTBOX_REPORT_MAX_LINES,
            "total_reports": 0,
            "note": note,
        }
    newest = reports[-1]  # append-only file → newest entry is last
    truncated = len(newest["body"]) > OUTBOX_REPORT_MAX_LINES
    return {
        "found": True,
        "issued": newest["issued"],
        "route": newest["route"],
        "title": newest["title"],
        "lines": newest["body"][:OUTBOX_REPORT_MAX_LINES],
        "truncated": truncated,
        "limit": OUTBOX_REPORT_MAX_LINES,
        "total_reports": len(reports),
        "note": note,
    }


async def outbox_report(refresh: bool = False) -> dict[str, Any]:
    """The newest REPORT entry of the committed lane→manager outbox,
    fetched with the same ``github.fetch_file`` path ASKS rides (raw host
    first, TTL-cached). Unreadable file → ``state: unknown`` with the
    bounded reason; readable file with no REPORT entries → ``state: ok``
    with ``found: False`` (an honest absence, not a failure)."""
    res = await github.fetch_file(OUTBOX_REPO, OUTBOX_PATH, refresh=refresh)
    if not (res["ok"] and isinstance(res["data"], str) and res["data"].strip()):
        return {
            "state": "unknown",
            "reason": github.short_reason(
                res.get("error") or f"HTTP {res.get('status')}",
                status=res.get("status"),
            ),
            "found": False,
            "issued": "",
            "route": "",
            "title": "",
            "lines": [],
            "truncated": False,
            "limit": OUTBOX_REPORT_MAX_LINES,
            "total_reports": 0,
            "note": "",
            "url": OUTBOX_URL,
        }
    report = latest_report(res["data"])
    return {"state": "ok", "reason": "", "url": OUTBOX_URL, **report}


# --------------------------------------------------------------------------- #
# The page payload
# --------------------------------------------------------------------------- #
async def overview(
    hours_raw: Optional[str] = None,
    refresh: bool = False,
    now: Optional[datetime] = None,
) -> dict[str, Any]:
    """Everything /owner/briefing renders: the window + the six sections,
    fetched concurrently. Never raises for an upstream failure — each
    section degrades to its own honest unknown; the route stays 200."""
    now = now or clock.now()
    window = parse_window(hours_raw)
    cutoff = now - timedelta(hours=window["hours"])
    (
        shipped_s,
        orders_s,
        asks_s,
        fleet_s,
        watches_s,
        outbox_s,
    ) = await asyncio.gather(
        shipped(cutoff, refresh=refresh),
        orders_digest(refresh=refresh, now=now),
        asks(refresh=refresh),
        fleet_attention(refresh=refresh, now=now),
        watches(refresh=refresh),
        outbox_report(refresh=refresh),
    )
    return {
        "window": window,
        "cutoff_iso": _iso(cutoff),
        "now_iso": _iso(now),
        "default_hours": DEFAULT_WINDOW_HOURS,
        "min_hours": MIN_WINDOW_HOURS,
        "max_hours": MAX_WINDOW_HOURS,
        "shipped": shipped_s,
        "orders": orders_s,
        "asks": asks_s,
        "fleet": fleet_s,
        "watches": watches_s,
        "outbox": outbox_s,
    }
