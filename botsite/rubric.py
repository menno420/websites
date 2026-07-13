""""Should I build it?" rubric scorer — loader for ``data/rubric.json``.

The /should-i-build-it page is an interactive scorer for **venture-eval-001**,
the venture-lab lane's real distribution-first vetting rubric — ORDER 022
item 4 venture WEBSITE-IDEA batch-2 intake (marker: "'Should I build it?'
rubric scorer"). Every candidate intake in venture-lab's ``candidates/*/
INTAKE.md`` is scored on exactly these five axes and weights ("Scoring
(venture-eval-001 rubric, weighted 0–5)"); the axis anchors and verdict
bands are the ones the lane ships in its own Kill-Rule Intake Kit
(``candidates/kill-rule-intake-kit/pack/SCORING-RUBRIC.md``).

This module is a **read-only slice**: the rubric (axes + weights + anchors +
verdict bands + anti-gaming rules) lives in a JSON file committed in this
repo with explicit provenance (source repo, paths, commit sha, retrieved
date) — cross-repo data arrives only as committed JSON (never a live import,
nothing fetched on the request path). Read from disk at request time:
**no network, no secrets, stdlib only**. Scoring happens entirely in the
visitor's browser (vanilla JS over the same committed data) — the route is
GET-only and holds zero server state.

Honesty rules (the "never fake data" doctrine, applied to a methodology
page):

- A missing or corrupt file degrades to an empty axes list — the page shows
  its honest empty state, never a crash and never invented criteria.
- Axes/bands missing required fields are skipped, never fatal.
- The weights, anchors, thresholds, and verdict wording come from the
  committed JSON, curated verbatim-faithfully from venture-lab @ the
  recorded sha — nothing invented, no criteria this fleet does not actually
  score on, and the rubric's own caveat ("comparative, not absolute — no
  magic pass mark") renders with the verdict.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
RUBRIC_JSON_PATH = BASE_DIR / "data" / "rubric.json"

_AXIS_REQUIRED = ("id", "name", "measures", "question", "plain")
_AXIS_OPTIONAL = ("kit_name",)
_BAND_REQUIRED = ("id", "range", "label")
_PROVENANCE_REQUIRED = ("repo", "commit", "retrieved")


def _nonempty_str(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _valid_anchor(entry: Any) -> bool:
    return (isinstance(entry, dict)
            and isinstance(entry.get("score"), (int, float))
            and _nonempty_str(entry.get("text")))


def _valid_axis(entry: Any) -> bool:
    if not isinstance(entry, dict):
        return False
    if not all(_nonempty_str(entry.get(f)) for f in _AXIS_REQUIRED):
        return False
    weight = entry.get("weight")
    if not isinstance(weight, (int, float)) or not 0 < weight <= 1:
        return False
    anchors = entry.get("anchors")
    return (isinstance(anchors, list) and bool(anchors)
            and all(_valid_anchor(a) for a in anchors))


def _load_axis(entry: dict[str, Any]) -> dict[str, Any]:
    axis = {f: entry[f] for f in _AXIS_REQUIRED}
    axis["weight"] = float(entry["weight"])
    axis["anchors"] = [
        {"score": a["score"], "text": a["text"]} for a in entry["anchors"]
    ]
    for f in _AXIS_OPTIONAL:
        axis[f] = entry[f] if _nonempty_str(entry.get(f)) else None
    return axis


def _valid_band(entry: Any) -> bool:
    if not isinstance(entry, dict):
        return False
    if not all(_nonempty_str(entry.get(f)) for f in _BAND_REQUIRED):
        return False
    max_ = entry.get("max")
    return max_ is None or isinstance(max_, (int, float))


def _load_band(entry: dict[str, Any]) -> dict[str, Any]:
    band = {f: entry[f] for f in _BAND_REQUIRED}
    band["max"] = float(entry["max"]) if entry.get("max") is not None else None
    band["caveat"] = entry["caveat"] if _nonempty_str(entry.get("caveat")) else None
    return band


def _load_provenance(raw: Any) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    if not all(_nonempty_str(raw.get(f)) for f in _PROVENANCE_REQUIRED):
        return None
    paths = raw.get("paths")
    if not isinstance(paths, list) or not all(_nonempty_str(p) for p in paths):
        return None
    return {f: raw[f] for f in _PROVENANCE_REQUIRED} | {"paths": list(paths)}


def _load_scale(raw: Any) -> dict[str, float]:
    if (isinstance(raw, dict)
            and all(isinstance(raw.get(k), (int, float))
                    for k in ("min", "max", "step"))
            and raw["min"] < raw["max"] and raw["step"] > 0):
        return {k: float(raw[k]) for k in ("min", "max", "step")}
    return {"min": 0.0, "max": 5.0, "step": 0.5}


_EMPTY: dict[str, Any] = {
    "axes": [],
    "bands": [],
    "scale": {"min": 0.0, "max": 5.0, "step": 0.5},
    "provenance": None,
    "framing": None,
    "reading_note": None,
    "anti_gaming": [],
    "worked_example": None,
}


def load_rubric(path: Path | None = None) -> dict[str, Any]:
    """Load and validate the rubric page data from disk.

    Returns ``{"axes": [...], "bands": [...], "scale": {...},
    "provenance": {...} | None, "framing": str | None,
    "reading_note": str | None, "anti_gaming": [...],
    "worked_example": {...} | None}``. Degrades to empty structures on a
    missing or corrupt file; skips (never crashes on) invalid entries.
    """
    src = path or RUBRIC_JSON_PATH
    try:
        raw = json.loads(src.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return dict(_EMPTY)
    if not isinstance(raw, dict):
        return dict(_EMPTY)
    axes_raw = raw.get("axes")
    bands_raw = raw.get("bands")
    rules_raw = raw.get("anti_gaming")
    example = raw.get("worked_example")
    return {
        "axes": ([_load_axis(a) for a in axes_raw if _valid_axis(a)]
                 if isinstance(axes_raw, list) else []),
        "bands": ([_load_band(b) for b in bands_raw if _valid_band(b)]
                  if isinstance(bands_raw, list) else []),
        "scale": _load_scale(raw.get("scale")),
        "provenance": _load_provenance(raw.get("provenance")),
        "framing": raw["framing"] if _nonempty_str(raw.get("framing")) else None,
        "reading_note": (raw["reading_note"]
                         if _nonempty_str(raw.get("reading_note")) else None),
        "anti_gaming": ([r for r in rules_raw if _nonempty_str(r)]
                        if isinstance(rules_raw, list) else []),
        "worked_example": example if isinstance(example, dict) else None,
    }


def scorer_config(rubric: dict[str, Any]) -> str:
    """The client-side scorer's config, serialized once from the SAME loaded
    rubric the page renders — axes (id/name/weight), scale, verdict bands,
    and the reading note. Single-sourced: the JS never re-declares a weight
    or threshold."""
    config = json.dumps({
        "axes": [{"id": a["id"], "name": a["name"], "weight": a["weight"]}
                 for a in rubric["axes"]],
        "scale": rubric["scale"],
        "bands": rubric["bands"],
        "reading_note": rubric["reading_note"],
    })
    # Rendered raw inside a <script type="application/json"> tag — make a
    # literal "<" (e.g. "</script>") inert regardless of the data's content.
    return config.replace("<", "\\u003c")
