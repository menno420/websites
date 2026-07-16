"""Fleet store registry — loader for the committed ``data/products.json``.

The /products page is the fleet's storefront face for venture-lab's products
(ORDER 022 item 4, self-initiated). The registry is a JSON file committed in
this repo, curated from venture-lab launch copy — cross-repo data arrives
only as committed JSON (never a live import). Read from disk at request
time: **no network, no secrets, stdlib only**. Sales happen on Gumroad —
this page only links out; it never takes payment.

Honesty rules (the "never fake data" doctrine, applied to products):

- A missing or corrupt registry file degrades to an empty list — the page
  shows its honest empty state, never a crash and never invented entries.
- Entries missing required fields are skipped, never fatal.
- An entry is only ever presented as buyable when ``availability == "live"``
  AND its ``url`` is non-null; coming-soon entries carry their status note
  and never render a buy link. No dead links.
- Outbound buy links carry ``?ref=fleet-store`` for attribution.
- The optional ``blocker`` object (``owner_action`` + ``unblocks``, plus an
  optional stable ``ask_id`` ledger ref — schema shared with the arcade via
  ``botsite/blockers.py``) records the named owner click standing between a
  coming-soon product and its launch. Fail-soft everywhere: a missing or
  malformed blocker normalizes to ``None`` and never invalidates the entry.

``stale_products`` (below) is a SEPARATE freshness check, not part of the
load/validate path: each entry's ``as_of`` records when it was last
re-verified against venture-lab, and a hand-curated registry drifts
silently the moment a product goes live or changes price. It never
disqualifies an entry from ``load_products`` — staleness is a nag for a
human to re-verify, not an honesty violation to hide.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import blockers

BASE_DIR = Path(__file__).resolve().parent
PRODUCTS_JSON_PATH = BASE_DIR / "data" / "products.json"

AVAILABILITIES = ("live", "coming-soon")
REF_QUERY = "ref=fleet-store"

_REQUIRED = ("slug", "name", "tagline", "description", "price", "availability", "source", "as_of")


def _valid(entry: Any) -> bool:
    """True when the entry has every required field with a sane value."""
    if not isinstance(entry, dict):
        return False
    for field in _REQUIRED:
        value = entry.get(field)
        if not isinstance(value, str) or not value.strip():
            return False
    if entry["availability"] not in AVAILABILITIES:
        return False
    url = entry.get("url")
    if url is not None and not isinstance(url, str):
        return False
    return True


def _with_ref(url: str) -> str:
    """Append the ``ref=fleet-store`` attribution parameter to an outbound URL."""
    return url + ("&" if "?" in url else "?") + REF_QUERY


def load_products(path: Path | None = None) -> list[dict[str, Any]]:
    """Load and validate the product registry from disk.

    Returns a list of product dicts enriched with derived, template-ready
    fields: ``is_live`` (availability == "live" and a URL exists),
    ``has_link`` (alias of ``is_live`` — only live products link out) and
    ``link_url`` (the URL with the attribution ref, or ``None``). Degrades to
    ``[]`` on a missing or corrupt file; skips (never crashes on) invalid
    entries.
    """
    src = path or PRODUCTS_JSON_PATH
    try:
        raw = json.loads(src.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    if not isinstance(raw, list):
        return []
    products: list[dict[str, Any]] = []
    for entry in raw:
        if not _valid(entry):
            continue
        product = dict(entry)
        url = (product.get("url") or "").strip() or None
        product["url"] = url
        product["status_note"] = str(product.get("status_note") or "").strip()
        product["is_live"] = product["availability"] == "live" and url is not None
        product["has_link"] = product["is_live"]
        product["link_url"] = _with_ref(url) if product["has_link"] and url else None
        product["blocker"] = blockers.normalized_blocker(product.get("blocker"))
        products.append(product)
    return products


# Staleness horizon (days): how long a product's ``as_of`` re-verification
# is trusted before it nags. Two weeks — venture-lab entries move on a
# roughly weekly cadence at the busiest (see ``app.freshness``'s analogous
# ``COMMIT_STALE_DAYS`` docstring for the same reasoning shape); one week
# would false-alarm a quiet-but-current product, a month would let a real
# price/availability change go unverified for too long.
STALE_HORIZON_DAYS = 14


def stale_products(
    products: list[dict[str, Any]],
    now: datetime,
    horizon_days: int = STALE_HORIZON_DAYS,
) -> list[dict[str, Any]]:
    """Products whose ``as_of`` is strictly past ``horizon_days`` old.

    ``now`` is injectable (the module time-discipline convention — see
    ``app/clock.py``'s docstring for the fleet-wide rule this follows);
    callers pass the real wall clock in production/CI and a frozen instant
    in tests. Exactly at the horizon is not stale, only strictly past it
    (matches ``app.freshness``'s boundary rule). An entry with a missing or
    unparseable ``as_of`` is skipped, never invented as stale or crashed
    on — ``load_products`` already guarantees the field is a non-empty
    string, but this function makes no assumption about its shape.

    Returns the stale entries verbatim plus a computed ``age_days`` float,
    oldest first.
    """
    stale: list[dict[str, Any]] = []
    for product in products:
        try:
            as_of_dt = datetime.strptime(
                str(product.get("as_of", "")), "%Y-%m-%d"
            ).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        age_days = (now - as_of_dt).total_seconds() / 86400
        if age_days > horizon_days:
            stale.append({**product, "age_days": age_days})
    stale.sort(key=lambda p: p["age_days"], reverse=True)
    return stale
