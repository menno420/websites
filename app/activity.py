"""Cross-repo activity timeline: recent pull requests across every fleet repo,
merged into ONE reverse-chronological stream and deep-linked back to GitHub.

Reuses the shared TTL-cached github client (github.repo_api) — the same layer
the readiness board and journal browser ride, so a warm cache serves this page
for free. Every per-repo fetch carries its own result, so one failing repo
degrades to an honest banner row instead of 500ing the whole timeline.
"""

from __future__ import annotations

import asyncio
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any

from . import config, github

ATOM_NS = "http://www.w3.org/2005/Atom"
FEED_TITLE = "SuperBot fleet activity"

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


# --------------------------------------------------------------------------- #
# Atom 1.0 serializer — a second serializer over the exact timeline() list, so a
# reader/webhook can subscribe to fleet activity instead of polling /activity.
# Rides the same TTL-cached data source (no second fetch path). All text/attrs
# are escaped by ElementTree; we never hand-concatenate XML.
# --------------------------------------------------------------------------- #


def _now_rfc3339() -> str:
    """Feed-generation time in RFC3339 (Atom's required timestamp form). Used
    only as a *clearly-derived* fallback for the feed-level ``updated`` and the
    diagnostic entry when there are no real dated entries — never to fake a PR."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _el(parent: ET.Element, tag: str, text: str | None = None) -> ET.Element:
    """Namespaced Atom child element; ElementTree escapes ``text`` for us."""
    child = ET.SubElement(parent, f"{{{ATOM_NS}}}{tag}")
    if text is not None:
        child.text = text
    return child


def _summary_of(item: dict) -> str:
    """Short human summary for an entry: repo + collapsed state + author."""
    who = f" by {item['author']}" if item.get("author") else ""
    return f"{item['repo']} · {item['state']} pull request{who}"


def atom_feed(data: dict[str, Any], self_url: str, alternate_url: str) -> str:
    """Render a timeline() result as a valid Atom 1.0 feed string.

    Each PR with a real timestamp becomes an ``<entry>`` (title = ``repo #num
    title``, id = the PR's GitHub URL, updated = its merge/update time, a link to
    GitHub, author, and a short summary). Entries without a timestamp are omitted
    (honest — never dated with an invented value). If nothing dated is available
    the feed still validates: it carries one diagnostic entry noting the empty /
    errored state, timestamped with the clearly-derived generation time.
    """
    ET.register_namespace("", ATOM_NS)
    feed = ET.Element(f"{{{ATOM_NS}}}feed")

    entries = [it for it in data.get("items", []) if it.get("ts")]
    # Items arrive newest-first, so entries[0] is the newest dated one.
    feed_updated = entries[0]["ts"] if entries else _now_rfc3339()

    _el(feed, "title", FEED_TITLE)
    _el(feed, "id", self_url)
    _el(feed, "updated", feed_updated)
    self_link = _el(feed, "link")
    self_link.set("rel", "self")
    self_link.set("type", "application/atom+xml")
    self_link.set("href", self_url)
    alt_link = _el(feed, "link")
    alt_link.set("rel", "alternate")
    alt_link.set("type", "text/html")
    alt_link.set("href", alternate_url)

    if entries:
        for it in entries:
            entry = _el(feed, "entry")
            _el(entry, "title", f"{it['repo']} #{it['number']} {it['title']}".strip())
            _el(entry, "id", it["url"])
            _el(entry, "updated", it["ts"])
            link = _el(entry, "link")
            link.set("rel", "alternate")
            link.set("type", "text/html")
            link.set("href", it["url"])
            if it.get("author"):
                author = _el(entry, "author")
                _el(author, "name", it["author"])
            _el(entry, "summary", _summary_of(it))
    else:
        # Honest degradation: a valid feed with one diagnostic entry rather than a
        # malformed feed or an invented PR.
        errors = data.get("errors", [])
        if errors:
            detail = "; ".join(
                f"{e['repo']}: {e.get('error') or 'HTTP ' + str(e.get('status'))}"
                for e in errors
            )
            summary = f"Fleet activity could not be fetched — {detail}"
        else:
            summary = "No recent pull requests across the fleet."
        gen = _now_rfc3339()
        entry = _el(feed, "entry")
        _el(entry, "title", FEED_TITLE + " — status")
        # Day-stable id so readers dedupe a persisting empty/error state per day.
        _el(entry, "id", f"{self_url}#status-{gen[:10]}")
        _el(entry, "updated", gen)
        _el(entry, "summary", summary)

    body = ET.tostring(feed, encoding="unicode")
    return '<?xml version="1.0" encoding="utf-8"?>\n' + body
