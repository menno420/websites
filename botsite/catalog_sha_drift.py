"""Catalog sha-drift probe — flags when a vetting packet changed upstream
since the committed catalog pinned it.

Why (docs/ideas/backlog.md, "Catalog sha-drift pin", 2026-07-13,
venture-vetting-catalog session): every entry in ``data/catalog.json``
(PR #248) carries a ``source`` field pinning its provenance —
``"<repo> <path> @ <sha>"``, e.g. ``"venture-lab
docs/publishing/vetting/stripe-webhook-test-kit.md @ 2c039e3"`` — but
nothing ever re-checks that pin against reality. A 22-entry hand-curated
registry decays the moment the vetting lane moves: a title going live
upstream while the catalog still says publish-ready is exactly the
dishonesty the /products/catalog page exists to avoid.

This module cold-fetches, for each entry, the packet's content AT its
pinned sha and AT the source repo's current ``main`` — both over
``raw.githubusercontent.com`` (the read-only, forward-only channel the
fleet already uses for cross-repo data; no GitHub REST API, no token,
same doctrine as ``app/github.py``'s raw-content path). A byte difference
means the packet moved upstream since the catalog pinned it: the status,
price, or verdict this repo committed may no longer match the source of
truth.

Design contract (matches ``botsite/arcade_probe.py``'s shape):

- **Fail-soft per entry**: an unfetchable pinned sha or HEAD, a
  non-pinned-provenance ``source`` string, or any surprise exception
  becomes a per-entry finding, never a crash. ``probe_catalog_sha_drift``
  itself never raises.
- **Real network runs ONLY in ``scripts/healthcheck.py``** (the scheduled
  healthcheck). The required ``quality`` CI gate never touches the
  network — botsite never imports this module at request time, and its
  tests exercise it exclusively through ``httpx.MockTransport``.
- Reads the registry through the SAME loader the /products/catalog page
  renders from (``botsite.catalog.load_catalog``), so probe coverage and
  page content can never disagree about which entries exist.
- An entry whose ``source`` doesn't match the pinned-provenance shape
  (free text, or missing the ``@ <sha>`` suffix) is honestly SKIPPED, not
  flagged — this probe verifies a pin, it does not invent one.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import httpx

from . import catalog

TIMEOUT_S = 10.0
USER_AGENT = "websites-healthcheck-catalog-sha-drift-probe"
RAW_BASE = "https://raw.githubusercontent.com"
OWNER = "menno420"

# The catalog's pinned-provenance ``source`` shape: "<repo> <path> @ <sha>".
# Repo and path are non-space tokens (this fleet's repo/path conventions
# never carry spaces); the sha is 7-40 lowercase hex (short or full).
_SOURCE_RE = re.compile(r"^(\S+)\s+(\S+)\s+@\s+([0-9a-f]{7,40})$")


def parse_source(source: str) -> tuple[str, str, str] | None:
    """``(repo, path, sha)`` from a catalog entry's ``source`` field, or
    ``None`` when it isn't pinned-provenance shaped."""
    m = _SOURCE_RE.match((source or "").strip())
    if not m:
        return None
    return m.group(1), m.group(2), m.group(3)


def make_client() -> httpx.Client:
    """The real-network client used by scripts/healthcheck.py. Tests never
    call this — they inject an ``httpx.Client(transport=MockTransport(...))``."""
    return httpx.Client(
        timeout=TIMEOUT_S,
        follow_redirects=True,
        headers={"User-Agent": USER_AGENT},
    )


def _fetch(client: httpx.Client, repo: str, ref: str, path: str) -> tuple[bool, str]:
    """GET one raw-content ref; ``(True, text)`` or ``(False, reason)``.
    Never raises — every failure mode degrades to a finding."""
    url = f"{RAW_BASE}/{OWNER}/{repo}/{ref}/{path}"
    try:
        resp = client.get(url)
    except httpx.TimeoutException as exc:
        return False, f"timeout after {TIMEOUT_S:g}s ({type(exc).__name__})"
    except httpx.HTTPError as exc:
        return False, f"connection error ({type(exc).__name__}: {exc})"
    except Exception as exc:  # fail-soft: any surprise is a finding, not a crash
        return False, f"probe error ({type(exc).__name__}: {exc})"
    if resp.status_code != 200:
        return False, f"HTTP {resp.status_code}"
    return True, resp.text


def probe_catalog_sha_drift(
    path: Path | None = None, client: httpx.Client | None = None
) -> dict[str, Any]:
    """Probe every pinned-provenance catalog entry for upstream drift.

    Returns a summary dict — never raises:

    - ``rows``: probed entries, each ``{"slug", "repo", "source_path",
      "sha", "ok", "note"}``
    - ``flagged``: the subset of ``rows`` with ``ok`` False
    - ``skipped``: entries whose ``source`` isn't pinned-provenance shaped,
      each ``{"slug", "source"}`` — honestly NOT probed
    - ``ok``: True iff the registry loaded non-empty and nothing was flagged
    - ``note``: one-line headline (counts, or the zero-entries alert)
    """
    entries = catalog.load_catalog(path)
    if not entries:
        return {
            "rows": [],
            "flagged": [],
            "skipped": [],
            "ok": False,
            "note": "registry loaded ZERO entries — missing/corrupt catalog.json suspected",
        }

    rows: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    own_client = client is None
    cli = client or make_client()
    try:
        for entry in entries:
            slug = entry["slug"]
            source = entry.get("source", "")
            parsed = parse_source(source)
            if parsed is None:
                skipped.append({"slug": slug, "source": source})
                continue
            repo, source_path, sha = parsed
            base = {"slug": slug, "repo": repo, "source_path": source_path, "sha": sha}

            ok_pin, pinned = _fetch(cli, repo, sha, source_path)
            if not ok_pin:
                rows.append({**base, "ok": False, "note": f"pinned sha unreachable ({pinned})"})
                continue
            ok_head, head = _fetch(cli, repo, "main", source_path)
            if not ok_head:
                rows.append({**base, "ok": False, "note": f"main unreachable ({head})"})
                continue
            if pinned == head:
                rows.append({**base, "ok": True, "note": "unchanged since pin"})
            else:
                rows.append(
                    {**base, "ok": False,
                     "note": "packet changed upstream since pin — re-verify against venture-lab"}
                )
    finally:
        if own_client:
            cli.close()

    flagged = [row for row in rows if not row["ok"]]
    note = (
        f"{len(rows)} pinned entr{'y' if len(rows) == 1 else 'ies'} checked, "
        f"{len(flagged)} flagged, {len(skipped)} not pinned-provenance-shaped (not probed)"
    )
    return {
        "rows": rows,
        "flagged": flagged,
        "skipped": skipped,
        "ok": len(flagged) == 0,
        "note": note,
    }
