"""Projects registry view (/projects): render fleet-manager's ``projects/``
directory — one card per Project package.

ORDER 009 increment (1): the owner centralizes ALL fleet/project information
in ``menno420/fleet-manager`` and browses it on this site — the manager's repo
STORES, the site RENDERS. The ``projects/`` registry holds one package per
repo (``projects/<repo>/``) carrying the files a Project runs on: Custom
Instructions, the coordinator prompt, the environment setup script, a
failsafe, and a ``meta.md`` describing the package's deployed state.

The registry is being created upstream RIGHT NOW (dispatch note on the
order), so this page's honest EMPTY state is its expected launch state: a
``projects/`` folder that does not exist yet renders as a friendly
"registry not landed yet" card — never a 500, never invented packages.
Other degradations follow the /queue + /environments model exactly:
``not-configured`` (GITHUB_TOKEN unset AND the fetch failed) or
``unavailable`` (token set, fetch failed, reason surfaced). Same TTL-cached
``github`` layer as every other page; fleet-manager is READ-ONLY here.

Per package the page shows: the recognized role files (instructions /
coordinator-prompt / setup / failsafe / meta — matched by tolerant filename
heuristics, unrecognized files listed honestly as "other"), each deep-linked
to GitHub, plus ``meta.md`` rendered inline (sanitized markdown) with a
best-effort ``deployed:``-style state line surfaced as a badge — absent
metadata shows as "unknown", never a fabricated state.

Owner Launch Console (single-screen dispatch, 2026-07-12 ask): the index
splits into active **Seats** (owner start order — :func:`start_rank`) with
retired/merged **stubs** collapsed below (:func:`is_stub`, fail-active), and
each seat links to ``/projects/{package}`` (:func:`detail`) — the dispatch
screen rendering every recognized role file's FULL content copy-ready, plus
best-effort meta fields (deployed state / environment / claude.ai Project
URL — absent = "unknown"/"none recorded", never invented). Package names are
validated against the live registry listing; anything else is 404.

Seat role-coverage chips (backlog bullet, 2026-07-12): each seat card on the
index carries a chip row over the dispatch-critical roles — instructions /
coordinator / failsafe, present ✓ or missing ✗ (:func:`role_coverage`) —
derived from the role-classified listing the page already fetches (zero
extra API calls), so "which seat can't launch yet" is a glance instead of a
mid-dispatch surprise. A package whose listing failed shows NO chips
(``coverage`` = ``[]``, ``dispatch_ready`` = ``None``) — honest unknown,
never a fabricated ✗.
"""

from __future__ import annotations

import asyncio
import re
from typing import Any, Optional

from . import config, github, journal, prompt_artifacts

# Shared with /prompts (ORDER 015): same registry repo, same blob deep-links.
from .prompt_artifacts import REPO, blob_url as _blob_url  # noqa: F401

ROOT = "projects"

# Safety bounds — a registry of package folders, not an arbitrary tree.
MAX_PACKAGES = 30
MAX_FILES_PER_PACKAGE = 20

# Filename → role heuristics (checked against the lowercased basename).
# Tolerant on purpose: the upstream package layout is still landing, so we
# recognize the intent-bearing names and list everything else honestly.
_ROLE_PATTERNS: list[tuple[str, str, str]] = [
    # (role key, human label, substring matched in the basename)
    ("meta", "meta / deployed-state", "meta"),
    ("instructions", "Custom Instructions", "instruction"),
    ("coordinator", "coordinator prompt", "coordinator"),
    ("setup", "setup script", "setup"),
    ("failsafe", "failsafe", "failsafe"),
    ("routine", "wake-routine prompt", "routine"),
]

# Best-effort deployed-state extraction from meta.md: the first line whose
# key looks like a deploy/state field. Never guessed — no match = "".
_STATE_LINE_RE = re.compile(
    r"^\s*\**\s*(deployed(?:-state)?|state|status)\s*\**\s*[:=]\s*(.+)$",
    re.IGNORECASE,
)

