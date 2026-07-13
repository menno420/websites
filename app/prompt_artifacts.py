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
- Artifacts are UNTRUSTED DATA and PASTE BODIES — shown in ``<pre>``
  blocks (Jinja2 autoescape on, never ``|safe``), whitespace preserved
  exactly, never interpreted or obeyed. The ONE mutation applied is
  :func:`extract_paste_body`: the registry's generation metadata (comment
  headers, GENERATED COPY / char-count blockquotes, the
  ``registry-header-end`` marker) is stripped so render and copy present
  only the clean paste body; the full file stays one click away via the
  per-artifact GitHub link.
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


# Supersession / do-not-paste markers (ORDER 022 item 3): an artifact whose
# OWN header disclaims being the paste source must not render
# indistinguishably from the pasteable ones. The one real marker today is
# universal-startup.md line 5 — a FULL-LINE comment: "⚠ v3.3 (2026-07-12):
# SUPERSEDED AS THE GENERATION SOURCE — historical template, … Do not paste
# this file; do not regenerate from it." (verified live 2026-07-13). Because
# extract_paste_body STRIPS full-line comments, the matcher runs on the RAW
# upstream text (same convention as extract_provenance), header region only.
#
# Conservative by design — strong signals only, ambiguity = no warning:
# - the STANDALONE ALL-CAPS token `SUPERSEDED` (never lowercase "supersedes":
#   every current per-seat registry copy's header says "Version lineage: vN
#   (…) supersedes the prior registry sync copy" and is CURRENT);
# - "do not paste" (case-insensitive);
# - "historical template" (case-insensitive).
# NOT matched (all verified-current phrasing upstream): bare "retired" /
# "RETIRED" ("the v3.1/v3.2 core+seat-block assembly is RETIRED" describes
# the assembly, not the file), body prose like "this table supersedes any
# cron previously recorded", and session-ender's "THIS file stays the
# canonical single source".
_SUPERSESSION_SIGNALS: tuple[tuple[str, "re.Pattern[str]"], ...] = (
    ("SUPERSEDED", re.compile(r"\bSUPERSEDED\b")),  # caps token only
    ("do not paste", re.compile(r"\bdo not paste\b", re.IGNORECASE)),
    ("historical template", re.compile(r"\bhistorical template\b", re.IGNORECASE)),
)
_SUPERSESSION_LINE_MAX_CHARS = 300
# Successor extraction: ONLY an explicit single naming on the marker line —
# one markdown link, or one "see <path>.md" — otherwise None (the real
# marker names the per-seat startups generically; a link is never invented).
_SUCCESSOR_MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
_SUCCESSOR_SEE_RE = re.compile(r"\bsee\s+`?([\w./-]+\.md)`?", re.IGNORECASE)


def extract_supersession(text: str) -> Optional[dict[str, Any]]:
    """A supersession/do-not-paste marker in the artifact's RAW header, or
    ``None``.

    Scans only the first ``_PROVENANCE_SCAN_LINES`` RAW lines (the marker
    lives in the comment header extract_paste_body strips), and only lines
    in the header region — HTML-comment lines/blocks, blockquotes, headings;
    a strong phrase in plain body text does not flag. Returns
    ``{"phrase": <matched strong phrase>, "line": <marker line, comment
    delimiters stripped, truncated>, "successor": <path/url or None>}``.
    """
    in_comment = False
    for line in (text or "").splitlines()[:_PROVENANCE_SCAN_LINES]:
        s = line.strip()
        was_in_comment = in_comment
        if in_comment and "-->" in s:
            in_comment = False
        opens_comment = s.startswith("<!--")
        if opens_comment and "-->" not in s:
            in_comment = True
        header_region = (
            was_in_comment
            or opens_comment
            or s.startswith(">")
            or s.startswith("#")
        )
        if not header_region:
            continue
        for phrase, pattern in _SUPERSESSION_SIGNALS:
            if pattern.search(s):
                cleaned = s
                for token in ("<!--", "-->"):
                    cleaned = cleaned.replace(token, "")
                cleaned = cleaned.strip().lstrip(">#").strip()
                if len(cleaned) > _SUPERSESSION_LINE_MAX_CHARS:
                    cleaned = (
                        cleaned[: _SUPERSESSION_LINE_MAX_CHARS - 1].rstrip()
                        + "…"
                    )
                # all naming candidates on the marker line — a successor is
                # linked only when exactly ONE file is named, else None.
                candidates = list(dict.fromkeys(
                    _SUCCESSOR_MD_LINK_RE.findall(s)
                    + _SUCCESSOR_SEE_RE.findall(s)
                ))
                successor = candidates[0] if len(candidates) == 1 else None
                return {
                    "phrase": phrase,
                    "line": cleaned,
                    "successor": successor,
                }
    return None


