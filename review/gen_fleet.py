"""Fleet-mirror bake for the review service — registry + heartbeats to JSON.

The review service is network-free at runtime (Railway Root Directory =
``review`` ships only this folder — see ``gen_snapshot.py`` for the full
rationale), so everything the fleet pages show must be COMMITTED under
``review/data/``. This script is the bake half: run it from the repo root
(any session, or the scheduled ``review-bake`` GitHub Actions workflow) and
it writes ``review/data/fleet.json``:

- **The lane registry** — fetched live from the fleet-manager's canonical
  ``LANES`` literal in ``scripts/gen_roster.py`` (the same source the
  control-plane's ``/fleet`` parses; fleet-manager is verified anonymously
  readable over raw.githubusercontent.com — ``docs/CAPABILITIES.md``
  2026-07-10). The registry counts are recorded as found: total seats,
  repo-backed seats, and registry-only seats (a seat with ``repo: None`` has
  no repo to feature — the pages surface that split honestly instead of
  hardcoding a fleet size).
- **Every repo-backed lane's heartbeat** — ``control/status.md`` fetched raw
  and parsed with the fleet's documented key grammar (a standalone copy of
  the ``control/README.md`` format; this script deliberately imports nothing
  from ``app/`` — services never import each other's packages, and a bake
  script honors the same seam). A repo whose heartbeat cannot be fetched is
  recorded with the exact reason — never guessed, never dropped.
- **Every repo-backed lane's latest committed state** — a ``head`` record
  (HEAD sha + committer date) read over ANONYMOUS GIT TRANSPORT
  (``ls-remote`` + a depth-1 treeless fetch), which works in environments
  where the GitHub REST API is walled (session proxies) and needs no token.
  A repo git can't reach (private, gone) records the honest reason.

Fail-soft by design (this runs unattended on a cron): if the REGISTRY fetch
fails and a previously committed ``fleet.json`` exists, the old file is left
in place untouched (its ``generated_at`` ages honestly and the site's
staleness banner does the telling) and the script exits 0. Network calls are
few (1 registry + ~18 raw heartbeat fetches + ~18 git-transport probes, no
REST API) and each is bounded by a timeout.

    python3 review/gen_fleet.py
"""

from __future__ import annotations

import ast
import datetime as dt
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

OWNER = "menno420"
REGISTRY_REPO = "fleet-manager"
REGISTRY_PATH = "scripts/gen_roster.py"
REGISTRY_RAW = (
    f"https://raw.githubusercontent.com/{OWNER}/{REGISTRY_REPO}/main/{REGISTRY_PATH}"
)
REGISTRY_URL = f"https://github.com/{OWNER}/{REGISTRY_REPO}/blob/main/{REGISTRY_PATH}"

OUT_PATH = Path(__file__).resolve().parent / "data" / "fleet.json"
TIMEOUT = 20

# ---------------------------------------------------------------------------
# The 8 standing seats — the fleet's owner-decided standing structure.
#
# This block is REGISTRY STRUCTURE (names, member repos, one-job roles), not
# numbers: it transcribes the owner's 8-seat decision doc and the manager's
# registry restructure, each pinned to its commit below. The per-seat
# HEARTBEAT data is never written here — it is derived at bake/render time
# from the same per-repo heartbeat mirror the lanes use, so the numbers stay
# regenerated, not hand-edited. If the seat structure changes again, the
# fleet-manager registry moves first and this transcription follows it.
#
# Sources (commit-pinned; every URL verified resolving before commit):
# - superbot docs/owner/fleet-8seat-structure-2026-07-11.md
#     @ 95fc025bb56d0901940ccd5a9b6184a2d8a813de
#     (the owner decision — "8 standing Projects, owner-decided 2026-07-11, late")
# - fleet-manager commit 639b0f09d7e99056cb8be83abc733edc198f1728
#     (2026-07-12T03:15:10Z — "Fleet restructure slice 1: registry
#     restructured to the 8 standing seats")
# - fleet-manager projects/README.md @ main (the living 8-seat registry)
# ---------------------------------------------------------------------------
SEAT_DECISION_URL = (
    "https://github.com/menno420/superbot/blob/"
    "95fc025bb56d0901940ccd5a9b6184a2d8a813de/"
    "docs/owner/fleet-8seat-structure-2026-07-11.md"
)
SEAT_REGISTRY_URL = (
    f"https://github.com/{OWNER}/{REGISTRY_REPO}/blob/main/projects/README.md"
)
SEAT_RESTRUCTURE_COMMIT_URL = (
    f"https://github.com/{OWNER}/{REGISTRY_REPO}/commit/"
    "639b0f09d7e99056cb8be83abc733edc198f1728"
)

