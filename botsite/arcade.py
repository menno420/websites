"""Fleet Arcade registry — loader for the committed ``data/arcade.json``.

The arcade is the public front door for the fleet's playable games
(ORDER 014; superbot ``docs/planning/fleet-strategy-synthesis-2026-07-11.md``
rank 3: "maturity labels + attribution telemetry"). Slice 1 is a read-only
catalog: the registry is a JSON file committed in this repo, read from disk at
request time — **no network, no secrets, stdlib only**.

Honesty rules (the "never fake data" doctrine, applied to games):

- A missing or corrupt registry file degrades to an empty list — the page
  shows its honest empty state, never a crash and never invented entries.
- Entries missing required fields are skipped, never fatal.
- An entry is only ever presented as *live* when ``availability == "live"``
  AND its ``url`` is non-null; a play/download link is only rendered when
  ``availability`` is live/download AND a URL is present. No dead links.
- Outbound game links carry ``?ref=fleet-arcade`` for attribution.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
ARCADE_JSON_PATH = BASE_DIR / "data" / "arcade.json"

MATURITIES = ("playable", "beta", "prototype")
AVAILABILITIES = ("live", "download", "unavailable")
REF_QUERY = "ref=fleet-arcade"

_REQUIRED = ("slug", "name", "tagline", "description", "maturity", "availability", "source_repo")


def _valid(entry: Any) -> bool:
    """True when the entry has every required field with a sane value."""
    if not isinstance(entry, dict):
        return False
    for field in _REQUIRED:
        value = entry.get(field)
        if not isinstance(value, str) or not value.strip():
            return False
    if entry["maturity"] not in MATURITIES:
        return False
    if entry["availability"] not in AVAILABILITIES:
        return False
    url = entry.get("url")
    if url is not None and not isinstance(url, str):
        return False
    return True


def _with_ref(url: str) -> str:
    """Append the ``ref=fleet-arcade`` attribution parameter to an outbound URL."""
    return url + ("&" if "?" in url else "?") + REF_QUERY


def load_games(path: Path | None = None) -> list[dict[str, Any]]:
    """Load and validate the arcade registry from disk.

    Returns a list of game dicts enriched with derived, template-ready fields:
    ``is_live`` (availability == "live" and a URL exists), ``has_link``
    (availability live/download and a URL exists) and ``link_url`` (the URL
    with the attribution ref, or ``None``). Degrades to ``[]`` on a missing or
    corrupt file; skips (never crashes on) invalid entries.
    """
    src = path or ARCADE_JSON_PATH
    try:
        raw = json.loads(src.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    if not isinstance(raw, list):
        return []
    games: list[dict[str, Any]] = []
    for entry in raw:
        if not _valid(entry):
            continue
        game = dict(entry)
        url = (game.get("url") or "").strip() or None
        game["url"] = url
        game["status_note"] = str(game.get("status_note") or "").strip()
        game["is_live"] = game["availability"] == "live" and url is not None
        game["has_link"] = game["availability"] in ("live", "download") and url is not None
        game["link_url"] = _with_ref(url) if game["has_link"] and url else None
        games.append(game)
    return games
