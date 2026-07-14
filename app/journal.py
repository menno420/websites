"""Journal browser: session logs, decision ledgers, question routers, PR and
commit history per repo — fetched live, deep-linked back to GitHub, never
narrated or summarized."""

from __future__ import annotations

import asyncio
import html as _html
import posixpath
import re
from typing import Any, Optional
from urllib.parse import quote as _urlquote, urlsplit as _urlsplit

from . import config, github

OWNER = config.OWNER

# Cross-repo search scans the most-recent N session logs per repo (plus every
# configured ledger/router doc). Bounded so a search never fans out to hundreds
# of fetches; all fetches ride the server-side TTL cache in github.py.
SEARCH_SESSION_LIMIT = 25
SNIPPET_RADIUS = 90

# Markdown output allow-list for bleach sanitization (defense-in-depth: the docs
# are trusted repo content, but we still render safely). Covers everything the
# markdown extensions below can emit.
_ALLOWED_TAGS = [
    "p", "br", "hr", "pre", "code", "blockquote", "span", "div",
    "h1", "h2", "h3", "h4", "h5", "h6",
    "ul", "ol", "li", "dl", "dt", "dd",
    "strong", "em", "b", "i", "del", "sub", "sup",
    "a", "img",
    "table", "thead", "tbody", "tr", "th", "td",
]
_ALLOWED_ATTRS = {
    "a": ["href", "title", "id"],
    "img": ["src", "alt", "title"],
    "th": ["align"],
    "td": ["align"],
    "code": ["class"],
    "span": ["class"],
    "div": ["class"],
    "h1": ["id"], "h2": ["id"], "h3": ["id"], "h4": ["id"], "h5": ["id"], "h6": ["id"],
}


def _gh(repo: str, tail: str = "") -> str:
    return f"https://github.com/{OWNER}/{repo}{tail}"


# --------------------------------------------------------------------------- #
# Relative-link rewriting inside remotely-fetched markdown
#
# The pages here render OTHER repos' markdown documents verbatim (heartbeats on
# /fleet, the fleet-manager ledger on /reviews, environment docs on
# /environments, the /journal file view). Relative links inside that content
# ("README.md", "../docs/x.md", "/control/inbox.md") are the DOCUMENT's links:
# they resolve against this site's origin and 404 for a real visitor — the
# first scheduled smoke-crawl (PR #321) flagged 20 of them live. When the
# document's source (repo + path + ref) is known, rewrite them to absolute
# URLs at the source: github.com blob URLs for links, raw.githubusercontent
# for images. When it is not known (or a ../ path escapes the repo root),
# DE-LINKIFY: keep the link text, drop the anchor — plain text beats a
# guaranteed 404.
#
# The rewrite runs on the FINAL sanitized HTML (after bleach), because
# bleach's serializer normalizes everything — including raw inline HTML the
# markdown passed through — to double-quoted, entity-escaped attributes the
# patterns below can rely on. Only two untrusted inputs reach the rewritten
# attribute: the resolved relative path (percent-quoted) and the fragment
# (HTML-escaped on injection); autoescape/sanitization is otherwise untouched.
# --------------------------------------------------------------------------- #

_A_TAG_RE = re.compile(
    r'<a(?P<pre>[^>]*?)\shref="(?P<href>[^"]*)"(?P<post>[^>]*)>'
    r"(?P<inner>.*?)</a>",
    re.DOTALL | re.IGNORECASE,
)
_IMG_TAG_RE = re.compile(
    r'<img(?P<pre>[^>]*?)\ssrc="(?P<src>[^"]*)"(?P<post>[^>]*?)>',
    re.DOTALL | re.IGNORECASE,
)
_ALT_ATTR_RE = re.compile(r'\balt="([^"]*)"')


def _is_rewritable_relative(url: str) -> bool:
    """True for the relative URLs that need rewriting. Absolute http(s)/mailto
    links, protocol-relative ``//host`` links, and pure ``#fragment`` anchors
    are left untouched (a first path segment containing ``:`` parses as a
    scheme — browsers treat it the same way, so it is not "relative" here)."""
    u = url.strip()
    if not u or u.startswith("#"):
        return False
    try:
        parts = _urlsplit(u)
    except ValueError:  # unparseable — leave it to bleach's verdict
        return False
    return not parts.scheme and not parts.netloc


