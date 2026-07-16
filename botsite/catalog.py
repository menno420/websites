"""Vetting catalog — loader for the committed ``data/catalog.json``.

The /products/catalog page is the full-pipeline face of venture-lab's
publishing lane (ORDER 022 item 4 — venture WEBSITE-IDEA intake; marker:
venture-lab ``control/outbox.md`` @ d56ec31). Where /products is the 4-item
store, this catalog shows EVERY vetted title and product with its honest
pipeline state. The registry is a JSON file committed in this repo, curated
by hand from venture-lab ``docs/publishing/vetting/*.md`` + ``OWNER-QUEUE.md``
— cross-repo data arrives only as committed JSON (never a live import). Read
from disk at request time: **no network, no secrets, stdlib only**. Sales
happen on Gumroad — this page only links out; it never takes payment.

Honesty rules (the "never fake data" doctrine, applied to the catalog):

- A missing or corrupt registry file degrades to an empty list — the page
  shows its honest empty state, never a crash and never invented entries.
- Entries missing required fields are skipped, never fatal.
- The status taxonomy is small and honest, derived from each packet's own
  Status blockquote + Verdict paragraph: ``live`` (actually purchasable
  now), ``publish-ready`` (publish-ready up to the owner gate),
  ``hard-gated`` (blocked on components/assets), ``parked`` (concept-stage
  or gate parks).
- An entry is only ever presented as buyable when ``status == "live"`` AND
  its ``url`` is non-null; every other entry carries its status note and
  never renders a buy link. No dead links.
- Outbound buy links carry ``?ref=fleet-store`` for attribution.
- The optional ``blocker`` object (``owner_action`` + ``unblocks``, plus an
  optional stable ``ask_id`` ledger ref — schema shared with the arcade via
  ``botsite/blockers.py``) records the named owner click/decision standing
  between a not-live entry and its launch; the page renders it as the
  entry's blocker panel. Fail-soft everywhere: a missing or malformed
  blocker normalizes to ``None`` and never invalidates the entry.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import blockers

BASE_DIR = Path(__file__).resolve().parent
CATALOG_JSON_PATH = BASE_DIR / "data" / "catalog.json"

STATUSES = ("live", "publish-ready", "hard-gated", "parked")
KINDS = ("book", "digital-product", "bundle")
REF_QUERY = "ref=fleet-store"

# Render order + page labels for the status groups.
STATUS_GROUPS = (
    ("live", "Live — purchasable now"),
    ("publish-ready", "Publish-ready — awaiting the owner's publish click"),
    ("hard-gated", "Hard-gated — blocked on components or assets"),
    ("parked", "Parked — vetted concept, blocking step flagged"),
)

_REQUIRED = ("slug", "title", "category", "kind", "price", "status", "status_note", "source", "as_of")


def _valid(entry: Any) -> bool:
    """True when the entry has every required field with a sane value."""
    if not isinstance(entry, dict):
        return False
    for field in _REQUIRED:
        value = entry.get(field)
        if not isinstance(value, str) or not value.strip():
            return False
    if entry["status"] not in STATUSES:
        return False
    if entry["kind"] not in KINDS:
        return False
    url = entry.get("url")
    if url is not None and not isinstance(url, str):
        return False
    return True


def _with_ref(url: str) -> str:
    """Append the ``ref=fleet-store`` attribution parameter to an outbound URL."""
    return url + ("&" if "?" in url else "?") + REF_QUERY


def load_catalog(path: Path | None = None) -> list[dict[str, Any]]:
    """Load and validate the vetting catalog from disk.

    Returns a list of entry dicts enriched with derived, template-ready
    fields: ``is_live`` (status == "live" and a URL exists), ``has_link``
    (alias of ``is_live`` — only live entries link out) and ``link_url``
    (the URL with the attribution ref, or ``None``). Degrades to ``[]`` on
    a missing or corrupt file; skips (never crashes on) invalid entries.
    """
    src = path or CATALOG_JSON_PATH
    try:
        raw = json.loads(src.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    if not isinstance(raw, list):
        return []
    entries: list[dict[str, Any]] = []
    for entry in raw:
        if not _valid(entry):
            continue
        item = dict(entry)
        url = (item.get("url") or "").strip() or None
        item["url"] = url
        item["is_live"] = item["status"] == "live" and url is not None
        item["has_link"] = item["is_live"]
        item["link_url"] = _with_ref(url) if item["has_link"] and url else None
        item["blocker"] = blockers.normalized_blocker(item.get("blocker"))
        entries.append(item)
    return entries


def group_by_status(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Group loaded entries into the honest status sections, render-ready.

    Returns only non-empty groups, in STATUS_GROUPS order, each as
    ``{"status": ..., "label": ..., "entries": [...]}``.
    """
    groups: list[dict[str, Any]] = []
    for status, label in STATUS_GROUPS:
        matched = [e for e in entries if e["status"] == status]
        if matched:
            groups.append({"status": status, "label": label, "entries": matched})
    return groups
