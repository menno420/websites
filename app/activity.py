"""Cross-repo activity timeline: recent pull requests across every fleet repo,
merged into ONE reverse-chronological stream and deep-linked back to GitHub.

Reuses the shared TTL-cached github client (github.repo_api) — the same layer
the readiness board and journal browser ride, so a warm cache serves this page
for free. Every per-repo fetch carries its own result, so one failing repo
degrades to an honest banner row instead of 500ing the whole timeline.
"""

from __future__ import annotations

import asyncio
from typing import Any

from . import config, github

OWNER = config.OWNER

# How many recent PRs to pull per repo before merging into the combined stream,
# and how many combined items to render. Bounded so the page never fans out to
# hundreds of items; all fetches ride the server-side TTL cache in github.py.
PER_REPO_LIMIT = 15
TIMELINE_LIMIT = 60


def _state_of(pr: dict) -> str:
    """Collapse a PR into one display state: merged | open | draft | closed."""
    if pr.get("merged_at"):
        return "merged"
    if pr.get("state") == "closed":
        return "closed"
    if pr.get("draft"):
        return "draft"
    return "open"


def _timestamp_of(pr: dict) -> str:
    """The moment that places this PR on the timeline: merge time if merged,
    else last-updated time. Empty string sorts last (honest, never faked)."""
    return pr.get("merged_at") or pr.get("updated_at") or pr.get("created_at") or ""


async def repo_activity(repo: str, refresh: bool = False) -> dict[str, Any]:
    """Recent PRs for one repo as normalized timeline items, plus the raw
    fetch result so the caller can render a per-repo error banner honestly."""
    res = await github.repo_api(
        repo,
        f"/pulls?state=all&per_page={PER_REPO_LIMIT}&sort=updated&direction=desc",
        refresh=refresh,
    )
    items: list[dict] = []
    if res["ok"] and isinstance(res["data"], list):
        for p in res["data"]:
            ts = _timestamp_of(p)
            items.append(
                {
                    "repo": repo,
                    "kind": "pr",
                    "number": p.get("number"),
                    "title": p.get("title") or "",
                    "author": (p.get("user") or {}).get("login") or "",
                    "state": _state_of(p),
                    "ts": ts,
                    "date": ts[:10],
                    "time": ts[11:16],
                    "url": p.get("html_url")
                    or f"https://github.com/{OWNER}/{repo}/pull/{p.get('number')}",
                }
            )
    return {"repo": repo, "items": items, "result": res}


async def timeline(refresh: bool = False) -> dict[str, Any]:
    """One reverse-chronological stream across every fleet repo.

    Fetches each repo's recent PRs concurrently (cache-backed), merges them,
    sorts newest-first by merge/update time, and caps the combined length.
    Fetch failures are collected into ``errors`` so the UI shows an honest
    banner per repo rather than silently dropping it.
    """
    per_repo = await asyncio.gather(
        *[repo_activity(r, refresh=refresh) for r in config.REPOS]
    )

    items: list[dict] = []
    errors: list[dict] = []
    for pr in per_repo:
        res = pr["result"]
        if not res["ok"]:
            errors.append(
                {
                    "repo": pr["repo"],
                    "status": res.get("status"),
                    "error": res.get("error") or f"HTTP {res.get('status')}",
                    "url": f"https://github.com/{OWNER}/{pr['repo']}/pulls",
                }
            )
        items.extend(pr["items"])

    # Newest first. Empty timestamps ("") sort to the bottom naturally.
    items.sort(key=lambda i: i["ts"], reverse=True)
    return {
        "items": items[:TIMELINE_LIMIT],
        "errors": errors,
        "repos_ok": [pr["repo"] for pr in per_repo if pr["result"]["ok"]],
        "total": len(items),
    }