# Best-effort environment-name extraction from meta.md (same discipline as
# _STATE_LINE_RE: first matching key line wins, no match = "" = "unknown").
_ENV_LINE_RE = re.compile(
    r"^\s*[-*>\s]*\**\s*(?:environment(?:[-_ ]?name)?|env(?:[-_ ]?name)?)"
    r"\s*\**\s*[:=]\s*(.+)$",
    re.IGNORECASE,
)

# Best-effort claude.ai Project URL from meta.md — the first recorded link
# wins; absent = "" (the page renders "none recorded", never an invented URL).
_PROJECT_URL_RE = re.compile(r"https://claude\.ai/projects?/[^\s)\]>`\"',]+")

# Stub detection (tolerant, fail-ACTIVE): a package whose meta declares it
# retired / merged away / a stub collapses under the index's "Retired /
# merged stubs" <details>. The state line may use the ambiguous word
# "merged"; the body scan sticks to the unambiguous spellings so prose like
# "PR #12 merged" never demotes a live seat — when unsure, treat as active,
# never hide a real seat.
_STUB_STATE_RE = re.compile(r"\b(retired|merged|stub|archived)\b", re.IGNORECASE)
_STUB_BODY_RE = re.compile(r"\b(retired|stub|merged[- ]into)\b", re.IGNORECASE)
_STUB_BODY_SCAN_LINES = 10

# The owner's seat start order (dispatch order, 2026-07-12 ask). Each entry
# is the set of package names (lowercased, "_"→"-") that map to that slot;
# unmatched packages sort after every matched one, alphabetically.
_START_ORDER: list[tuple[str, ...]] = [
    ("fleet-manager", "project-manager"),
    ("venture-lab",),
    ("superbot-world",),
    ("superbot-2.0", "superbot-next", "superbot-2", "superbot2.0", "superbot2"),
    ("ideas-lab",),
    ("game-lab",),
    ("self-improvement",),
    ("websites",),
]

# Detail-page package names: plain directory-name shape only. The real gate
# is membership in the live registry listing; this just refuses traversal
# shapes (slashes, dots-only, leading dot) before any fetch happens.
_SAFE_PKG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,100}$")

# Dispatch-critical roles (seat role-coverage chips, backlog bullet
# 2026-07-12): a seat launches from its Custom Instructions + coordinator
# prompt and is guarded by its failsafe — a package missing any of the three
# is not dispatch-READY, and until now looked identical to a complete one on
# the index. Coverage is derived from the role-classified listing the page
# already fetches: zero extra API calls.
_DISPATCH_ROLES: tuple[str, ...] = ("instructions", "coordinator", "failsafe")


def _repo_url() -> str:
    return f"https://github.com/{config.OWNER}/{REPO}/tree/main/{ROOT}"


def classify_role(filename: str) -> tuple[str, str]:
    """Map a package filename to ``(role_key, label)``; unmatched → other."""
    base = filename.rsplit("/", 1)[-1].lower()
    for key, label, needle in _ROLE_PATTERNS:
        if needle in base:
            return key, label
    return "other", "other"


def extract_state(meta_text: str) -> str:
    """Best-effort deployed-state line from a package's meta.md body.

    Returns the raw value of the first ``deployed:`` / ``state:`` /
    ``status:``-keyed line (markdown emphasis tolerated), or ``""`` when no
    such line exists — the template renders that as an honest "unknown".
    """
    for line in (meta_text or "").splitlines():
        m = _STATE_LINE_RE.match(line)
        if m:
            value = m.group(2).strip().strip("*").strip()
            # A markdown-table or badge-line artifact is not a state value.
            if value and not set(value) <= set("-| "):
                return value
    return ""


