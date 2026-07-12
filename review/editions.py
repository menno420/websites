"""Review editions — dated, committed program reviews rendered as a section.

The site is a channel for CONTINUOUS review: each edition is one committed
markdown file under ``data/reviews/`` (shipped inside the Railway
Root-Directory deploy, like every other data file here), written by an agent
session from the repo's real record and landed through the normal PR
ceremony. The publishing ritual + template live in ``review/README.md``.

File format — a minimal front-matter header, then markdown:

    ---
    title: Edition 1 — …
    date: 2026-07-11
    summary: one or two plain sentences for the index + feed
    ---
    body markdown …

Rendering uses the ``markdown`` package (same pinned version the
control-plane journal uses) with a graceful escaped-``<pre>`` fallback; the
content is this repo's own committed files (trusted input). The Atom feed
(``/reviews/feed.xml``) is built with ``xml.etree`` — every field
XML-escaped by the library, never hand-concatenated (the ``/activity.xml``
precedent). Entry ids are the editions' GitHub blob URLs: stable, real, and
independent of whatever host the service runs on.
"""

from __future__ import annotations

import html as _html
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Optional

from . import listfilter

BASE_DIR = Path(__file__).resolve().parent
REVIEWS_DIR = BASE_DIR / "data" / "reviews"
REPO_URL = "https://github.com/menno420/websites"

_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def parse_edition(text: str, slug: str) -> Optional[dict[str, Any]]:
    """One edition file → ``{slug, title, date, summary, body_md}``.

    Returns None for a file without a well-formed front-matter block —
    the caller skips it (an honest absence beats rendering a broken page).
    """
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text, re.DOTALL)
    if not m:
        return None
    header, body = m.group(1), m.group(2)
    meta: dict[str, str] = {}
    for line in header.splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            meta[k.strip().lower()] = v.strip()
    title = meta.get("title", "")
    date = meta.get("date", "")
    if not title or not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
        return None
    return {
        "slug": slug,
        "title": title,
        "date": date,
        "summary": meta.get("summary", ""),
        "body_md": body.strip(),
        "source_url": f"{REPO_URL}/blob/main/review/data/reviews/{slug}.md",
    }


def list_editions(directory: Path | None = None) -> list[dict[str, Any]]:
    """All well-formed editions, newest date first (date desc, slug desc)."""
    directory = REVIEWS_DIR if directory is None else directory
    editions: list[dict[str, Any]] = []
    if not directory.is_dir():
        return editions
    for path in sorted(directory.glob("*.md")):
        if not _SLUG_RE.match(path.stem):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        parsed = parse_edition(text, path.stem)
        if parsed:
            editions.append(parsed)
    editions.sort(key=lambda e: (e["date"], e["slug"]), reverse=True)
    return editions


def get_edition(slug: str, directory: Path | None = None) -> Optional[dict[str, Any]]:
    for e in list_editions(directory):
        if e["slug"] == slug:
            return e
    return None


def render_markdown(text: str) -> str:
    """Trusted committed markdown → HTML; escaped ``<pre>`` if the lib breaks."""
    try:
        import markdown as _md
    except Exception:  # pragma: no cover - markdown is pinned in requirements
        return f"<pre>{_html.escape(text)}</pre>"
    return _md.markdown(text, extensions=["fenced_code", "tables", "sane_lists"])


def atom_feed(editions: list[dict[str, Any]], base_url: str) -> str:
    """A valid Atom 1.0 feed over the editions list.

    ``base_url`` is the deployment's own root (taken from the live request,
    since the service URL is owner-created); entry ids are GitHub blob URLs
    so they stay stable across hosts. An empty editions list still yields a
    valid feed — never malformed, never a fake entry.
    """
    base = base_url.rstrip("/")
    ET.register_namespace("", "http://www.w3.org/2005/Atom")
    feed = ET.Element("{http://www.w3.org/2005/Atom}feed")
    ET.SubElement(feed, "{http://www.w3.org/2005/Atom}title").text = (
        "Program review editions — owner + Claude-agent fleet"
    )
    ET.SubElement(feed, "{http://www.w3.org/2005/Atom}id").text = (
        f"{REPO_URL}/tree/main/review/data/reviews"
    )
    ET.SubElement(
        feed, "{http://www.w3.org/2005/Atom}link",
        {"rel": "self", "href": f"{base}/reviews/feed.xml", "type": "application/atom+xml"},
    )
    ET.SubElement(
        feed, "{http://www.w3.org/2005/Atom}link",
        {"rel": "alternate", "href": f"{base}/reviews", "type": "text/html"},
    )
    author = ET.SubElement(feed, "{http://www.w3.org/2005/Atom}author")
    ET.SubElement(author, "{http://www.w3.org/2005/Atom}name").text = (
        "Claude agent sessions (menno420/websites)"
    )
    updated = ET.SubElement(feed, "{http://www.w3.org/2005/Atom}updated")
    updated.text = (
        f"{editions[0]['date']}T00:00:00Z" if editions else "1970-01-01T00:00:00Z"
    )
    for e in editions:
        entry = ET.SubElement(feed, "{http://www.w3.org/2005/Atom}entry")
        ET.SubElement(entry, "{http://www.w3.org/2005/Atom}title").text = e["title"]
        ET.SubElement(entry, "{http://www.w3.org/2005/Atom}id").text = e["source_url"]
        ET.SubElement(
            entry, "{http://www.w3.org/2005/Atom}link",
            {"rel": "alternate", "href": f"{base}/reviews/{e['slug']}", "type": "text/html"},
        )
        ET.SubElement(entry, "{http://www.w3.org/2005/Atom}updated").text = (
            f"{e['date']}T00:00:00Z"
        )
        ET.SubElement(entry, "{http://www.w3.org/2005/Atom}summary").text = (
            e["summary"] or e["title"]
        )
    return '<?xml version="1.0" encoding="utf-8"?>\n' + ET.tostring(
        feed, encoding="unicode"
    )


# --------------------------------------------------------------------------- #
# ORDER 019 PR2 — /reviews filter/sort/search over the centralized listfilter
# core (review/listfilter.py, a byte-identical vendored copy of
# app/listfilter.py — the repo's sharing pattern, like static/ds/).
# --------------------------------------------------------------------------- #


def edition_month(edition: dict[str, Any]) -> str:
    """The dated edition's ``YYYY-MM`` bucket (dates are format-validated by
    ``parse_edition``, so this never invents a month)."""
    return str(edition.get("date") or "")[:7]


def _newest_key(edition: dict[str, Any]) -> tuple:
    return (edition.get("date", ""), edition.get("slug", ""))


FILTER_SPEC = listfilter.ListSpec(
    path="/reviews",
    dimensions=(
        listfilter.Dimension(
            key="month", label="month",
            get=lambda e: [edition_month(e)],
        ),
    ),
    sorts=(
        # ``newest`` reproduces list_editions()' own order exactly (same
        # date-desc, slug-desc key) — no params renders identically to before.
        listfilter.SortOption("newest", "newest", sort_key=_newest_key,
                              reverse=True),
        listfilter.SortOption("oldest", "oldest", sort_key=_newest_key),
        listfilter.SortOption(
            "title", "title A-Z",
            sort_key=lambda e: str(e.get("title") or "").casefold(),
        ),
    ),
    search=lambda e: " ".join(
        str(e.get(k) or "") for k in ("title", "summary")
    ),
)