def _resolve_source_url(
    url: str, source: dict, *, image: bool
) -> Optional[str]:
    """Resolve a relative ``url`` against the fetched document's directory and
    return the absolute URL at the source repo — ``github.com/.../blob/...``
    for links, ``raw.githubusercontent.com/...`` for images — or ``None`` when
    the path escapes the repo root (unresolvable → caller de-linkifies)."""
    path_part, sep, frag = url.partition("#")
    path_part = path_part.strip()
    if path_part.startswith("/"):  # root-relative: against the repo root
        resolved = posixpath.normpath(path_part.lstrip("/"))
    else:  # ./ and ../ and bare: against the fetched file's directory
        base_dir = posixpath.dirname(source["path"])
        resolved = posixpath.normpath(posixpath.join(base_dir, path_part))
    if not resolved or resolved in (".", "..") or resolved.startswith("../"):
        return None
    quoted = _urlquote(resolved, safe="/")
    repo = source["repo"]
    ref = source.get("ref") or "main"
    if image:
        return f"{config.GITHUB_RAW_BASE}/{OWNER}/{repo}/{ref}/{quoted}"
    out = f"https://github.com/{OWNER}/{repo}/blob/{ref}/{quoted}"
    if sep:
        out += "#" + frag
    return out


def _rewrite_relative_urls(html_out: str, source: Optional[dict]) -> str:
    """Rewrite (known source) or de-linkify (unknown source / unresolvable)
    every relative link and image in sanitized rendered-markdown HTML."""

    def sub_a(m: re.Match[str]) -> str:
        href = _html.unescape(m.group("href"))
        if not _is_rewritable_relative(href):
            return m.group(0)
        if source:
            new = _resolve_source_url(href, source, image=False)
            if new:
                return (
                    f'<a{m.group("pre")} href="{_html.escape(new, quote=True)}"'
                    f'{m.group("post")}>{m.group("inner")}</a>'
                )
        return m.group("inner")  # de-linkify: the text survives, the 404 dies

    def sub_img(m: re.Match[str]) -> str:
        src = _html.unescape(m.group("src"))
        if not _is_rewritable_relative(src):
            return m.group(0)
        if source:
            new = _resolve_source_url(src, source, image=True)
            if new:
                return (
                    f'<img{m.group("pre")} src="{_html.escape(new, quote=True)}"'
                    f'{m.group("post")}>'
                )
        alt = _ALT_ATTR_RE.search(m.group(0))
        return alt.group(1) if alt else ""  # alt text (already escaped) or gone

    return _IMG_TAG_RE.sub(sub_img, _A_TAG_RE.sub(sub_a, html_out))


def render_markdown(text: str, source: Optional[dict] = None) -> str:
    """Render trusted repo markdown to sanitized HTML.

    Lazy-imports ``markdown`` (pinned in requirements) so a missing/broken lib
    degrades to an escaped ``<pre>`` block rather than 500ing the whole page.
    When ``bleach`` is present the rendered HTML is sanitized to an allow-list
    (defense-in-depth); when it is absent we return the rendered HTML as-is,
    since the source is trusted repo content.

    ``source`` is the fetched document's location —
    ``{"repo": <repo>, "path": <path>, "ref": <ref, default main>}`` (owner is
    always ``config.OWNER``) — used to rewrite relative links/images to their
    absolute GitHub source URLs. When ``source`` is ``None``, relative links
    are de-linkified instead (they cannot resolve on this origin).
    """
    try:
        import markdown as _md
    except Exception:  # pragma: no cover - markdown is pinned in requirements
        return f"<pre>{_html.escape(text)}</pre>"
    rendered = _md.markdown(
        text,
        extensions=["fenced_code", "tables", "sane_lists"],
        output_format="html5",
    )
    try:
        import bleach
    except Exception:  # pragma: no cover - bleach is pinned in requirements
        return _rewrite_relative_urls(rendered, source)
    return _rewrite_relative_urls(
        bleach.clean(
            rendered, tags=_ALLOWED_TAGS, attributes=_ALLOWED_ATTRS, strip=True
        ),
        source,
    )


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


# --------------------------------------------------------------------------- #
# Cross-repo journal search
# --------------------------------------------------------------------------- #


