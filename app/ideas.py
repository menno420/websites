"""Idea-backlog view: the ``docs/ideas/`` conveyor across every fleet repo that
keeps one — the owner's "what's queued to build" glance.

Each repo's ideas directory is listed once (cache-backed contents API); the most
recent files are enriched with a real parsed title + one-line summary (a bounded
content fan-out, cached). Repos without an ideas directory show nothing for that
repo — that is an absence, not an error. Detail rendering reuses the existing
in-app markdown file view (``/journal/{repo}/file``) plus a GitHub deep-link.
"""

from __future__ import annotations

import asyncio
import re
from typing import Any

from . import config, github

OWNER = config.OWNER

IDEAS_DIR = "docs/ideas"
# How many newest idea files per repo to enrich with a parsed title + summary
# (each costs one cache-backed content fetch). The rest are surfaced as a count
# with a browse-all link so the page stays fast even for the 200+ superbot set.
ENRICH_LIMIT = 24
SUMMARY_MAX = 200

_FRONTMATTER = re.compile(r"^---\s*\n.*?\n---\s*\n", re.DOTALL)

# The idea lifecycle states the fleet's backlog convention uses
# (docs/ideas/README.md: captured → planned → built → retired). An idea file
# whose front-matter carries no recognizable `state:` counts as `unstated` —
# an honest bucket, never guessed into a lifecycle stage.
IDEA_STATES = ("captured", "planned", "built", "retired")
_STATE_RE = re.compile(r"^state:\s*([A-Za-z-]+)\s*$", re.MULTILINE)


def extract_state(text: str) -> str:
    """The idea's lifecycle state from its front-matter, or "" (unstated).

    Only the front-matter block is searched (a body sentence mentioning
    "state:" must not classify the idea), and only the four known lifecycle
    tokens count — anything else is unstated, honestly.
    """
    m = _FRONTMATTER.match(text or "")
    if not m:
        return ""
    sm = _STATE_RE.search(m.group(0))
    if sm and sm.group(1).lower() in IDEA_STATES:
        return sm.group(1).lower()
    return ""


def _title_from_filename(name: str) -> str:
    """Human title from a `some-idea-name-2026-07-09.md` filename: drop the .md
    and a trailing ISO date, turn dashes into spaces. Always available, so a
    file whose content can't be fetched still gets a readable label."""
    stem = re.sub(r"\.md$", "", name)
    stem = re.sub(r"-?\d{4}-\d{2}-\d{2}$", "", stem)
    return stem.replace("-", " ").strip() or name


def parse_idea(text: str, fallback_title: str) -> dict[str, str]:
    """Parse an idea markdown file into a title + one-line summary.

    Title: the first ``# H1`` heading (a leading ``Idea:`` label is stripped);
    falls back to the filename-derived title. Summary: a ``**One line:**`` marker
    if present, else the first real paragraph that is not a heading, blockquote,
    frontmatter, table, or list line. Trimmed to a single line.
    """
    body = _FRONTMATTER.sub("", text, count=1)
    lines = body.splitlines()

    title = fallback_title
    for ln in lines:
        s = ln.strip()
        if s.startswith("# "):
            title = re.sub(r"^#\s+", "", s)
            title = re.sub(r"^Idea:\s*", "", title, flags=re.I)
            # Drop inline-code backticks so the display title reads cleanly.
            title = title.replace("`", "").strip()
            break

    summary = ""
    # Preferred: an explicit "**One line:**" marker anywhere in the file.
    m = re.search(r"\*\*One[\s-]?line:\*\*\s*(.+)", body, flags=re.I)
    if m:
        summary = m.group(1)
    else:
        for ln in lines:
            s = ln.strip()
            if not s:
                continue
            # Skip structural lines, but keep a `**bold:**` metadata paragraph —
            # only true list items (dash/star/plus + space) are skipped.
            if s.startswith(("#", ">", "|", "`", "<")):
                continue
            if re.match(r"^[-*+]\s", s):
                continue
            summary = s
            break

    # Collapse markdown emphasis noise and whitespace into one clean line.
    summary = re.sub(r"[*_`]+", "", summary).replace("\n", " ").strip()
    summary = re.sub(r"\s+", " ", summary)
    if len(summary) > SUMMARY_MAX:
        summary = summary[: SUMMARY_MAX - 1].rstrip() + "…"
    return {"title": title.strip() or fallback_title, "summary": summary}


