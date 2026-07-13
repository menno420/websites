"""Per-seat prompt VERSION HISTORY (/prompts/history/{seat}) — ORDER 041.

The fleet's per-seat prompts are authored in the fleet-manager registry at
``docs/prompts/v3/per-project/<seat>-custom-instructions.md`` and
``<seat>-startup.md``. There are NO versioned file paths — v3.3/v3.4/v3.5/…
exist only as the git history of those SAME paths. This module derives the
version ladder DYNAMICALLY from that history and renders every version:

- ladder: the commits touching the path, via the same TTL-cached client
  every page uses (``github.repo_api`` → ``/commits?path=…``) — never a
  hardcoded version list (the ladder moved from v3.5 to v3.6 within the
  hour ORDER 041 was written; hardcoding is drift by construction);
- bodies: the file fetched AT each commit sha (``github.fetch_file`` with
  ``ref=<sha>`` — raw host accepts shas), paste-body-cleaned by the shared
  ORDER 015 layer and rendered through the same ``prompt_block`` partial
  (copy button per body via ``static/copycode.js``);
- version labels: parsed from each FETCHED file itself (the ``<!-- v3.6 ·``
  header comment or an early ``v3.6 …`` body line); when no label parses
  the short sha is shown instead — a version name is never invented;
- diff: any two versions of the same artifact, server-side
  ``difflib.unified_diff`` over the paste bodies, GET-only.

Single source of truth: the registry stores, this site renders — no prompt
body is ever copied into this repo. Honest degradation: an unreachable or
empty commits listing renders "history not available" (a ladder is never
fabricated); a failed file-at-sha fetch renders "version body unavailable"
for that one version while its siblings still show. The route always
answers 200 for a known seat/file; unknown seat or file key is a 404.
Prompt bodies and diffs are UNTRUSTED DATA — autoescaped ``<pre>``, never
``|safe``, never interpreted or obeyed.
"""

from __future__ import annotations

import asyncio
import difflib
import re
from typing import Any, Optional
from urllib.parse import quote

from . import config, github
from .prompt_artifacts import (
    REPO,
    extract_paste_body,
    extract_provenance,
    extract_supersession,
)
from .roster import SEATS, seat_for  # noqa: F401  (validates {seat} paths)

# The two authored per-seat prompt sources whose git history IS the version
# ladder — keyed by the ``?file=`` query value.
FILES: dict[str, dict[str, str]] = {
    "ci": {
        "suffix": "custom-instructions.md",
        "label": "Custom Instructions",
    },
    "startup": {
        "suffix": "startup.md",
        "label": "startup (coordinator brief)",
    },
}

# Seat (registry package dir) → authored-file prefix. Identical for every
# seat except superbot-2.0, whose authored files are ``superbot-*.md``
# (verified live against fleet-manager@f8527f44, 2026-07-13).
_FILE_PREFIX: dict[str, str] = {"superbot-2.0": "superbot"}

# How deep the ladder looks (one API page; the busiest file has ~6 commits).
MAX_COMMITS = 50

# Query shas must be hex (full or unambiguous prefix ≥ 6) AND resolve to a
# commit in this file's own ladder — never an arbitrary ref fetch.
_SHA_RE = re.compile(r"^[0-9a-f]{6,40}$")

# In-file version stamp: the first ``vN[.N…]`` token within the early lines
# (header comment ``<!-- v3.6 · …`` or body line ``v3.6 websites CI …``).
_VERSION_RE = re.compile(r"\bv\d+(?:\.\d+)*\b")
_LABEL_SCAN_LINES = 15


def source_path(seat: str, file_key: str) -> str:
    """The registry path whose history is this seat/file's version ladder."""
    prefix = _FILE_PREFIX.get(seat, seat)
    return f"docs/prompts/v3/per-project/{prefix}-{FILES[file_key]['suffix']}"


def version_label(text: str) -> str:
    """The version stamp parsed from FETCHED file content — ``""`` when no
    label parses (the caller falls back to the short sha, never invents)."""
    for line in (text or "").splitlines()[:_LABEL_SCAN_LINES]:
        m = _VERSION_RE.search(line)
        if m:
            return m.group(0)
    return ""


