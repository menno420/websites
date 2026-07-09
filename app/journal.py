"""Journal browser: session logs, decision ledgers, question routers, PR and
commit history per repo — fetched live, deep-linked back to GitHub, never
narrated or summarized."""

from __future__ import annotations

import asyncio
from typing import Any

from . import config, github

OWNER = config.OWNER


def _gh(repo: str, tail: str = "") -> str:
    return f"https://github.com/{OWNER}/{repo}{tail}"


async def repo_journal(repo: str, refresh: bool = False) -> dict[str, Any]:
    cfg = config.REPOS[repo]["journal"]

    tasks = {
        "pulls": github.repo_api(
            repo,
            "/pulls?state=all&per_page=15&sort=updated&direction=desc",
            refresh=refresh,
        ),
        "commits": github.repo_api(repo, "/commits?per_page=15", refresh=refresh),
    }
    if cfg["sessions_dir"]:
        tasks["sessions"] = github.repo_api(
            repo, f"/contents/{cfg['sessions_dir']}", refresh=refresh
        )
    keys = list(tasks)
    results = dict(zip(keys, await asyncio.gather(*[tasks[k] for k in keys])))

    sessions = []
    sessions_res = results.get("sessions")
    if sessions_res and sessions_res["ok"] and isinstance(sessions_res["data"], list):
        files = [
            f
            for f in sessions_res["data"]
            if f.get("type") == "file" and f.get("name", "").endswith(".md")
        ]
        # session logs are date-prefixed YYYY-MM-DD-<slug>.md -> newest first
        for f in sorted(files, key=lambda x: x.get("name", ""), reverse=True):
            sessions.append(
                {
                    "name": f["name"],
                    "path": f["path"],
                    "github_url": f.get("html_url")
                    or _gh(repo, f"/blob/main/{f['path']}"),
                }
            )

    docs = [
        {
            "label": label,
            "path": path,
            "github_url": _gh(repo, f"/blob/main/{path}"),
        }
        for (label, path) in cfg["docs"]
    ]

    pulls = []
    pr_res = results["pulls"]
    if pr_res["ok"] and isinstance(pr_res["data"], list):
        for p in pr_res["data"]:
            state = p.get("state")
            if p.get("merged_at"):
                state = "merged"
            pulls.append(
                {
                    "number": p.get("number"),
                    "title": p.get("title"),
                    "state": state,
                    "created_at": (p.get("created_at") or "")[:10],
                    "url": p.get("html_url"),
                    "branch": (p.get("head") or {}).get("ref", ""),
                }
            )

    commits = []
    c_res = results["commits"]
    if c_res["ok"] and isinstance(c_res["data"], list):
        for c in c_res["data"]:
            msg = ((c.get("commit") or {}).get("message") or "").splitlines()[0]
            commits.append(
                {
                    "sha": (c.get("sha") or "")[:8],
                    "message": msg,
                    "date": (((c.get("commit") or {}).get("committer") or {}).get(
                        "date"
                    )
                    or "")[:10],
                    "url": c.get("html_url"),
                }
            )

    return {
        "repo": repo,
        "github_url": _gh(repo),
        "note": cfg["note"],
        "has_sessions": bool(cfg["sessions_dir"]),
        "sessions_result": sessions_res,
        "sessions": sessions,
        "docs": docs,
        "pulls": pulls,
        "pulls_result": pr_res,
        "commits": commits,
        "commits_result": c_res,
    }


async def overview(refresh: bool = False) -> list[dict]:
    return list(
        await asyncio.gather(
            *[repo_journal(r, refresh=refresh) for r in config.REPOS]
        )
    )
