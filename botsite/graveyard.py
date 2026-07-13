"""Strategy Graveyard — loader for the committed ``data/graveyard.json``.

The /graveyard page is the honest leaderboard of the trading-strategy lab's
experiment ledger (ORDER 022 item 4, venture WEBSITE-IDEA batch-2 intake).
This module is a **read-only slice**: the aggregate, the per-strategy rows,
and the top-N tables live in a JSON file committed in this repo, baked by
``botsite/gen_graveyard.py`` from trading-strategy's
``experiments/index.jsonl`` — cross-repo data arrives only as committed
JSON (never a live fetch in the request path). Read from disk at request
time: **no network, no secrets, stdlib only**.

Honesty rules (the "never fake data" doctrine):

- A missing or corrupt file degrades to ``available: False`` with the exact
  reason — the page shows its honest empty state, never a crash and never
  an invented leaderboard.
- The verdict counts pass through verbatim from the bake, including the
  load-bearing zero: ``promoted`` is 0 because the lab's promotion protocol
  is closed (holdout spent) — the page presents that plainly, never spun.
- ``source_sha`` may honestly be ``null`` (recorded with its reason at bake
  time) — a sha is never invented.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
GRAVEYARD_JSON_PATH = BASE_DIR / "data" / "graveyard.json"

_REQUIRED_TOP_LEVEL = ("as_of", "aggregate", "top", "strategies", "verdict_rule")
_REQUIRED_AGGREGATE = ("runs", "config_evals", "verdicts")
_REQUIRED_VERDICTS = ("promoted", "keep", "kill")


def _unavailable(reason: str) -> dict[str, Any]:
    return {"available": False, "reason": reason}


def load_graveyard(path: Path | None = None) -> dict[str, Any]:
    """Load and validate the graveyard summary from disk.

    Returns the baked document with ``available: True`` added, or
    ``{"available": False, "reason": ...}`` on a missing/corrupt/misshapen
    file — the template renders the honest empty state from the reason.
    """
    src = path or GRAVEYARD_JSON_PATH
    try:
        raw = json.loads(src.read_text(encoding="utf-8"))
    except OSError:
        return _unavailable(
            f"{src.name} is missing — the graveyard bake "
            "(botsite/gen_graveyard.py) has not committed its data here yet"
        )
    except ValueError:
        return _unavailable(f"{src.name} is not valid JSON — the committed bake is corrupt")

    if not isinstance(raw, dict):
        return _unavailable(f"{src.name} is not a JSON object — the committed bake is misshapen")
    for field in _REQUIRED_TOP_LEVEL:
        if field not in raw:
            return _unavailable(f"{src.name} is missing its '{field}' section — the committed bake is misshapen")
    aggregate = raw.get("aggregate")
    if not isinstance(aggregate, dict) or any(f not in aggregate for f in _REQUIRED_AGGREGATE):
        return _unavailable(f"{src.name} carries a misshapen 'aggregate' section")
    verdicts = aggregate.get("verdicts")
    if not isinstance(verdicts, dict) or any(
        not isinstance(verdicts.get(f), int) for f in _REQUIRED_VERDICTS
    ):
        return _unavailable(f"{src.name} carries a misshapen 'verdicts' section")
    top = raw.get("top")
    if not isinstance(top, dict) or not isinstance(top.get("keep"), list) or not isinstance(top.get("kill"), list):
        return _unavailable(f"{src.name} carries a misshapen 'top' section")
    if not isinstance(raw.get("strategies"), list):
        return _unavailable(f"{src.name} carries a misshapen 'strategies' section")

    doc = dict(raw)
    doc["available"] = True
    doc["reason"] = ""
    return doc