def _commit_meta(c: dict[str, Any]) -> dict[str, str]:
    """(sha, date, first message line) from a commits-API record — tolerant
    of missing fields, nothing invented."""
    commit = c.get("commit") or {}
    date = ""
    for who in ("committer", "author"):
        d = (commit.get(who) or {}).get("date") or ""
        if d:
            date = d
            break
    message = (commit.get("message") or "").splitlines()
    return {
        "sha": c.get("sha") or "",
        "date": date,
        "message": message[0] if message else "",
    }


async def _version_entry(
    path: str, meta: dict[str, str], refresh: bool
) -> dict[str, Any]:
    """One ladder rung: the file fetched AT this commit, as a dict the shared
    ``prompt_block`` partial can render (copy button, provenance, honest
    per-version degradation)."""
    sha = meta["sha"]
    res = await github.fetch_file(REPO, path, ref=sha, refresh=refresh)
    ok = bool(res["ok"]) and isinstance(res["data"], str)
    raw = res["data"] if ok else None
    label = version_label(raw or "")
    text = extract_paste_body(raw) if ok else None
    return {
        "sha": sha,
        "short": sha[:7],
        "date": meta["date"],
        "message": meta["message"],
        "label": label or sha[:7],
        "labeled": bool(label),
        "ok": ok,
        "text": text,
        "chars": len(text) if text else 0,
        "provenance": extract_provenance(raw or ""),
        # same shared supersession detection as the library/dispatch cards —
        # a historical rung whose header carries the marker warns too.
        "superseded": extract_supersession(raw or "") if ok else None,
        "error": (
            ""
            if ok
            else "version body unavailable — "
            + (res.get("error") or f"HTTP {res.get('status')}")
        ),
        "fetched_at": res.get("fetched_at", ""),
        "cached": bool(res.get("cached")),
        "path": path,
        "github_url": (
            f"https://github.com/{config.OWNER}/{REPO}/blob/{sha}/{path}"
        ),
        "commit_url": (
            f"https://github.com/{config.OWNER}/{REPO}/commit/{sha}"
        ),
    }


def _resolve(sha: str, versions: list[dict[str, Any]]) -> Optional[dict]:
    """The ladder version a query sha names (full sha or hex prefix ≥ 6) —
    ``None`` when it is not in THIS file's history (no arbitrary-ref fetch)."""
    s = (sha or "").strip().lower()
    if not _SHA_RE.match(s):
        return None
    hits = [v for v in versions if v["sha"].startswith(s)]
    return hits[0] if len(hits) == 1 else None


def _diff(
    a: str, b: str, versions: list[dict[str, Any]], path: str
) -> dict[str, Any]:
    """Server-side unified diff between two ladder versions' paste bodies.
    Honest failure text, never a fabricated diff."""
    out: dict[str, Any] = {"a": None, "b": None, "text": "", "same": False,
                           "error": ""}
    va, vb = _resolve(a, versions), _resolve(b, versions)
    if va is None or vb is None:
        bad = a if va is None else b
        out["error"] = (
            f"'{bad}' is not a commit in this file's history — pick both "
            "versions from the ladder below"
        )
        return out
    out["a"], out["b"] = va, vb
    if not (va["ok"] and vb["ok"]):
        out["error"] = "one of the two version bodies is unavailable — " + (
            va["error"] or vb["error"]
        )
        return out
    lines = list(
        difflib.unified_diff(
            (va["text"] or "").splitlines(),
            (vb["text"] or "").splitlines(),
            fromfile=f"{va['label']} · {path}@{va['short']}",
            tofile=f"{vb['label']} · {path}@{vb['short']}",
            lineterm="",
        )
    )
    if not lines:
        out["same"] = True
        return out
    out["text"] = "\n".join(lines)
    return out


