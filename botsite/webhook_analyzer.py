"""Webhook payload analyzer — loader for ``data/webhook_analyzer.json``.

The /webhook-analyzer page is a CLIENT-SIDE-ONLY tool for **the last
venture-lab batch-2 WEBSITE-IDEA marker** ("webhook-payload analyzer",
venture-lab ``control/outbox.md`` 2026-07-13 morning tally @ 0679327) under
ORDER 022 item 4. A visitor pastes a webhook JSON payload into a textarea
and vanilla in-browser JS parses and classifies it — provider detection
from body shape, a depth-capped field walk, and per-provider
signature-verification guidance. **Zero server involvement with pasted
data**: the route is GET-only, there is no form POST, and the analyzer JS
makes no network calls. The page states that privacy property prominently,
because it is the feature.

This module is a **read-only slice**: the analyzer's knowledge base
(provider detection markers, signature guidance, field notes, generic
heuristics) lives in a JSON file committed in this repo with an explicit
per-source provenance block. Read from disk at request time: **no network,
no secrets, stdlib only**.

Honesty rules (the "never fake data" doctrine, applied to a security-adjacent
tool page):

- A missing or corrupt file — or one whose providers all fail validation —
  degrades to ``None``; the page shows its honest empty state, never a crash
  and never invented guidance.
- Providers missing required fields are skipped, never fatal.
- Every signature-guidance line carries a source id from the provenance
  block. Stripe claims are the SWTK material already committed as
  ``botsite/data/stripe_gotchas.json`` (venture-lab @ 0679327); GitHub
  claims were verified against the official docs on the recorded fetch
  date; Discord's signature specifics were NOT verifiable from the page
  fetched this session, so that guidance is a bare pointer at the official
  docs — downgraded, not invented.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
ANALYZER_JSON_PATH = BASE_DIR / "data" / "webhook_analyzer.json"

_SOURCE_REQUIRED = ("id", "label")
_PROVIDER_REQUIRED = ("id", "name")
_MARKER_REQUIRED = ("id", "label")


def _nonempty_str(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _valid_source(entry: Any) -> bool:
    return (isinstance(entry, dict)
            and all(_nonempty_str(entry.get(f)) for f in _SOURCE_REQUIRED)
            and isinstance(entry.get("verified"), bool))


def _load_source(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": entry["id"],
        "label": entry["label"],
        "url": entry["url"] if _nonempty_str(entry.get("url")) else None,
        "detail": entry["detail"] if _nonempty_str(entry.get("detail")) else None,
        "verified": entry["verified"],
        "fetched": entry["fetched"] if _nonempty_str(entry.get("fetched")) else None,
    }


def _load_provenance(raw: Any) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    sources_raw = raw.get("sources")
    if not isinstance(sources_raw, list):
        return None
    sources = [_load_source(s) for s in sources_raw if _valid_source(s)]
    if not sources:
        return None
    return {
        "note": raw["note"] if _nonempty_str(raw.get("note")) else None,
        "sources": sources,
    }


def _valid_marker(entry: Any) -> bool:
    return (isinstance(entry, dict)
            and all(_nonempty_str(entry.get(f)) for f in _MARKER_REQUIRED))


def _valid_line(entry: Any) -> bool:
    return (isinstance(entry, dict)
            and _nonempty_str(entry.get("text"))
            and _nonempty_str(entry.get("source")))


def _valid_note(entry: Any) -> bool:
    return (isinstance(entry, dict)
            and _nonempty_str(entry.get("id"))
            and _nonempty_str(entry.get("text"))
            and _nonempty_str(entry.get("source")))


def _valid_provider(entry: Any) -> bool:
    if not isinstance(entry, dict):
        return False
    if not all(_nonempty_str(entry.get(f)) for f in _PROVIDER_REQUIRED):
        return False
    markers = entry.get("markers")
    if not isinstance(markers, list) or not markers:
        return False
    if not all(_valid_marker(m) for m in markers):
        return False
    sig = entry.get("signature")
    if not isinstance(sig, dict):
        return False
    lines = sig.get("lines")
    return (isinstance(lines, list) and bool(lines)
            and all(_valid_line(ln) for ln in lines))


def _load_provider(entry: dict[str, Any]) -> dict[str, Any]:
    sig = entry["signature"]
    marker_ids = {m["id"] for m in entry["markers"]}
    strong_raw = entry.get("strong_markers")
    prefixes_raw = entry.get("id_prefixes")
    notes_raw = entry.get("field_notes")
    return {
        "id": entry["id"],
        "name": entry["name"],
        "markers": [{"id": m["id"], "label": m["label"]} for m in entry["markers"]],
        # strong markers must name real markers — unknown ids are dropped
        "strong_markers": ([m for m in strong_raw if m in marker_ids]
                           if isinstance(strong_raw, list) else []),
        "id_prefixes": ({str(k): str(v) for k, v in prefixes_raw.items()
                         if _nonempty_str(k) and _nonempty_str(v)}
                        if isinstance(prefixes_raw, dict) else {}),
        "signature": {
            "header": (sig["header"] if _nonempty_str(sig.get("header")) else None),
            "lines": [{"text": ln["text"], "source": ln["source"]}
                      for ln in sig["lines"]],
        },
        "field_notes": ([{"id": n["id"], "text": n["text"], "source": n["source"]}
                         for n in notes_raw if _valid_note(n)]
                        if isinstance(notes_raw, list) else []),
    }


def _load_generic(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        return {"header_reminder": None, "heuristics": [], "limits": None}
    heuristics_raw = raw.get("heuristics")
    return {
        "header_reminder": (raw["header_reminder"]
                            if _nonempty_str(raw.get("header_reminder")) else None),
        "heuristics": ([{"id": h["id"], "label": h["label"]}
                        for h in heuristics_raw if _valid_marker(h)]
                       if isinstance(heuristics_raw, list) else []),
        "limits": raw["limits"] if _nonempty_str(raw.get("limits")) else None,
    }


def load_analyzer(path: Path | None = None) -> dict[str, Any] | None:
    """Load and validate the analyzer knowledge base from disk.

    Returns ``{"providers": [...], "generic": {...}, "provenance": {...} |
    None}`` — or ``None`` when the file is missing, corrupt, or carries no
    valid provider (the page then renders its honest unavailable state).
    Invalid providers/sources/notes are skipped, never fatal.
    """
    src = path or ANALYZER_JSON_PATH
    try:
        raw = json.loads(src.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(raw, dict):
        return None
    providers_raw = raw.get("providers")
    providers = ([_load_provider(p) for p in providers_raw if _valid_provider(p)]
                 if isinstance(providers_raw, list) else [])
    if not providers:
        return None
    return {
        "providers": providers,
        "generic": _load_generic(raw.get("generic")),
        "provenance": _load_provenance(raw.get("provenance")),
    }


def analyzer_config(data: dict[str, Any]) -> str:
    """The client-side analyzer's config, serialized once from the SAME
    loaded knowledge base the page renders — providers (markers, strong
    markers, id prefixes, signature guidance, field notes, with a source
    label resolved onto every guidance line) and the generic section.
    Single-sourced: the JS never re-declares a marker or a guidance claim."""
    sources = {s["id"]: s for s in (data.get("provenance") or {}).get("sources", [])}

    def _line(ln: dict[str, Any]) -> dict[str, Any]:
        src = sources.get(ln["source"])
        return {
            "text": ln["text"],
            "source_label": src["label"] if src else ln["source"],
            "source_url": src["url"] if src else None,
            "verified": src["verified"] if src else False,
        }

    config = json.dumps({
        "providers": [
            {
                "id": p["id"],
                "name": p["name"],
                "markers": p["markers"],
                "strong_markers": p["strong_markers"],
                "id_prefixes": p["id_prefixes"],
                "signature": {
                    "header": p["signature"]["header"],
                    "lines": [_line(ln) for ln in p["signature"]["lines"]],
                },
                "field_notes": [_line(n) | {"id": n["id"]}
                                for n in p["field_notes"]],
            }
            for p in data["providers"]
        ],
        "generic": data["generic"],
    })
    # Rendered raw inside a <script type="application/json"> tag — make a
    # literal "<" (e.g. "</script>") inert regardless of the data's content.
    return config.replace("<", "\\u003c")
