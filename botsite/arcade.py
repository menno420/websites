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
- The optional ``blocker`` object (``owner_action`` + ``unblocks``, both
  non-empty strings) records the named owner click that stands between an
  unavailable game and launch — the /arcade/{slug} detail page renders it
  as the "What's blocking launch" panel. It is OPTIONAL and fail-soft: a
  missing or malformed blocker normalizes to ``None`` (the panel simply
  falls back to the status note), never invented and never fatal.
- A blocker may additionally carry ``ask_id`` — the stable ``ASK-NNNN`` id
  of its row in the owner-actions ledger (docs/owner/OWNER-ACTIONS.md;
  append-only, never reused). It is the PRIMARY join key between this
  public panel and the gated owner console's verification chips
  (app/askverify.py joins on the id exactly; keyword signatures remain the
  fallback for id-less rows), so both surfaces flip from one ledger edit.
  Fail-soft like the rest of the schema: a missing or malformed id
  normalizes to ``None`` — the panel still renders, just without the
  ledger ref, and the console falls back to its signature scan.

The blocker schema itself lives in ``botsite/blockers.py`` (shared with the
catalog / products / puddle-museum registries since 2026-07-16 — one
normalizer, identical fail-soft semantics everywhere).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import blockers, listfilter

BASE_DIR = Path(__file__).resolve().parent
ARCADE_JSON_PATH = BASE_DIR / "data" / "arcade.json"

MATURITIES = ("playable", "beta", "prototype")
AVAILABILITIES = ("live", "download", "unavailable")
# The SINGLE source of truth for which availabilities carry an outbound link
# on the /arcade page (``has_link``). The drift probe's coverage
# (``arcade_probe.PROBED_AVAILABILITIES``) is defined AS this constant, so the
# probe can never silently under-cover a link-bearing availability the page
# renders — add a new linked value here and both surfaces move together.
LINKED_AVAILABILITIES = ("live", "download")
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
        game["has_link"] = game["availability"] in LINKED_AVAILABILITIES and url is not None
        game["link_url"] = _with_ref(url) if game["has_link"] and url else None
        game["blocker"] = blockers.normalized_blocker(game.get("blocker"))
        game["detail_url"] = f"/arcade/{game['slug']}"
        games.append(game)
    return games


def availability_summary(games: Any) -> dict[str, int]:
    """Pure, fail-soft availability counts for the /arcade catalog summary strip.

    Given any iterable of enriched game dicts (as :func:`load_games` returns),
    returns ``{"total", "live", "blocked", "owner_clicks"}``:

    - ``live`` — games really reachable (``has_link`` is truthy: a play or
      download link renders).
    - ``blocked`` — games with no reachable link (the honest inverse of
      ``live``); these are the cards that carry a blocker / status note.
    - ``owner_clicks`` — the number of DISTINCT owner actions standing between
      the blocked games and launch, deduplicated by ``ask_id`` (the stable
      owner-actions ledger id) when present, else by the ``owner_action``
      text. Blocked games with no recorded blocker contribute nothing — we
      only count clicks the registry actually names (never invent).
    - ``total`` — the number of games counted.

    Never raises: a non-iterable input, a non-dict entry, or a missing field
    is simply skipped (degrade, don't invent) — same honesty doctrine as the
    loader. Pure: takes already-loaded games, touches no disk and no network.
    """
    total = live = blocked = 0
    clicks: set[str] = set()
    try:
        iterator = iter(games)
    except TypeError:
        return {"total": 0, "live": 0, "blocked": 0, "owner_clicks": 0}
    for game in iterator:
        if not isinstance(game, dict):
            continue
        total += 1
        if game.get("has_link"):
            live += 1
            continue
        blocked += 1
        blocker = game.get("blocker")
        if not isinstance(blocker, dict):
            continue
        ask_id = blocker.get("ask_id")
        owner_action = blocker.get("owner_action")
        if isinstance(ask_id, str) and ask_id.strip():
            clicks.add("ask:" + ask_id.strip())
        elif isinstance(owner_action, str) and owner_action.strip():
            clicks.add("act:" + owner_action.strip())
    return {
        "total": total,
        "live": live,
        "blocked": blocked,
        "owner_clicks": len(clicks),
    }


def game_by_slug(slug: str, path: Path | None = None) -> dict[str, Any] | None:
    """The enriched game entry for ``slug``, or ``None`` when the registry has
    no such (valid) game — the /arcade/{slug} route turns that into the site's
    standard 404. Reads through :func:`load_games`, so the detail page and the
    catalog can never disagree about which games exist or what they claim."""
    for game in load_games(path):
        if game["slug"] == slug:
            return game
    return None


# --------------------------------------------------------------------------- #
# ORDER 019 PR2 — /arcade filter/sort/search over the centralized listfilter
# core (botsite/listfilter.py, a byte-identical vendored copy of
# app/listfilter.py — the repo's sharing pattern, like static/ds/).
# --------------------------------------------------------------------------- #

_MATURITY_RANK = {m: i for i, m in enumerate(MATURITIES)}


def _search_text(game: dict[str, Any]) -> str:
    return " ".join(
        str(game.get(k) or "") for k in ("name", "tagline", "description")
    )


FILTER_SPEC = listfilter.ListSpec(
    path="/arcade",
    dimensions=(
        listfilter.Dimension(
            key="maturity", label="maturity", values=MATURITIES,
            get=lambda g: [g.get("maturity", "")],
        ),
        listfilter.Dimension(
            key="availability", label="availability", values=AVAILABILITIES,
            get=lambda g: [g.get("availability", "")],
        ),
    ),
    sorts=(
        # ``catalog`` keeps the registry file's own order — the default, so a
        # no-param /arcade renders exactly as before.
        listfilter.SortOption("catalog", "catalog order"),
        listfilter.SortOption(
            "az", "name A-Z",
            sort_key=lambda g: str(g.get("name") or "").casefold(),
        ),
        listfilter.SortOption(
            "maturity", "maturity",
            sort_key=lambda g: (
                _MATURITY_RANK.get(g.get("maturity"), len(MATURITIES)),
                str(g.get("name") or "").casefold(),
            ),
        ),
    ),
    search=_search_text,
)
