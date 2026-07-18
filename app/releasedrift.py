"""Release-drift parity on the console board (``/``).

Re-renders review's already-baked release-drift mirror (``review/data/releases.json``,
committed IN THIS repo by the review service) on the public board. This surface
NEVER recomputes drift and never imports review's package — it fetches the committed
JSON over the same TTL-cached, token-free raw path every other page uses
(``github._get(url, raw=True)``) and re-renders the producer's ``drift`` flag.

NOTE: this is a DISTINCT module from ``app/release_drift.py`` (an unrelated
classifier) — do not conflate the two.

Honest degrade, matching review's own handling: a failed fetch or an
unparseable / misshaped body yields count 0 and an empty list (never a faked
drift indicator), and this module never raises on feed content.
"""

from __future__ import annotations

import json
from typing import Any

from . import config, github

# The release-drift mirror is committed in THIS repo (menno420/websites) by the
# review service. Its only override knob is the ALREADY-DECLARED GITHUB_RAW_BASE
# (app/config.py, in the railway manifest) — this surface deliberately adds NO
# new env-var read, so it needs no new manifest entry (avoids the PR #426
# control-plane manifest collision). Read-only, forward-only.
RELEASES_JSON_URL = (
    f"{config.GITHUB_RAW_BASE}/menno420/websites/main/review/data/releases.json"
)

_EMPTY: dict[str, Any] = {"entries": [], "count": 0, "generated_at": ""}


def shape(data: Any) -> dict[str, Any]:
    """Baked drifting entries + count over the committed releases mirror.

    Filters to the producer-flagged ``drift`` entries; never re-derives the flag.
    Missing/empty/non-dict input degrades to an empty list, count 0; never raises.
    """
    if not isinstance(data, dict):
        return dict(_EMPTY)
    entries = [
        e
        for e in (data.get("entries") or [])
        if isinstance(e, dict) and e.get("drift")
    ]
    return {
        "entries": entries,
        "count": len(entries),
        "generated_at": data.get("generated_at") or "",
    }


async def overview(refresh: bool = False) -> dict[str, Any]:
    """Fetch + shape the committed release-drift mirror (honest degrade).

    Uses the shared TTL-cached raw path (token-free). Any fetch, parse, or shape
    failure degrades to count 0 / empty — never a faked drift indicator, never
    raises; the board simply shows no drift chip.
    """
    try:
        res = await github._get(RELEASES_JSON_URL, refresh=refresh, raw=True)
    except Exception:  # never let a data hiccup 500 the board
        return dict(_EMPTY)
    if not res.get("ok"):
        return dict(_EMPTY)
    data = res.get("data")
    if isinstance(data, str):  # raw host can hand back text; parse honestly
        try:
            data = json.loads(data)
        except ValueError:
            return dict(_EMPTY)
    return shape(data)
