"""Tester-program task catalog — the committed ``testing_tasks.json`` loader.

Extracted from ``botsite/testing.py`` (which re-exports it, so the ``/testing``
routes keep rendering through the SAME loader) so that non-route consumers —
today the tester-task URL liveness probe (``botsite/testing_probe.py``),
consumed by ``scripts/healthcheck.py`` — can read the catalog without
importing the route module (FastAPI app, templates, SQLite store). Import
rules hold: this is data-layer code; it imports nothing from routes.

Semantics are byte-identical to the original ``testing.load_tasks``: the
committed JSON is the source of truth for WHAT can be tested; a missing or
corrupt file raises (the routes have always surfaced that loudly rather than
faking an empty catalog). Callers that must never crash — the probe — wrap
the load and degrade the failure to a finding.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
TASKS_PATH = BASE_DIR / "testing_tasks.json"


def load_tasks(path: Path | None = None) -> list[dict[str, Any]]:
    src = path or TASKS_PATH
    data = json.loads(src.read_text(encoding="utf-8"))
    return list(data.get("tasks") or [])