async def _corpus(repo: str, refresh: bool) -> list[dict]:
    """Journal files to search for ``repo``: configured ledgers/routers + the
    most-recent session logs. Each entry carries the path and its GitHub blob
    URL so a hit can deep-link back."""
    cfg = config.REPOS[repo]["journal"]
    entries: list[dict] = [
        {"path": path, "blob": _gh(repo, f"/blob/main/{path}"), "kind": "doc"}
        for (_label, path) in cfg["docs"]
    ]
    if cfg["sessions_dir"]:
        res = await github.repo_api(
            repo, f"/contents/{cfg['sessions_dir']}", refresh=refresh
        )
        if res["ok"] and isinstance(res["data"], list):
            files = sorted(
                (
                    f
                    for f in res["data"]
                    if f.get("type") == "file" and f.get("name", "").endswith(".md")
                ),
                key=lambda x: x.get("name", ""),
                reverse=True,
            )[:SEARCH_SESSION_LIMIT]
            for f in files:
                entries.append(
                    {
                        "path": f["path"],
                        "blob": f.get("html_url") or _gh(repo, f"/blob/main/{f['path']}"),
                        "kind": "session",
                    }
                )
    return entries


def _snippet_html(text: str, idx: int, qlen: int) -> str:
    """An escaped, single-line context window around the first match, with the
    matched span wrapped in ``<mark>``. XSS-safe: every text segment is escaped,
    only the literal ``<mark>`` tags are injected."""
    start = max(0, idx - SNIPPET_RADIUS)
    end = min(len(text), idx + qlen + SNIPPET_RADIUS)
    before = _html.escape(text[start:idx].replace("\n", " "))
    match = _html.escape(text[idx : idx + qlen])
    after = _html.escape(text[idx + qlen : end].replace("\n", " "))
    return (
        ("… " if start > 0 else "")
        + before
        + "<mark>"
        + match
        + "</mark>"
        + after
        + (" …" if end < len(text) else "")
    )


def _snippet_text(text: str, idx: int, qlen: int) -> str:
    start = max(0, idx - SNIPPET_RADIUS)
    end = min(len(text), idx + qlen + SNIPPET_RADIUS)
    frag = text[start:end].replace("\n", " ").strip()
    return ("… " if start > 0 else "") + frag + (" …" if end < len(text) else "")


async def search_journal(q: str, refresh: bool = False) -> dict[str, Any]:
    """Case-insensitive search across every repo's journal corpus.

    Fetches each corpus file through the TTL-cached raw-content path and greps
    for ``q``; returns ranked hits (most matches first) each with repo, file,
    line, a highlighted snippet, and a GitHub deep-link. Fetch failures are
    collected into ``errors`` so the UI can show an honest banner rather than
    silently dropping a repo.
    """
    q = (q or "").strip()
    if not q:
        return {"q": q, "results": [], "errors": [], "scanned": 0, "empty": True}
    ql = q.lower()
    qlen = len(q)

    corpora = await asyncio.gather(
        *[_corpus(r, refresh) for r in config.REPOS]
    )
    targets: list[tuple[str, dict]] = []
    for repo, entries in zip(config.REPOS, corpora):
        for e in entries:
            targets.append((repo, e))

    fetched = await asyncio.gather(
        *[github.fetch_file(repo, e["path"], refresh=refresh) for (repo, e) in targets]
    )

    results: list[dict] = []
    errors: list[dict] = []
    for (repo, e), res in zip(targets, fetched):
        if not res["ok"] or not isinstance(res["data"], str):
            errors.append(
                {
                    "repo": repo,
                    "path": e["path"],
                    "status": res.get("status"),
                    "error": res.get("error") or f"HTTP {res.get('status')}",
                }
            )
            continue
        text = res["data"]
        lower = text.lower()
        if ql not in lower:
            continue
        idx = lower.index(ql)
        line = text.count("\n", 0, idx) + 1
        results.append(
            {
                "repo": repo,
                "path": e["path"],
                "kind": e["kind"],
                "matches": lower.count(ql),
                "line": line,
                "snippet_html": _snippet_html(text, idx, qlen),
                "snippet": _snippet_text(text, idx, qlen),
                "github_url": f"{e['blob']}#L{line}",
                "internal_url": f"/journal/{repo}/file?path={e['path']}",
            }
        )

    results.sort(key=lambda r: (-r["matches"], r["repo"], r["path"]))
    return {
        "q": q,
        "results": results,
        "errors": errors,
        "scanned": len(targets),
        "empty": False,
    }