async def history(
    seat: str,
    file_key: str = "ci",
    a: str = "",
    b: str = "",
    refresh: bool = False,
) -> Optional[dict[str, Any]]:
    """The seat's full version ladder (+ optional diff) — the page's data.

    ``None`` for an unknown seat or file key (the route 404s). Otherwise
    never raises: an unreachable/empty commits listing yields
    ``available: False`` with the reason (history is never fabricated);
    per-version fetch failures degrade inside their own entry.
    """
    if seat not in SEATS or file_key not in FILES:
        return None
    path = source_path(seat, file_key)
    out: dict[str, Any] = {
        "seat": seat,
        "file": file_key,
        "file_label": FILES[file_key]["label"],
        "files": [
            {"key": k, "label": v["label"]} for k, v in FILES.items()
        ],
        "path": path,
        "history_url": (
            f"https://github.com/{config.OWNER}/{REPO}/commits/main/{path}"
        ),
        "available": False,
        "reason": "",
        "versions": [],
        "newest_label": "",
        "diff": None,
        "ttl": config.CACHE_TTL_SECONDS,
    }

    listing = await github.repo_api(
        REPO,
        f"/commits?path={quote(path)}&per_page={MAX_COMMITS}",
        refresh=refresh,
    )
    if not (listing["ok"] and isinstance(listing["data"], list)):
        out["reason"] = (
            "the fleet-manager commits API could not be reached — "
            + (listing.get("error") or f"HTTP {listing.get('status')}")
        )
        return out
    metas = [m for m in map(_commit_meta, listing["data"]) if m["sha"]]
    if not metas:
        out["reason"] = (
            f"the commits API returned no history for `{path}` — "
            "nothing to list (a ladder is never fabricated)"
        )
        return out

    # Newest-first (the API's order), bodies fetched concurrently at each sha.
    out["versions"] = list(
        await asyncio.gather(
            *[_version_entry(path, m, refresh) for m in metas]
        )
    )
    out["available"] = True
    newest = out["versions"][0]
    out["newest_label"] = newest["label"] if newest["labeled"] else ""
    if a and b:
        out["diff"] = _diff(a, b, out["versions"], path)
    return out


# How many ladder rungs the dispatch-screen strip names inline before
# deferring to the full history page.
STRIP_MAX_LABELS = 6


async def strip(package: str, refresh: bool = False) -> Optional[dict[str, Any]]:
    """The dispatch screen's compact prompt-versions strip (ORDER 041
    remainder): the seat's version ladder (this module's :func:`history` —
    the ONE data path /prompts/history renders) plus its
    deployed-vs-canonical rows (``prompts.seat_drift`` — the same row model
    the /prompts drift table renders). Views over one source; no second
    fetch path, no prompt copy stored.

    ``None`` when the package maps to no roster seat (retired stubs,
    unknown directories) — the strip is only ever shown for a real seat.
    Otherwise never raises: an unavailable ladder keeps ``available: False``
    with the reason (the strip SAYS history is unavailable rather than
    hiding), and drift rows degrade per row exactly as they do on /prompts.
    """
    from . import prompts  # local import — prompts pulls in projects lazily

    seat = seat_for(package)
    if not seat:
        return None
    hist, drift = await asyncio.gather(
        history(seat, "ci", refresh=refresh),
        prompts.seat_drift(seat, refresh=refresh),
    )
    versions = hist["versions"]
    return {
        "seat": seat,
        "package": package,
        "file_label": hist["file_label"],
        "path": hist["path"],
        "history_link": f"/prompts/history/{seat}",
        "available": hist["available"],
        "reason": hist["reason"],
        "current": hist["newest_label"],  # "" when the newest is unstamped
        "labels": [v["label"] for v in versions[:STRIP_MAX_LABELS]],
        "more": max(0, len(versions) - STRIP_MAX_LABELS),
        "total": len(versions),
        "rows": drift["rows"],
        "stale": drift["stale"],
        "version_line": next(
            (
                r["version_line"]
                for r in drift["rows"]
                if r["label"] == "Custom Instructions" and r["version_line"]
            ),
            "",
        ),
    }