SEATS: list[dict[str, Any]] = [
    {"seat": "Fleet Manager", "repos": ["fleet-manager"],
     "role": "Hub — single source of truth; routes work; keeps records truthful"},
    {"seat": "Venture Lab", "repos": ["venture-lab", "trading-strategy"],
     "role": "Make money; trading-strategy is a research toolkit only (holdout spent)"},
    {"seat": "SuperBot World", "repos": ["superbot-games", "superbot-idle", "superbot-mineverse"],
     "role": "The bot's games (flagship: mineverse — it reads the bot's mining economy)"},
    {"seat": "SuperBot 2.0", "repos": ["superbot-next", "superbot"],
     "role": "Drive the rebuild to cutover; keep prod alive"},
    {"seat": "Ideas Lab", "repos": ["idea-engine", "sim-lab"],
     "role": "Generate → verify; honest nulls are the product"},
    {"seat": "Game Lab", "repos": ["gba-homebrew", "pokemon-mod-lab"],
     "role": "Standalone games; strict public/private isolation"},
    {"seat": "Self Improvement", "repos": ["substrate-kit"],
     "role": "Improve the workflow all seats run on"},
    {"seat": "Websites", "repos": ["websites"],
     "role": "Control plane; merge = deploy"},
]

CONSOLIDATION: dict[str, Any] = {
    # Precise phrasing, on purpose: no machine count of exactly 15 exists —
    # the peak is screenshot-supported ("~15"), the 8-seat side is
    # commit-verified. Decided late 2026-07-11 (owner decision doc);
    # canonicalized in the fleet-manager registry 2026-07-12T03:15Z.
    "summary": (
        "peaked at ~15 Projects; consolidation decided 2026-07-11, "
        "canonicalized 2026-07-12T03:15Z"
    ),
    "peak": "~15",
    "decided": "2026-07-11",
    "canonicalized": "2026-07-12T03:15:10Z",
    "evidence": [
        {"label": "the 8-seat decision doc (superbot, 2026-07-11)",
         "url": SEAT_DECISION_URL},
        {"label": "registry restructure commit (fleet-manager 639b0f0, 2026-07-12T03:15Z)",
         "url": SEAT_RESTRUCTURE_COMMIT_URL},
        {"label": "before: the ~15-Project grid (fig-01)",
         "url": ("https://github.com/menno420/superbot/blob/"
                 "e3eb0eb2bf3683794dd0d8c40bbf3988832c31ea/"
                 "docs/eap/screenshots-2026-07-11/index.md")},
        {"label": "after: the 8-seat grid (fig-21)",
         "url": ("https://github.com/menno420/superbot/blob/"
                 "cbb549539c64e0ce3b4fea268e27b7ac49eeaf08/"
                 "docs/eap/screenshots-2026-07-12/index.md")},
    ],
}

# The documented control/status.md field keys (control/README.md grammar —
# a standalone copy of app/fleet.KNOWN_KEYS; see module docstring for why
# this is a copy and not an import).
KNOWN_KEYS = {
    "updated", "phase", "health", "last-shipped", "blockers", "orders",
    "needs-owner", "notes", "kit", "routine", "landing", "deployed",
    "rung", "tooling",
}

_REGISTRY_LANES_RE = re.compile(r"^LANES\s*=\s*(\[.*?\n\])", re.DOTALL | re.MULTILINE)

# Per-field cap for the committed mirror. Some lanes write huge free-text
# fields (or don't follow the grammar, so a whole document lands in one
# field as continuation lines); the review pages show summary cards, not
# full bodies, and an uncapped mirror weighed 440KB. Truncation is marked
# visibly — never silent.
FIELD_CAP = 600
_TRUNC_MARK = " … [truncated for the mirror — full text at the source]"