def extract_env(meta_text: str) -> str:
    """Best-effort environment-name line from a package's meta.md body.

    Same contract as :func:`extract_state`: the first ``environment:`` /
    ``env-name:``-keyed line's raw value, or ``""`` when absent — the
    template renders that as an honest "unknown", never a guess.
    """
    for line in (meta_text or "").splitlines():
        m = _ENV_LINE_RE.match(line)
        if m:
            value = m.group(1).strip().strip("*").strip("`").strip()
            if value and not set(value) <= set("-| "):
                return value
    return ""


def extract_project_url(meta_text: str) -> str:
    """First recorded claude.ai Project URL in meta.md, or ``""`` (absent =
    "none recorded" on the page — a link is only ever shown when the registry
    actually carries one)."""
    m = _PROJECT_URL_RE.search(meta_text or "")
    return m.group(0).rstrip(".") if m else ""


def is_stub(state: str, meta_text: str) -> bool:
    """Tolerant retired/merged/stub detection — fail-ACTIVE by design.

    True when the extracted state value says retired/merged/stub/archived,
    or an early meta.md body line uses the unambiguous spellings
    ("retired", "stub", "merged into"). Anything else — including no meta
    at all — is active: a real seat is never hidden on a guess.
    """
    if state and _STUB_STATE_RE.search(state):
        return True
    scanned = 0
    for line in (meta_text or "").splitlines():
        if not line.strip():
            continue
        if _STUB_BODY_RE.search(line):
            return True
        scanned += 1
        if scanned >= _STUB_BODY_SCAN_LINES:
            break
    return False


