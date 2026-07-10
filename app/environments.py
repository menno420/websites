"""Environments registry view (/environments): render fleet-manager's
``environments/`` directory read-only.

ORDER 005 half (2): the owner creates/edits claude.ai environments by hand and
needs the setup scripts + env-var schemas viewable and copyable in one place.
The manager's repo STORES the registry (``menno420/fleet-manager`` →
``environments/``: README, templates with setup scripts, env-var schemas,
specs); this site only RENDERS it. Secrets are never present by design — the
registry stores names/placeholders only (fleet-manager PR #5).

fleet-manager is PRIVATE: agent sessions cannot read it, and the deployed
control-plane can only read it at runtime via ``GITHUB_TOKEN`` — which may be
unset. Degradation is honest: ``not-configured`` (token unset — the documented
production state until the owner mints the PAT) or ``unavailable`` (fetch
failed with the reason surfaced); never a 500, never fabricated files.

Markdown files render via the sanitized ``journal.render_markdown``; everything
else (setup scripts, schemas) renders as an escaped code block. The template
attaches a copy-to-clipboard button to every code block. Same TTL-cached
``github`` layer as every other page.
"""

from __future__ import annotations

import asyncio
from typing import Any

from . import config, github, journal

REPO = "fleet-manager"
ROOT = "environments"

# Safety bounds: one level of subdirectories, a sane number of files — the
# registry is a handful of templates/specs, not an arbitrary tree.
MAX_FILES = 40

# Extensions rendered as sanitized markdown; everything else is an escaped
# code block (setup-universal.sh, env-var schemas, yaml, …).
_MD_EXTS = (".md", ".markdown")


def _repo_url() -> str:
    return f"https://github.com/{config.OWNER}/{REPO}/tree/main/{ROOT}"


def _sort_rank(path: str) -> tuple:
    """README first, then root files, then subdirectory files — stable A→Z."""
    name = path.rsplit("/", 1)[-1].lower()
    depth = path.count("/")
    return (0 if name == "readme.md" else 1, depth, path.lower())


async def _list_dir(path: str, refresh: bool = False) -> dict[str, Any]:
    """Contents-API listing of one directory (result dict, honest on failure)."""
    return await github.repo_api(REPO, f"/contents/{path}", refresh=refresh)


async def _collect_paths(refresh: bool = False) -> tuple[list[str], list[str]]:
    """File paths under ROOT (one subdir level deep) + per-subdir error notes."""
    root = await _list_dir(ROOT, refresh=refresh)
    if not (root["ok"] and isinstance(root["data"], list)):
        # Signal the caller with the raw result via an exception-free contract:
        # an empty path list + the root error note.
        reason = root.get("error") or f"HTTP {root.get('status')}"
        raise LookupError(reason)

    files: list[str] = []
    subdirs: list[str] = []
    for entry in root["data"]:
        if entry.get("type") == "file":
            files.append(entry.get("path", ""))
        elif entry.get("type") == "dir":
            subdirs.append(entry.get("path", ""))

    errors: list[str] = []
    listings = await asyncio.gather(
        *[_list_dir(d, refresh=refresh) for d in subdirs]
    )
    for subdir, listing in zip(subdirs, listings):
        if listing["ok"] and isinstance(listing["data"], list):
            files.extend(
                e.get("path", "")
                for e in listing["data"]
                if e.get("type") == "file"
            )
        else:
            reason = listing.get("error") or f"HTTP {listing.get('status')}"
            errors.append(f"{subdir}/ could not be listed ({reason})")
    files = [f for f in files if f]
    files.sort(key=_sort_rank)
    return files[:MAX_FILES], errors


async def _fetch_one(path: str, refresh: bool = False) -> dict[str, Any]:
    """One registry file, rendered: markdown → sanitized HTML, else raw text
    for an escaped copyable code block. Per-file failures degrade per-cell."""
    res = await github.fetch_file(REPO, path, refresh=refresh)
    name = path[len(ROOT) + 1 :] if path.startswith(ROOT + "/") else path
    out: dict[str, Any] = {
        "path": path,
        "name": name,
        "kind": "markdown" if path.lower().endswith(_MD_EXTS) else "code",
        "body_html": "",
        "text": "",
        "error": None,
        "github_url": f"https://github.com/{config.OWNER}/{REPO}/blob/main/{path}",
    }
    if res["ok"] and isinstance(res["data"], str):
        if out["kind"] == "markdown":
            out["body_html"] = journal.render_markdown(res["data"])
        else:
            out["text"] = res["data"]
    else:
        out["error"] = res.get("error") or f"HTTP {res.get('status')}"
    return out


async def overview(refresh: bool = False) -> dict[str, Any]:
    """The rendered registry, or an honest degraded state.

    ``state``: ``ok`` | ``not-configured`` (GITHUB_TOKEN unset) |
    ``unavailable`` (token present, fetch failed). Never raises for upstream
    failures — the route always renders 200.
    """
    token_set = bool(config.GITHUB_TOKEN)
    out: dict[str, Any] = {
        "state": "ok",
        "reason": "",
        "token_set": token_set,
        "repo_url": _repo_url(),
        "files": [],
        "listing_errors": [],
    }
    try:
        paths, errors = await _collect_paths(refresh=refresh)
    except LookupError as exc:
        reason = str(exc)
        if not token_set:
            out["state"] = "not-configured"
            out["reason"] = (
                "GITHUB_TOKEN is not set on this service, and "
                f"{config.OWNER}/{REPO} is private — the environments "
                f"registry cannot be read (fetch: {reason})"
            )
        else:
            out["state"] = "unavailable"
            out["reason"] = reason
        return out

    out["listing_errors"] = errors
    out["files"] = list(
        await asyncio.gather(*[_fetch_one(p, refresh=refresh) for p in paths])
    )
    return out
