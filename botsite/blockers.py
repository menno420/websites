"""Shared blocker + ask-id normalizer for the botsite registries.

The optional ``blocker`` object first shipped on the arcade registry
(``botsite/arcade.py``, PR #349) and gained its stable ledger join key in
PR #360: ``{"owner_action", "unblocks", "ask_id"}`` — the named owner
click/decision standing between a registry entry and going live, plus the
``ASK-NNNN`` id of its row in the owner-actions ledger
(docs/owner/OWNER-ACTIONS.md; append-only, never reused). The 2026-07-16
follow-up extends the same object to catalog.json, products.json and
puddle_museum.json, so the schema lives here ONCE and every loader imports
it — the fail-soft semantics can never drift between registries.

Fail-soft semantics (the "never fake data" doctrine, verbatim from arcade):

- ``owner_action`` and ``unblocks`` are REQUIRED non-empty strings; a
  missing or malformed blocker normalizes to ``None`` and never
  invalidates the entry that carries it (degrade, don't invent).
- ``ask_id`` is OPTIONAL and validated against the ledger's stable id
  shape (``ASK-NNNN``); a malformed id costs only the ledger ref — the
  blocker itself survives, and the owner console's verification chips
  (app/askverify.py) fall back to their keyword-signature join.
"""

from __future__ import annotations

import re
from typing import Any

# The owner-actions ledger's stable ask-id shape (``ID: ASK-NNNN`` lines in
# docs/owner/OWNER-ACTIONS.md) — the exact join key the owner console's
# verification chips use. Anything else on ``blocker.ask_id`` is malformed
# and normalizes to ``None`` (fail-soft, never fatal).
ASK_ID_RE = re.compile(r"ASK-\d{4}\Z")


def normalized_ask_id(blocker: dict[str, Any]) -> str | None:
    """The blocker's ``ask_id`` when it is a well-formed stable ledger id
    (``ASK-NNNN``) — ``None`` for a missing or malformed one (fail-soft: a
    bad id costs only the ledger ref, never the blocker itself; the owner
    console then falls back to its keyword-signature join)."""
    ask_id = blocker.get("ask_id")
    if not isinstance(ask_id, str):
        return None
    ask_id = ask_id.strip()
    return ask_id if ASK_ID_RE.fullmatch(ask_id) else None


def normalized_blocker(raw: Any) -> dict[str, str | None] | None:
    """A raw ``blocker`` value as ``{"owner_action", "unblocks", "ask_id"}``
    with the first two values non-empty strings and ``ask_id`` a validated
    stable ledger id or ``None`` — or ``None`` for a missing/malformed
    blocker (fail-soft: a bad blocker never invalidates the registry entry
    that carries it)."""
    if not isinstance(raw, dict):
        return None
    owner_action = raw.get("owner_action")
    unblocks = raw.get("unblocks")
    if not isinstance(owner_action, str) or not owner_action.strip():
        return None
    if not isinstance(unblocks, str) or not unblocks.strip():
        return None
    return {
        "owner_action": owner_action.strip(),
        "unblocks": unblocks.strip(),
        "ask_id": normalized_ask_id(raw),
    }
