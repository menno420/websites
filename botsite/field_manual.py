"""Agent Fleet Field Manual funnel — loader for ``data/field_manual.json``.

The /field-manual page is the free-chapter funnel page for the **Agent Fleet
Field Manual** ($39 eBook, publish-ready in the vetting catalog but not yet
purchasable) — ORDER 022 item 4 venture WEBSITE-IDEA batch-2 intake (marker:
venture-lab ``control/outbox.md`` batch 2 @ 0679327, "field-manual
free-chapter funnel page"). This module is a **read-only slice**: the book
pitch (curated from the launch kit's LISTING.md + one-pager.md) and the free
chapter (the kit's own designated free chapter 1, "The D1 Lesson") live in a
JSON file committed in this repo with explicit provenance (source repo,
path, commit sha, retrieved date) — cross-repo data arrives only as
committed JSON (never a live import, nothing fetched on the request path).
Read from disk at request time: **no network, no secrets, stdlib only**.

Honesty rules (the "never fake data" doctrine, applied to a book that is
not purchasable yet):

- A missing or corrupt file degrades to empty structures — the page shows
  its honest empty state, never a crash and never an invented pitch.
- Blocks/chapters missing required fields are skipped, never fatal.
- The CTA follows the committed ``data/catalog.json`` entry (slug
  ``agent-fleet-field-manual``): a buy link renders ONLY when that entry
  carries a real ``url``. Today it does not — the page says plainly that
  the publish click is queued to the owner and the book cannot be bought
  yet. The moment the committed catalog gains the url, :func:`buy_url`
  returns it (with the ``ref=fleet-store`` attribution) and the page shows
  the buy link automatically. No invented store link, ever.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import catalog as catalog_registry

BASE_DIR = Path(__file__).resolve().parent
FIELD_MANUAL_JSON_PATH = BASE_DIR / "data" / "field_manual.json"

BOOK_SLUG = "agent-fleet-field-manual"

BLOCK_TEXT_TYPES = ("p", "h2", "note")
BLOCK_LIST_TYPES = ("ul", "ol")

_BOOK_REQUIRED = ("slug", "title", "subtitle", "tagline", "description",
                  "who_for", "source", "as_of")
_CHAPTER_REQUIRED = ("num", "title", "line")
_PROVENANCE_REQUIRED = ("repo", "path", "commit", "retrieved")


def _nonempty_str(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _valid_chapter(entry: Any) -> bool:
    if not isinstance(entry, dict):
        return False
    if not all(_nonempty_str(entry.get(f)) for f in _CHAPTER_REQUIRED):
        return False
    return isinstance(entry.get("free"), bool)


def _valid_block(entry: Any) -> bool:
    if not isinstance(entry, dict):
        return False
    kind = entry.get("type")
    if kind in BLOCK_TEXT_TYPES:
        return _nonempty_str(entry.get("text"))
    if kind in BLOCK_LIST_TYPES:
        items = entry.get("items")
        return (isinstance(items, list) and bool(items)
                and all(_nonempty_str(i) for i in items))
    return False


def _str_list(raw: Any) -> list[str]:
    if not isinstance(raw, list):
        return []
    return [s for s in raw if _nonempty_str(s)]


def _load_book(raw: Any) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    if not all(_nonempty_str(raw.get(f)) for f in _BOOK_REQUIRED):
        return None
    book = {f: raw[f] for f in _BOOK_REQUIRED}
    book["bullets"] = _str_list(raw.get("bullets"))
    book["not_claims"] = _str_list(raw.get("not_claims"))
    chapters_raw = raw.get("chapters")
    book["chapters"] = ([c for c in chapters_raw if _valid_chapter(c)]
                        if isinstance(chapters_raw, list) else [])
    return book


def _load_excerpt(raw: Any) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    if not _nonempty_str(raw.get("title")):
        return None
    prov = raw.get("provenance")
    if not isinstance(prov, dict) or not all(
            _nonempty_str(prov.get(f)) for f in _PROVENANCE_REQUIRED):
        return None
    blocks_raw = raw.get("blocks")
    blocks = ([b for b in blocks_raw if _valid_block(b)]
              if isinstance(blocks_raw, list) else [])
    if not blocks:
        return None  # an excerpt with no readable body is no excerpt
    return {
        "chapter": raw.get("chapter") if _nonempty_str(raw.get("chapter")) else None,
        "title": raw["title"],
        "why_chosen": raw.get("why_chosen") if _nonempty_str(raw.get("why_chosen")) else None,
        "provenance": {f: prov[f] for f in _PROVENANCE_REQUIRED},
        "blocks": blocks,
    }


def load_field_manual(path: Path | None = None) -> dict[str, Any]:
    """Load and validate the funnel-page data from disk.

    Returns ``{"book": {...} | None, "excerpt": {...} | None}``. Each half
    degrades independently to ``None`` when missing or invalid — the page
    renders an honest empty state for whichever half is absent. Never
    raises on a missing/corrupt file.
    """
    src = path or FIELD_MANUAL_JSON_PATH
    try:
        raw = json.loads(src.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"book": None, "excerpt": None}
    if not isinstance(raw, dict):
        return {"book": None, "excerpt": None}
    return {
        "book": _load_book(raw.get("book")),
        "excerpt": _load_excerpt(raw.get("excerpt")),
    }


def catalog_entry() -> dict[str, Any] | None:
    """The book's entry in the committed vetting catalog, or ``None``."""
    return next((e for e in catalog_registry.load_catalog()
                 if e["slug"] == BOOK_SLUG), None)


def buy_url(entry: dict[str, Any] | None) -> str | None:
    """The real buy link for the catalog entry, or ``None``.

    Returns a URL exactly when the committed catalog entry carries one
    (with the standard ``ref=fleet-store`` attribution appended) — the only
    condition under which the template may ever render a buy button. A
    ``None`` here is the honest "not purchasable yet" state.
    """
    if not entry:
        return None
    url = (entry.get("url") or "").strip()
    if not url:
        return None
    if entry.get("link_url"):  # live entry: the loader already added the ref
        return entry["link_url"]
    return url + ("&" if "?" in url else "?") + catalog_registry.REF_QUERY
