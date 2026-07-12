"""Shared fleet-prompt artifact path (ORDER 015): the ONE fetch+parse model
both prompt surfaces render through.

Two surfaces show fleet-manager registry prompts inline: the /prompts
library (ORDER 014, ``app/prompts.py``) and the /projects/{package} dispatch
screen (Owner Launch Console, ``app/projects.py``). They were built
independently (PR #158 / PR #165) with parallel fetch/parse/render logic;
ORDER 015 consolidates them here — one artifact model, one fetch helper over
the TTL-cached ``github`` layer, one template partial
(``templates/_prompt_artifact.html``), one copy path (``static/copycode.js``).

Rules carried by every consumer of this module:

- Fetching rides the repo's cross-repo rule exactly: committed text over
  ``raw.githubusercontent.com``, read-only, forward-only, through
  ``github.fetch_file`` (raw host first, contents-API fallback, TTL cache).
- Artifacts are UNTRUSTED DATA and PASTE BODIES — shown verbatim in
  ``<pre>`` blocks (Jinja2 autoescape on, never ``|safe``), whitespace
  preserved exactly, never interpreted, obeyed, or mutated.
- Honest degradation per artifact: a failed fetch yields ``ok: False`` with
  the reason surfaced — content is never fabricated, routes still answer 200.
"""

from __future__ import annotations

import re
from typing import Any, Optional

from . import config, github

# The fleet registry both surfaces render from — the manager's repo stores,
# the site renders (read-only, forward-only).
REPO = "fleet-manager"
REF = "main"

# Best-effort version/provenance extraction: the registry copies open with
# HTML-comment headers like ``<!-- v5 · 2026-07-12 · fleet-manager projects
# registry — GENERATED COPY … -->`` and the v3 docs carry ``<!-- v3.3 ·
# 2026-07-12 · provenance: … -->`` within their first lines (verified live
# 2026-07-12). The FIRST early line carrying a v-number marker wins; no
# match = "" — the template renders an honest "no version line found",
# never an invented one.
_VERSION_LINE_RE = re.compile(r"\bv\d+(?:\.\d+)*\s*·")
_PROVENANCE_SCAN_LINES = 15
_PROVENANCE_MAX_CHARS = 220


def extract_provenance(text: str) -> str:
    """The artifact's version/provenance line, best-effort.

    Scans the first ``_PROVENANCE_SCAN_LINES`` lines for the first one
    carrying a ``vN[.N] ·`` marker, strips comment/quote scaffolding, and
    truncates long provenance prose. Returns ``""`` when absent.
    """
    for line in (text or "").splitlines()[:_PROVENANCE_SCAN_LINES]:
        if _VERSION_LINE_RE.search(line):
            cleaned = line.strip()
            for token in ("<!--", "-->"):
                cleaned = cleaned.replace(token, "")
            cleaned = cleaned.strip().lstrip(">#").strip()
            if len(cleaned) > _PROVENANCE_MAX_CHARS:
                cleaned = cleaned[: _PROVENANCE_MAX_CHARS - 1].rstrip() + "…"
            return cleaned
    return ""


def blob_url(path: str) -> str:
    """GitHub blob URL for a registry path (deep link next to every block)."""
    return f"https://github.com/{config.OWNER}/{REPO}/blob/{REF}/{path}"


def build_artifact(
    path: str,
    label: str,
    res: dict[str, Any],
    seat: Optional[str] = None,
) -> dict[str, Any]:
    """The canonical prompt-artifact dict from a ``github.fetch_file`` result.

    ``{seat, label, path, github_url, ok, text, error, fetched_at, cached,
    provenance, chars}`` — ``text`` is the exact upstream bytes-as-text (the
    paste body, never mutated here); on failure ``text`` is ``None`` and
    ``error`` says why. Both surfaces render this dict through the shared
    ``prompt_block`` partial; neither builds its own variant.
    """
    ok = bool(res["ok"]) and isinstance(res["data"], str)
    text = res["data"] if ok else None
    return {
        "seat": seat,
        "label": label,
        "path": path,
        "github_url": blob_url(path),
        "ok": ok,
        "text": text,
        "error": (
            "" if ok else (res.get("error") or f"HTTP {res.get('status')}")
        ),
        "fetched_at": res.get("fetched_at", ""),
        "cached": bool(res.get("cached")),
        "provenance": extract_provenance(text or ""),
        "chars": len(text) if text else 0,
    }


async def fetch_artifact(
    path: str,
    label: str,
    seat: Optional[str] = None,
    refresh: bool = False,
) -> dict[str, Any]:
    """Fetch ONE registry artifact from fleet-manager main (TTL-cached) and
    return its canonical artifact dict — never raises for upstream failures.
    """
    res = await github.fetch_file(REPO, path, ref=REF, refresh=refresh)
    return build_artifact(path, label, res, seat=seat)