def role_coverage(files: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """The seat's role-coverage chip row: one entry per dispatch-critical
    role (:data:`_DISPATCH_ROLES`) with ``present`` derived from the
    package's already-role-classified file listing — never from an extra
    fetch. ``label`` carries the human role name for chip tooltips.
    """
    have = {f.get("role") for f in files}
    labels = {key: label for key, label, _ in _ROLE_PATTERNS}
    return [
        {"role": role, "label": labels[role], "present": role in have}
        for role in _DISPATCH_ROLES
    ]


def start_rank(name: str) -> int:
    """The owner's dispatch-order slot for a package name (lowercased,
    ``_``→``-``); unmatched names rank after every matched one."""
    norm = (name or "").strip().lower().replace("_", "-")
    for i, aliases in enumerate(_START_ORDER):
        if norm in aliases:
            return i
    return len(_START_ORDER)


async def _list_dir(path: str, refresh: bool = False) -> dict[str, Any]:
    """Contents-API listing of one directory (result dict, honest on failure)."""
    return await github.repo_api(REPO, f"/contents/{path}", refresh=refresh)


async def _build_package(
    name: str, path: str, refresh: bool = False
) -> dict[str, Any]:
    """One ``projects/<repo>/`` package card: file roles + rendered meta.md."""
    out: dict[str, Any] = {
        "name": name,
        "path": path,
        "github_url": f"https://github.com/{config.OWNER}/{REPO}/tree/main/{path}",
        "detail_url": f"/projects/{name}",
        "files": [],
        "error": None,
        "meta_html": "",
        "meta_error": None,
        "state": "",
        "stub": False,
        # Role-coverage chips: [] / None until the listing succeeds — an
        # unlistable package renders NO chips, never a fabricated ✗.
        "coverage": [],
        "dispatch_ready": None,
    }
    listing = await _list_dir(path, refresh=refresh)
    if not (listing["ok"] and isinstance(listing["data"], list)):
        out["error"] = listing.get("error") or f"HTTP {listing.get('status')}"
        return out

    meta_path: Optional[str] = None
    for entry in listing["data"][:MAX_FILES_PER_PACKAGE]:
        if entry.get("type") != "file":
            continue
        fpath = entry.get("path", "")
        fname = fpath.rsplit("/", 1)[-1]
        role, label = classify_role(fname)
        out["files"].append(
            {
                "name": fname,
                "path": fpath,
                "role": role,
                "label": label,
                "github_url": _blob_url(fpath),
            }
        )
        if role == "meta" and fname.lower().endswith(".md") and meta_path is None:
            meta_path = fpath

    # Role-first ordering (meta, instructions, coordinator, setup, failsafe,
    # routine, then other) so every card reads the same way.
    rank = {key: i for i, (key, _, _) in enumerate(_ROLE_PATTERNS)}
    out["files"].sort(key=lambda f: (rank.get(f["role"], 99), f["name"].lower()))

    # Seat role-coverage chips (instructions / coordinator / failsafe) from
    # the listing just classified — dispatch-READY only when all three exist.
    out["coverage"] = role_coverage(out["files"])
    out["dispatch_ready"] = all(c["present"] for c in out["coverage"])

    if meta_path:
        meta = await github.fetch_file(REPO, meta_path, refresh=refresh)
        if meta["ok"] and isinstance(meta["data"], str):
            out["meta_html"] = journal.render_markdown(meta["data"])
            out["state"] = extract_state(meta["data"])
            out["stub"] = is_stub(out["state"], meta["data"])
        else:
            out["meta_error"] = meta.get("error") or f"HTTP {meta.get('status')}"
    return out


async def overview(refresh: bool = False) -> dict[str, Any]:
    """The rendered projects registry, or an honest degraded state.

    ``state``: ``ok`` | ``empty`` (the ``projects/`` folder does not exist
    upstream yet — the expected launch state while the registry lands) |
    ``not-configured`` (GITHUB_TOKEN unset and the fetch failed) |
    ``unavailable`` (token set, fetch failed). Never raises for upstream
    failures — the route always renders 200.
    """
    token_set = bool(config.GITHUB_TOKEN)
    out: dict[str, Any] = {
        "state": "ok",
        "reason": "",
        "token_set": token_set,
        "repo_url": _repo_url(),
        "packages": [],
        "root_files": [],
    }

    root = await _list_dir(ROOT, refresh=refresh)
    if not (root["ok"] and isinstance(root["data"], list)):
        reason = root.get("error") or f"HTTP {root.get('status')}"
        if root.get("status") == 404:
            # The registry folder has not landed upstream yet — an absence,
            # not an error (the dispatch says it is being created right now).
            out["state"] = "empty"
            out["reason"] = (
                f"{config.OWNER}/{REPO} has no `{ROOT}/` directory yet — the "
                "registry is still landing upstream; this page fills in the "
                "moment it exists"
            )
        elif not token_set:
            out["state"] = "not-configured"
            out["reason"] = (
                "GITHUB_TOKEN is not set on this service and the "
                f"{config.OWNER}/{REPO} `{ROOT}/` listing failed "
                f"(fetch: {reason})"
            )
        else:
            out["state"] = "unavailable"
            out["reason"] = reason
        return out

    dirs: list[tuple[str, str]] = []
    for entry in root["data"]:
        if entry.get("type") == "dir":
            dirs.append((entry.get("name", ""), entry.get("path", "")))
        elif entry.get("type") == "file":
            fpath = entry.get("path", "")
            out["root_files"].append(
                {
                    "name": fpath.rsplit("/", 1)[-1],
                    "path": fpath,
                    "github_url": _blob_url(fpath),
                }
            )
    dirs = [(n, p) for n, p in dirs if n and p][:MAX_PACKAGES]

    if not dirs and not out["root_files"]:
        out["state"] = "empty"
        out["reason"] = (
            f"the `{ROOT}/` directory exists but holds no packages yet — the "
            "registry is still landing upstream"
        )
        return out

    packages = list(
        await asyncio.gather(
            *[_build_package(n, p, refresh=refresh) for n, p in sorted(dirs)]
        )
    )
    # Dispatch order: active seats first (owner start order, unmatched names
    # after, alphabetically), retired/merged stubs last — the template splits
    # on ``stub`` to collapse them under a <details>.
    packages.sort(
        key=lambda p: (p["stub"], start_rank(p["name"]), p["name"].lower())
    )
    out["packages"] = packages
    return out


async def detail(name: str, refresh: bool = False) -> dict[str, Any]:
    """One seat's dispatch screen: the package's recognized role files with
    their FULL raw content (copy-ready), plus best-effort meta fields. Role
    files carry the canonical shared prompt-artifact dict (``artifact`` key,
    ORDER 015 — one fetch/render/copy path with /prompts); ``text`` /
    ``fetch_error`` mirror it for meta extraction and existing consumers.

    ``state``: ``ok`` | ``not-found`` (the name is not a directory in the
    live registry listing — the route's ONLY 404; this doubles as the
    path-traversal gate) | ``empty`` / ``not-configured`` / ``unavailable``
    (the registry listing itself failed — same honest ladder as
    :func:`overview`, rendered as a 200 banner page). Per-file fetch
    failures degrade per-cell (``fetch_error``), never fabricate content.
    """
    token_set = bool(config.GITHUB_TOKEN)
    out: dict[str, Any] = {
        "state": "ok",
        "reason": "",
        "token_set": token_set,
        "name": name,
        "repo_url": _repo_url(),
        "package": None,
        "env": "",
        "project_url": "",
        "failsafe": None,
        "ttl": config.CACHE_TTL_SECONDS,
    }
    if not _SAFE_PKG_RE.match(name or "") or ".." in name:
        out["state"] = "not-found"
        out["reason"] = "not a registry package name"
        return out

    root = await _list_dir(ROOT, refresh=refresh)
    if not (root["ok"] and isinstance(root["data"], list)):
        reason = root.get("error") or f"HTTP {root.get('status')}"
        if root.get("status") == 404:
            out["state"] = "empty"
            out["reason"] = (
                f"{config.OWNER}/{REPO} has no `{ROOT}/` directory yet — the "
                "registry is still landing upstream"
            )
        elif not token_set:
            out["state"] = "not-configured"
            out["reason"] = (
                "GITHUB_TOKEN is not set on this service and the "
                f"{config.OWNER}/{REPO} `{ROOT}/` listing failed "
                f"(fetch: {reason})"
            )
        else:
            out["state"] = "unavailable"
            out["reason"] = reason
        return out

    # The registry listing is the allowlist: a name that is not one of its
    # directories is 404, full stop — no path is ever built from raw input.
    path = ""
    for entry in root["data"]:
        if entry.get("type") == "dir" and entry.get("name") == name:
            path = entry.get("path", "")
            break
    if not path:
        out["state"] = "not-found"
        out["reason"] = f"`{name}` is not a package in the `{ROOT}/` registry"
        return out

    pkg = await _build_package(name, path, refresh=refresh)
    out["package"] = pkg
    if pkg["error"]:
        return out

    # Full content for every recognized role file (the copy-ready blocks) via
    # the shared prompt-artifact path (ORDER 015) — the SAME fetch+parse
    # model /prompts renders through; "other" files stay link-only, listed
    # honestly. meta.md re-uses the TTL cache warmed by _build_package.
    role_files = [f for f in pkg["files"] if f["role"] != "other"]
    fetched = await asyncio.gather(
        *[
            prompt_artifacts.fetch_artifact(f["path"], f["label"], refresh=refresh)
            for f in role_files
        ]
    )
    for f in pkg["files"]:
        f["artifact"] = None
        f["text"] = None
        f["fetch_error"] = None
    for f, art in zip(role_files, fetched):
        f["artifact"] = art
        f["text"] = art["text"]
        f["fetch_error"] = None if art["ok"] else art["error"]
    for i, f in enumerate(pkg["files"]):
        f["anchor"] = f"file-{i}"

    meta_file = next(
        (f for f in pkg["files"] if f["role"] == "meta" and f["text"]), None
    )
    if meta_file:
        out["env"] = extract_env(meta_file["text"])
        out["project_url"] = extract_project_url(meta_file["text"])
    out["failsafe"] = next(
        (f for f in pkg["files"] if f["role"] == "failsafe"), None
    )
    return out
