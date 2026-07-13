"""The Puddle Museum — loader for the committed ``data/puddle_museum.json``.

The /puddle-museum page is the marketing + concept page for "The Puddle
Museum", the venture-lab rainy-day picture-book (ORDER 022 item 4 venture
WEBSITE-IDEA intake). This module is a **read-only slice**: the exhibit
gallery and edition status live in a JSON file committed in this repo,
curated from venture-lab's vetting packet and manuscripts — cross-repo data
arrives only as committed JSON (never a live import). Read from disk at
request time: **no network, no secrets, stdlib only**.

Honesty rules (the "never fake data" doctrine, applied to a book that does
not exist yet as a printed thing):

- A missing or corrupt file degrades to empty structures — the page shows
  its honest empty state, never a crash and never invented exhibits.
- Entries missing required fields are skipped, never fatal.
- An edition is only ever presented as buyable when ``availability ==
  "live"`` AND its ``url`` is non-null. With the shipped data nothing is
  buyable — every edition is coming-soon with a null URL, so the template
  renders status notes and **zero buy links**. No dead links, no fake store.
- No exhibit references an image: the book is not illustrated yet, so the
  collection is text and emoji, and the page says so.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
MUSEUM_JSON_PATH = BASE_DIR / "data" / "puddle_museum.json"

AVAILABILITIES = ("live", "coming-soon")

_EXHIBIT_REQUIRED = ("slug", "emoji", "name_en", "description", "source", "as_of")
_EDITION_REQUIRED = ("lang", "title", "language", "availability", "status_note", "source", "as_of")


def _required_ok(entry: Any, required: tuple[str, ...]) -> bool:
    """True when the entry is a dict with every required field non-empty."""
    if not isinstance(entry, dict):
        return False
    for field in required:
        value = entry.get(field)
        if not isinstance(value, str) or not value.strip():
            return False
    return True


def _valid_exhibit(entry: Any) -> bool:
    if not _required_ok(entry, _EXHIBIT_REQUIRED):
        return False
    # Optional translated names must be strings when present.
    for field in ("name_nl", "name_de"):
        value = entry.get(field)
        if value is not None and not isinstance(value, str):
            return False
    return True


def _valid_edition(entry: Any) -> bool:
    if not _required_ok(entry, _EDITION_REQUIRED):
        return False
    if entry["availability"] not in AVAILABILITIES:
        return False
    url = entry.get("url")
    if url is not None and not isinstance(url, str):
        return False
    return True


def _empty() -> dict[str, list[dict[str, Any]]]:
    return {"exhibits": [], "editions": []}


def load_museum(path: Path | None = None) -> dict[str, list[dict[str, Any]]]:
    """Load and validate the museum data from disk.

    Returns ``{"exhibits": [...], "editions": [...]}``. Editions are
    enriched with the derived, template-ready ``is_buyable`` flag —
    ``availability == "live"`` AND a non-null URL, the only condition under
    which the template may ever render a buy link. Degrades to empty lists
    on a missing or corrupt file; skips (never crashes on) invalid entries.
    """
    src = path or MUSEUM_JSON_PATH
    try:
        raw = json.loads(src.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return _empty()
    if not isinstance(raw, dict):
        return _empty()

    exhibits: list[dict[str, Any]] = []
    for entry in raw.get("exhibits") or []:
        if not _valid_exhibit(entry):
            continue
        exhibit = dict(entry)
        exhibit["name_nl"] = (exhibit.get("name_nl") or "").strip() or None
        exhibit["name_de"] = (exhibit.get("name_de") or "").strip() or None
        exhibits.append(exhibit)

    editions: list[dict[str, Any]] = []
    for entry in raw.get("editions") or []:
        if not _valid_edition(entry):
            continue
        edition = dict(entry)
        url = (edition.get("url") or "").strip() or None
        edition["url"] = url
        edition["is_buyable"] = edition["availability"] == "live" and url is not None
        editions.append(edition)

    return {"exhibits": exhibits, "editions": editions}
