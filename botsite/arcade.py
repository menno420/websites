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


# --------------------------------------------------------------------------- #
# Optional richer-detail fields — screenshots / controls / changelog.
# These mirror the optional ``blocker`` pattern (botsite/blockers.py): each is
# OPTIONAL and fail-soft. A missing or malformed value normalizes to an empty
# list, malformed entries are dropped (never fatal), and the detail template
# hides the whole section when the list is empty. TRUTH bar: only real,
# verifiable content the registry actually carries is ever rendered — a bad
# field costs only its own section, never the game entry (degrade, don't
# invent). The detail page renders them behind ``{% if game.<field> %}`` guards,
# so a game with none renders exactly as before this slice.
# --------------------------------------------------------------------------- #


def normalized_screenshots(raw: Any) -> list[dict[str, str]]:
    """A raw ``screenshots`` value as a list of ``{src, alt}`` dicts.

    ``src`` is a non-empty committed asset path (e.g. under
    ``botsite/static/...``); ``alt`` is descriptive text (``""`` when absent).
    Fail-soft: a non-list input, or an entry that is not a dict or lacks a
    non-empty string ``src``, is dropped — a missing/malformed value degrades
    to ``[]`` (the template then hides the screenshots section). Never raises.
    """
    if not isinstance(raw, list):
        return []
    out: list[dict[str, str]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        src = item.get("src")
        if not isinstance(src, str) or not src.strip():
            continue
        alt = item.get("alt")
        alt = alt.strip() if isinstance(alt, str) else ""
        out.append({"src": src.strip(), "alt": alt})
    return out


def normalized_controls(raw: Any) -> list[dict[str, str]]:
    """A raw ``controls`` value as a list of ``{input, action}`` dicts.

    Accepts either dicts (``{"input": "A", "action": "Thrust"}``) or bare
    strings (a plain action line, normalized to ``{"input": "", "action": s}``).
    A dict entry needs a non-empty string ``action``; ``input`` is optional
    (``""`` when absent). Fail-soft: a non-list input, or an entry that is
    neither a usable string nor a dict with a non-empty ``action``, is dropped
    — a missing/malformed value degrades to ``[]``. Never raises.
    """
    if not isinstance(raw, list):
        return []
    out: list[dict[str, str]] = []
    for item in raw:
        if isinstance(item, str):
            if item.strip():
                out.append({"input": "", "action": item.strip()})
            continue
        if not isinstance(item, dict):
            continue
        action = item.get("action")
        if not isinstance(action, str) or not action.strip():
            continue
        input_ = item.get("input")
        input_ = input_.strip() if isinstance(input_, str) else ""
        out.append({"input": input_, "action": action.strip()})
    return out


def normalized_changelog(raw: Any) -> list[dict[str, str]]:
    """A raw ``changelog`` value as a list of ``{version, date, note}`` dicts.

    An entry needs a non-empty string ``note`` plus at least one of a non-empty
    ``version`` or ``date`` (the label the list renders); the missing one is
    ``""``. Fail-soft: a non-list input, or an entry that is not a dict, lacks a
    ``note``, or carries neither version nor date, is dropped — a
    missing/malformed value degrades to ``[]``. Never raises.
    """
    if not isinstance(raw, list):
        return []
    out: list[dict[str, str]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        note = item.get("note")
        if not isinstance(note, str) or not note.strip():
            continue
        version = item.get("version")
        version = version.strip() if isinstance(version, str) else ""
        date = item.get("date")
        date = date.strip() if isinstance(date, str) else ""
        if not version and not date:
            continue
        out.append({"version": version, "date": date, "note": note.strip()})
    return out


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
        game["screenshots"] = normalized_screenshots(game.get("screenshots"))
        game["controls"] = normalized_controls(game.get("controls"))
        game["changelog"] = normalized_changelog(game.get("changelog"))
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


def pending_owner_actions(games: Any) -> list[dict[str, Any]]:
    """The consolidated owner-action queue for the /arcade summary panel.

    Given enriched game dicts (as :func:`load_games` returns), returns one
    entry per DISTINCT pending owner click standing between the blocked games
    and launch, in first-seen order::

        {"owner_action": str, "ask_id": str | None, "games": [name, ...]}

    Distinctness matches :func:`availability_summary`'s ``owner_clicks`` count
    exactly — deduplicated by ``ask_id`` when present, else by ``owner_action``
    text — so the panel's length always equals the summary strip's click
    count. When two blocked games name the same click they collapse to a single
    entry whose ``games`` list carries both names. Only games with no reachable
    link (``has_link`` falsy) and a recorded, nameable blocker contribute — we
    surface the clicks the registry actually names, never invent one.

    Pure and fail-soft: a non-iterable input or a malformed entry degrades to
    ``[]`` / skip, the same "degrade, don't invent" doctrine as the loader and
    the summary. Touches no disk and no network.
    """
    order: list[str] = []
    by_key: dict[str, dict[str, Any]] = {}
    try:
        iterator = iter(games)
    except TypeError:
        return []
    for game in iterator:
        if not isinstance(game, dict):
            continue
        if game.get("has_link"):
            continue
        blocker = game.get("blocker")
        if not isinstance(blocker, dict):
            continue
        owner_action = blocker.get("owner_action")
        if not (isinstance(owner_action, str) and owner_action.strip()):
            continue
        owner_action = owner_action.strip()
        raw_ask = blocker.get("ask_id")
        ask_id = raw_ask.strip() if isinstance(raw_ask, str) and raw_ask.strip() else None
        key = "ask:" + ask_id if ask_id else "act:" + owner_action
        entry = by_key.get(key)
        if entry is None:
            entry = {"owner_action": owner_action, "ask_id": ask_id, "games": []}
            by_key[key] = entry
            order.append(key)
        name = game.get("name")
        if isinstance(name, str) and name.strip():
            entry["games"].append(name.strip())
    return [by_key[k] for k in order]


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