def _gh_blob(repo: str, path: str) -> str:
    return f"https://github.com/{OWNER}/{repo}/blob/main/{path}"


async def repo_ideas(repo: str, refresh: bool = False) -> dict[str, Any]:
    """List one repo's ``docs/ideas/`` backlog.

    Returns the listing result (for an honest banner), the total idea count, and
    the enriched newest ideas (title + one-line summary + deep-links). README.md
    is the index, not an idea, so it is excluded from the backlog.
    """
    res = await github.repo_api(repo, f"/contents/{IDEAS_DIR}", refresh=refresh)

    has_dir = res["ok"] and isinstance(res["data"], list)
    # A 404 is a legitimate "this repo has no ideas dir" — NOT an error banner.
    missing = res["status"] == 404
    listing_error = None
    if not has_dir and not missing:
        listing_error = res.get("error") or f"HTTP {res.get('status')}"

    files: list[dict] = []
    if has_dir:
        files = [
            f
            for f in res["data"]
            if f.get("type") == "file"
            and f.get("name", "").endswith(".md")
            and f.get("name") != "README.md"
        ]
        # Newest first: idea files are date-suffixed, so filename sort works and
        # is stable for the undated few.
        files.sort(key=lambda f: f.get("name", ""), reverse=True)

    total = len(files)
    to_enrich = files[:ENRICH_LIMIT]
    fetched = await asyncio.gather(
        *[github.fetch_file(repo, f["path"], refresh=refresh) for f in to_enrich]
    )

    ideas: list[dict] = []
    state_counts: dict[str, int] = {}
    for f, fres in zip(to_enrich, fetched):
        fallback = _title_from_filename(f["name"])
        if fres["ok"] and isinstance(fres["data"], str):
            parsed = parse_idea(fres["data"], fallback)
            title, summary, degraded = parsed["title"], parsed["summary"], False
            state = extract_state(fres["data"])
        else:
            title, summary, degraded = fallback, "", True
            state = ""
        state_counts[state or "unstated"] = (
            state_counts.get(state or "unstated", 0) + 1
        )
        ideas.append(
            {
                "repo": repo,
                "name": f["name"],
                "path": f["path"],
                "title": title,
                "summary": summary,
                "state": state,  # "" = unstated (honest)
                "degraded": degraded,
                "github_url": f.get("html_url") or _gh_blob(repo, f["path"]),
                "internal_url": f"/journal/{repo}/file?path={f['path']}",
            }
        )

    return {
        "repo": repo,
        "github_url": f"https://github.com/{OWNER}/{repo}/tree/main/{IDEAS_DIR}",
        "has_dir": has_dir,
        "missing": missing,
        "listing_error": listing_error,
        "total": total,
        "shown": len(ideas),
        "more": max(0, total - len(ideas)),
        "ideas": ideas,
        # Conveyor-health counts over the ENRICHED (newest) files only — the
        # only ones whose content was fetched; honest scope, labeled on the
        # page ("of the newest N"). "unstated" = no recognizable front-matter
        # state, never guessed.
        "state_counts": state_counts,
    }


async def overview(
    refresh: bool = False, state: str | None = None
) -> list[dict]:
    """Every repo's ideas; ``state`` filters the DISPLAYED ideas to one
    lifecycle state (counts stay full — the filter narrows the list, never
    the truth). An unknown state value shows nothing and flags itself."""
    repos = list(
        await asyncio.gather(*[repo_ideas(r, refresh=refresh) for r in config.REPOS])
    )
    wanted = (state or "").strip().lower() or None
    for r in repos:
        r["state_filter"] = wanted
        r["state_filter_known"] = wanted is None or wanted in (
            IDEA_STATES + ("unstated",)
        )
        if wanted and r["state_filter_known"]:
            r["ideas"] = [
                i for i in r["ideas"]
                if (i["state"] or "unstated") == wanted
            ]
    return repos