def _fetch(url: str) -> tuple[str | None, str]:
    """(body, "") on success; (None, reason) on any failure — never raises."""
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT) as resp:  # noqa: S310
            return resp.read().decode("utf-8", errors="replace"), ""
    except urllib.error.HTTPError as exc:
        return None, f"HTTP {exc.code}"
    except Exception as exc:  # noqa: BLE001 — fail-soft bake, reason recorded
        return None, f"{type(exc).__name__}: {exc}"


def head_probe(repo: str) -> dict[str, Any]:
    """Latest committed state of one repo over anonymous git transport.

    ``git ls-remote`` advertises the default-branch HEAD sha without auth;
    a depth-1 ``--filter=tree:0`` bare fetch of HEAD then yields the commit
    date at near-zero transfer cost. Chosen over the REST API on purpose:
    git transport is reachable from session containers whose proxy walls
    api.github.com, and from the Actions runner alike. Fail-soft: any
    failure records its reason (private wall, empty repo, timeout) —
    a latest-commit is never invented.
    """
    url = f"https://github.com/{OWNER}/{repo}"
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
    try:
        out = subprocess.run(
            ["git", "ls-remote", url, "HEAD"],
            capture_output=True, text=True, timeout=TIMEOUT * 2, env=env,
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "reason": "ls-remote timed out"}
    if out.returncode != 0:
        reason = (out.stderr or "").strip().splitlines()
        return {"ok": False, "reason": f"unreadable over git transport ({reason[-1] if reason else 'ls-remote failed'})"}
    first = out.stdout.strip().splitlines()
    sha = first[0].split("\t")[0].strip() if first else ""
    if not re.fullmatch(r"[0-9a-f]{40}", sha or ""):
        return {"ok": False, "reason": "no HEAD advertised (empty repo?)"}
    committed_at = ""
    with tempfile.TemporaryDirectory() as td:
        try:
            subprocess.run(["git", "init", "-q", "--bare", td],
                           check=True, timeout=30, capture_output=True, env=env)
            subprocess.run(
                ["git", "-C", td, "fetch", "-q", "--depth", "1",
                 "--filter=tree:0", url, "HEAD"],
                check=True, timeout=TIMEOUT * 3, capture_output=True, env=env,
            )
            committed_at = subprocess.run(
                ["git", "-C", td, "log", "-1", "--format=%cI", "FETCH_HEAD"],
                check=True, timeout=30, capture_output=True, text=True, env=env,
            ).stdout.strip()
        except (subprocess.SubprocessError, OSError):
            committed_at = ""  # the sha is still real; the date degrades honestly
    return {
        "ok": True,
        "sha": sha,
        "committed_at": committed_at,
        "source": "anonymous git transport (ls-remote + depth-1 fetch)",
    }


def parse_registry(text: str) -> list[dict[str, Any]]:
    """The ``LANES`` literal out of gen_roster.py source — pure data via
    ``ast.literal_eval``, never executed. [] when absent/malformed."""
    m = _REGISTRY_LANES_RE.search(text or "")
    if not m:
        return []
    try:
        data = ast.literal_eval(m.group(1))
    except (ValueError, SyntaxError):
        return []
    if not isinstance(data, list):
        return []
    return [e for e in data if isinstance(e, dict)]


def _norm_key(raw: str) -> str:
    return raw.strip().lstrip("⚑").strip().lower()


def parse_heartbeat(text: str) -> dict[str, str]:
    """``control/status.md`` → the documented ``key: value`` fields, verbatim.

    Same tolerant grammar the control-plane uses: a line whose leading token
    is not a known key continues the current field (wrapped values survive);
    a colon inside a value never starts a new field.
    """
    fields: dict[str, str] = {}
    cur: str | None = None
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
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
    for key, value in fields.items():
        if len(value) > FIELD_CAP:
            fields[key] = value[:FIELD_CAP].rstrip() + _TRUNC_MARK
    return fields


def bake_lane(entry: dict[str, Any]) -> dict[str, Any]:
    """One registry entry → its committed lane record (heartbeat mirrored)."""
    repo = entry.get("repo")
    lane: dict[str, Any] = {
        "lane": str(entry.get("lane") or repo or "?"),
        "repo": repo,
        "disposition": str(entry.get("disposition") or ""),
    }
    if not repo:
        lane["heartbeat"] = {
            "available": False,
            "reason": "registry-only seat — no repo, nothing to mirror",
        }
        return lane
    lane["repo_url"] = f"https://github.com/{OWNER}/{repo}"
    lane["head"] = head_probe(repo)
    hb_url = f"https://raw.githubusercontent.com/{OWNER}/{repo}/main/control/status.md"
    body, err = _fetch(hb_url)
    if body is None or not body.strip():
        reason = err or "empty file"
        if err == "HTTP 404":
            reason = "HTTP 404 — no control/status.md on main (or repo not public)"
        lane["heartbeat"] = {"available": False, "reason": reason}
    else:
        lane["heartbeat"] = {
            "available": True,
            "fields": parse_heartbeat(body),
            "source_url": f"https://github.com/{OWNER}/{repo}/blob/main/control/status.md",
        }
    return lane