# The registry's authoritative end-of-header marker (per-seat instructions.md
# artifacts carry it; the paste body is everything AFTER it). Artifacts
# without the marker (coordinator/failsafe prompts, the universals) instead
# open with comment headers + provenance/budget blockquotes that
# extract_paste_body strips heuristically.
REGISTRY_HEADER_END = "<!-- registry-header-end -->"

# Header-region blockquote lines that are generation metadata, not body:
# the "> **GENERATED COPY — NOT SOURCE OF TRUTH** …" provenance quote and
# the "> char-count: … / budget …" budget quote.
_META_QUOTE_RE = re.compile(
    r"generated copy|not source of truth|char-count|budget", re.IGNORECASE
)


def _drop_full_line_comments(text: str) -> str:
    """Remove full-line HTML comment lines/blocks (``<!-- … -->``, possibly
    spanning lines) anywhere in ``text`` — the paste body must never carry
    generator comments. Lines with inline (mid-line) comments are body text
    and pass through untouched."""
    kept: list[str] = []
    in_comment = False
    for line in text.splitlines(keepends=True):
        s = line.strip()
        if in_comment:
            if "-->" in s:
                in_comment = False
            continue
        if s.startswith("<!--"):
            if "-->" not in s:
                in_comment = True
            continue
        kept.append(line)
    return "".join(kept)


def extract_paste_body(text: str) -> str:
    """The clean paste body of a registry artifact — what the page renders
    and the copy button copies.

    Rules, in order:

    - If ``<!-- registry-header-end -->`` appears (per-seat instructions.md
      artifacts), the body is everything AFTER that marker — the
      authoritative delimiter.
    - Otherwise strip from the top, until the first real content line:
      full HTML comment blocks (single- or multi-line), the
      ``> **GENERATED COPY …`` provenance blockquote (with its ``>``
      continuation lines), the ``> char-count: … / budget`` blockquote,
      and blank lines between them.
    - Either way, any remaining FULL-LINE comment lines/blocks anywhere in
      the body are removed, and leading blank lines are stripped.

    Already-clean text passes through unchanged (idempotent, apart from
    leading-blank stripping). The body itself is otherwise never mutated —
    whitespace and content are preserved exactly.
    """
    if not text:
        return ""
    if REGISTRY_HEADER_END in text:
        body = text.split(REGISTRY_HEADER_END, 1)[1]
    else:
        lines = text.splitlines(keepends=True)
        i = 0
        in_comment = False
        in_meta_quote = False
        while i < len(lines):
            s = lines[i].strip()
            if in_comment:
                if "-->" in s:
                    in_comment = False
                i += 1
                continue
            if s.startswith("<!--"):
                if "-->" not in s:
                    in_comment = True
                in_meta_quote = False
                i += 1
                continue
            if not s:
                in_meta_quote = False
                i += 1
                continue
            if s.startswith(">") and (_META_QUOTE_RE.search(s) or in_meta_quote):
                in_meta_quote = True
                i += 1
                continue
            break  # first real content line — the body starts here
        body = "".join(lines[i:])
    body = _drop_full_line_comments(body)
    out = body.splitlines(keepends=True)
    j = 0
    while j < len(out) and not out[j].strip():
        j += 1
    return "".join(out[j:])


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
    provenance, chars, superseded}`` — ``text`` is the CLEAN PASTE BODY
    (:func:`extract_paste_body` over the upstream text: generation metadata
    stripped, body otherwise byte-exact); ``provenance`` and the GitHub link
    keep the full file's metadata reachable. On failure ``text`` is ``None``
    and ``error`` says why. Both surfaces render this dict through the
    shared ``prompt_block`` partial; neither builds its own variant.
    """
    ok = bool(res["ok"]) and isinstance(res["data"], str)
    raw = res["data"] if ok else None
    text = extract_paste_body(raw) if ok else None
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
        # provenance comes from the FULL upstream text — the version line
        # usually lives in the very header extract_paste_body strips.
        "provenance": extract_provenance(raw or ""),
        "chars": len(text) if text else 0,
        # supersession marker from the RAW header (the comment lines
        # extract_paste_body strips); None on fetch failure — a warning is
        # never invented for content that could not be read.
        "superseded": extract_supersession(raw or "") if ok else None,
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
