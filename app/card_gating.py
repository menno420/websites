"""Reverse join: which public product cards does each owner-action gate?

The owner console lists the open ⚑ OWNER-ACTION asks and (since the
2026-07-15 launch console) an ``app/askverify.py`` verdict chip per ask.
What it never showed is the *blast radius* — how many public product cards
sit blocked behind that one owner click. This module computes exactly that,
the OTHER direction of the same ``ask_id`` join the botsite registries and
the owner-actions ledger already share (``botsite/blockers.py`` PR #360):

    ask_id (ASK-NNNN)  ->  [ the cards whose blocker names it ]

aggregated across the four committed botsite registries
(``botsite/data/{arcade,catalog,products,puddle_museum}.json``). The owner
console renders it as an "unblocks N cards" chip beside the verify chip, so
one glance ranks the open asks by how much public surface each unblocks.

Layering + honesty rules (the "never fake data" doctrine, applied here):

- **Read-only, disk-only.** The registries are committed JSON in this repo;
  they are read from disk exactly like every botsite loader reads them
  (``json.loads(path.read_text())``). NO network, NO secrets, stdlib only —
  this module imports nothing from the ``app`` client layer or from the
  ``botsite`` package (the four-service import rule: no service imports
  another service's package — the ``ASK-NNNN`` shape is re-stated here as a
  local constant rather than imported from ``botsite/blockers.py``).
- **Fail-soft everywhere.** A missing or corrupt registry file contributes
  nothing (empty), never a crash; a malformed entry or a malformed
  ``blocker`` is skipped; only a well-formed ``ASK-NNNN`` id (the ledger's
  stable join key) is ever counted. A bad file can only ever UNDERCOUNT —
  it never invents a gated card.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable

# Repo root -> the committed botsite registries. ``app`` and ``botsite`` are
# sibling packages in one repo; this reads botsite's committed DATA (never
# imports its code), the same read-only, forward-only pattern the rest of the
# codebase uses for cross-package committed JSON.
DATA_DIR = Path(__file__).resolve().parent.parent / "botsite" / "data"

# The owner-actions ledger's stable ask-id shape (``ID: ASK-NNNN``) — the
# exact join key ``botsite/blockers.py`` validates and ``app/askverify.py``
# joins on. Re-stated locally (not imported) to honor the import rule; the
# two definitions agreeing is pinned by tests/test_card_gating.py.
ASK_ID_RE = re.compile(r"ASK-\d{4}\Z")

# Per-registry identity: the public label the chip's tooltip shows, the JSON
# filename, and the ordered title-field candidates. One ordered candidate
# list spans all four shapes — catalog uses ``title``, arcade/products use
# ``name``, puddle-museum editions use ``title`` (exhibits carry no blocker);
# ``slug`` is the last-resort identity when a card names itself no other way.
_TITLE_KEYS = ("title", "name", "name_en", "slug")

REGISTRIES: tuple[dict[str, str], ...] = (
    {"registry": "arcade", "file": "arcade.json"},
    {"registry": "catalog", "file": "catalog.json"},
    {"registry": "products", "file": "products.json"},
    {"registry": "puddle-museum", "file": "puddle_museum.json"},
)


def _load_json(path: Path) -> Any:
    """Parse one registry file, degrading to ``None`` on a missing or corrupt
    file (fail-soft: a bad file contributes no cards, never a crash)."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _cards(raw: Any) -> Iterable[dict[str, Any]]:
    """The card dicts in one parsed registry, regardless of its top-level
    shape: a bare list (arcade / catalog / products) yields its entries; a
    dict (puddle-museum: ``{"exhibits": [...], "editions": [...]}``) yields
    every entry of every list-valued key, so a blocker on ANY collection is
    caught. Non-dict entries are skipped."""
    if isinstance(raw, list):
        collections: Iterable[Any] = [raw]
    elif isinstance(raw, dict):
        collections = [v for v in raw.values() if isinstance(v, list)]
    else:
        return
    for collection in collections:
        for entry in collection:
            if isinstance(entry, dict):
                yield entry


def _ask_id(blocker: Any) -> str | None:
    """The blocker's well-formed stable ``ASK-NNNN`` id, or ``None`` for a
    missing/malformed blocker or id (the exact fail-soft semantics of
    ``botsite.blockers.normalized_ask_id``, re-stated to avoid the
    cross-package import)."""
    if not isinstance(blocker, dict):
        return None
    ask_id = blocker.get("ask_id")
    if not isinstance(ask_id, str):
        return None
    ask_id = ask_id.strip()
    return ask_id if ASK_ID_RE.fullmatch(ask_id) else None


def _title(card: dict[str, Any]) -> str:
    """The card's display title — the first non-empty candidate field, or a
    stable placeholder (never an empty string, so the chip tooltip always
    names something)."""
    for key in _TITLE_KEYS:
        value = card.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return "(untitled card)"


def load_gating(data_dir: Path | None = None) -> dict[str, list[dict[str, str]]]:
    """Map every gating ``ask_id`` to the cards it holds closed.

    Returns ``{ask_id: [{"registry", "slug", "title"}, ...]}`` aggregated
    across the four registries — an ask gating cards in several registries
    accumulates all of them, in registry order then file order. An ask no
    card names is simply absent from the map (callers read a count of 0).
    Pure and side-effect-free: reads the committed JSON, touches nothing.
    """
    base = data_dir or DATA_DIR
    gating: dict[str, list[dict[str, str]]] = {}
    for reg in REGISTRIES:
        raw = _load_json(base / reg["file"])
        for card in _cards(raw):
            ask_id = _ask_id(card.get("blocker"))
            if ask_id is None:
                continue
            slug = card.get("slug")
            gating.setdefault(ask_id, []).append(
                {
                    "registry": reg["registry"],
                    "slug": slug if isinstance(slug, str) else "",
                    "title": _title(card),
                }
            )
    return gating


def annotate_unblocks(
    items: list[dict[str, Any]], data_dir: Path | None = None
) -> dict[str, list[dict[str, str]]]:
    """Attach ``unblocks_count`` + ``unblocks_cards`` to each queue item by
    its stable ``ask_id`` and return the gating map used.

    An item with no ``ask_id`` (legacy blocks, lane copies) or an id no card
    gates gets ``unblocks_count = 0`` and an empty list — the template hides
    the chip in that case. Read-only: the loaded map is computed once and
    shared across all items."""
    gating = load_gating(data_dir)
    for item in items:
        cards = gating.get(item.get("ask_id") or "", [])
        item["unblocks_count"] = len(cards)
        item["unblocks_cards"] = cards
    return gating