def bake_seats(lanes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """The 8 standing seats, each joined to its member repos' mirrored
    heartbeats. The heartbeat data comes from the SAME per-repo fetches the
    lane mirror uses (never hand-written): each member repo carries its
    heartbeat ``updated:`` stamp verbatim, or the honest reason it could not
    be read. A repo in the seat structure but absent from the lane registry
    is recorded as such — never silently dropped."""
    by_repo = {ln.get("repo"): ln for ln in lanes if ln.get("repo")}
    seats: list[dict[str, Any]] = []
    for seat in SEATS:
        members: list[dict[str, Any]] = []
        for repo in seat["repos"]:
            lane = by_repo.get(repo)
            if lane is None:
                members.append({
                    "repo": repo,
                    "heartbeat_available": False,
                    "updated": "",
                    "reason": "repo not in the lane registry mirror",
                })
                continue
            hb = lane.get("heartbeat") or {}
            members.append({
                "repo": repo,
                "repo_url": lane.get("repo_url", f"https://github.com/{OWNER}/{repo}"),
                "heartbeat_available": bool(hb.get("available")),
                "updated": (hb.get("fields") or {}).get("updated", ""),
                "reason": hb.get("reason", ""),
            })
        seats.append({
            "seat": seat["seat"],
            "role": seat["role"],
            "repos": members,
        })
    return seats


def main() -> int:
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    reg_text, reg_err = _fetch(REGISTRY_RAW)
    entries = parse_registry(reg_text) if reg_text else []

    if not entries:
        reason = reg_err or "registry parsed to zero seats"
        if OUT_PATH.exists():
            print(
                f"registry unavailable ({reason}) — keeping the previously "
                f"committed {OUT_PATH.name} untouched (fail-soft)."
            )
            return 0
        # First-ever bake with no registry: write an honest empty mirror so
        # the site banners rather than 500s or invents lanes.
        out = {
            "generated_at": now,
            "registry": {
                "ok": False,
                "reason": reason,
                "url": REGISTRY_URL,
                "total_seats": 0,
                "repo_seats": 0,
                "registry_only_seats": [],
            },
            "lanes": [],
        }
        OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUT_PATH.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {OUT_PATH.name} with an honest empty registry ({reason})")
        return 0

    lanes = [bake_lane(e) for e in entries]
    registry_only = [ln["lane"] for ln in lanes if not ln.get("repo")]
    out = {
        "generated_at": now,
        "registry": {
            "ok": True,
            "reason": "",
            "url": REGISTRY_URL,
            "total_seats": len(lanes),
            "repo_seats": len(lanes) - len(registry_only),
            "registry_only_seats": registry_only,
        },
        # The standing structure: 8 seats over the per-repo lanes, plus the
        # consolidation record (both commit-pinned — see the module constants).
        "seats": bake_seats(lanes),
        "seats_sources": [
            {"label": "the 8-seat decision doc", "url": SEAT_DECISION_URL},
            {"label": "fleet-manager projects/ registry", "url": SEAT_REGISTRY_URL},
            {"label": "restructure commit 639b0f0", "url": SEAT_RESTRUCTURE_COMMIT_URL},
        ],
        "consolidation": CONSOLIDATION,
        "lanes": lanes,
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    mirrored = sum(1 for ln in lanes if ln.get("heartbeat", {}).get("available"))
    heads = sum(1 for ln in lanes if ln.get("head", {}).get("ok"))
    print(
        f"wrote {OUT_PATH.name}: {len(lanes)} seats "
        f"({len(lanes) - len(registry_only)} repo-backed, "
        f"{len(registry_only)} registry-only), {mirrored} heartbeats mirrored, "
        f"{heads} repo HEADs probed"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
