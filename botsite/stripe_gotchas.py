"""SWTK webhook-gotchas companion — loader for ``data/stripe_gotchas.json``.

The /stripe-gotchas page is a free companion/marketing microsite for the
**Stripe Webhook Test Kit** (SWTK, the fleet's one LIVE product — $29 on
Gumroad) — ORDER 022 item 4 venture WEBSITE-IDEA batch-2 intake (marker:
"SWTK gotchas microsite"). This module is a **read-only slice**: the six
webhook gotchas (symptom + fix each, curated from the kit's own GOTCHAS.md
and the gotcha article) live in a JSON file committed in this repo with
explicit provenance (source repo, paths, commit sha, retrieved date) —
cross-repo data arrives only as committed JSON (never a live import, nothing
fetched on the request path). Read from disk at request time: **no network,
no secrets, stdlib only**.

Honesty rules (the "never fake data" doctrine, applied to a content page
that sells a real product):

- A missing or corrupt file degrades to an empty gotchas list — the page
  shows its honest empty state, never a crash and never invented content.
- Gotchas missing required fields are skipped, never fatal.
- Every technical claim on the page comes from the committed JSON, which is
  curated verbatim-faithfully from venture-lab @ the recorded sha — nothing
  invented, extended, or embellished here.
- The buy CTA is sourced from the existing committed product registry
  (:func:`swtk_product` → ``botsite/products.py``), never from constants
  duplicated here: a buy link renders ONLY when the registry says the kit
  is live with a real URL, and it already carries the ``ref=fleet-store``
  attribution. No invented store link, ever.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import products as products_registry

BASE_DIR = Path(__file__).resolve().parent
GOTCHAS_JSON_PATH = BASE_DIR / "data" / "stripe_gotchas.json"

SWTK_SLUG = "stripe-webhook-test-kit"

_GOTCHA_REQUIRED = ("id", "title", "symptom", "fix")
_GOTCHA_OPTIONAL = ("why", "code")
_PROVENANCE_REQUIRED = ("repo", "commit", "retrieved")


def _nonempty_str(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _valid_gotcha(entry: Any) -> bool:
    if not isinstance(entry, dict):
        return False
    return all(_nonempty_str(entry.get(f)) for f in _GOTCHA_REQUIRED)


def _load_gotcha(entry: dict[str, Any]) -> dict[str, Any]:
    gotcha = {f: entry[f] for f in _GOTCHA_REQUIRED}
    for f in _GOTCHA_OPTIONAL:
        gotcha[f] = entry[f] if _nonempty_str(entry.get(f)) else None
    return gotcha


def _load_provenance(raw: Any) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    if not all(_nonempty_str(raw.get(f)) for f in _PROVENANCE_REQUIRED):
        return None
    paths = raw.get("paths")
    if not isinstance(paths, list) or not all(_nonempty_str(p) for p in paths):
        return None
    return {f: raw[f] for f in _PROVENANCE_REQUIRED} | {"paths": list(paths)}


def _valid_check(entry: Any) -> bool:
    return isinstance(entry, dict) and all(
        _nonempty_str(entry.get(f)) for f in ("name", "line")
    )


_EMPTY: dict[str, Any] = {
    "gotchas": [],
    "provenance": None,
    "framing": None,
    "kit_checks": [],
    "kit_limits": [],
}


def load_gotchas(path: Path | None = None) -> dict[str, Any]:
    """Load and validate the gotchas page data from disk.

    Returns ``{"gotchas": [...], "provenance": {...} | None,
    "framing": str | None, "kit_checks": [...], "kit_limits": [...]}``.
    Degrades to empty structures on a missing or corrupt file; skips
    (never crashes on) invalid entries.
    """
    src = path or GOTCHAS_JSON_PATH
    try:
        raw = json.loads(src.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return dict(_EMPTY)
    if not isinstance(raw, dict):
        return dict(_EMPTY)
    gotchas_raw = raw.get("gotchas")
    checks_raw = raw.get("kit_checks")
    limits_raw = raw.get("kit_limits")
    return {
        "gotchas": ([_load_gotcha(g) for g in gotchas_raw if _valid_gotcha(g)]
                    if isinstance(gotchas_raw, list) else []),
        "provenance": _load_provenance(raw.get("provenance")),
        "framing": raw["framing"] if _nonempty_str(raw.get("framing")) else None,
        "kit_checks": ([c for c in checks_raw if _valid_check(c)]
                       if isinstance(checks_raw, list) else []),
        "kit_limits": ([s for s in limits_raw if _nonempty_str(s)]
                       if isinstance(limits_raw, list) else []),
    }


def swtk_product() -> dict[str, Any] | None:
    """The kit's entry in the committed product registry, or ``None``.

    The registry loader already derives ``is_live``/``has_link`` and a
    ``link_url`` carrying the standard ``ref=fleet-store`` attribution —
    the ONLY source the template's buy CTA may ever use."""
    return next((p for p in products_registry.load_products()
                 if p["slug"] == SWTK_SLUG), None)
