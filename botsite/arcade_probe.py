"""Arcade live-URL drift probe — cold-fetches every ``availability: "live"``
URL in the committed ``data/arcade.json`` and flags any that stop returning
HTTP 200.

Why (docs/ideas/backlog.md, "Arcade live-URL drift probe", ORDER 022 drift
session): the arcade honesty doctrine says a play link is only rendered for a
really-reachable game, but nothing re-verifies a live URL after its card
ships — a dead deployment silently outlives its card until a human reconciles
by hand (ORDER 022 flipped mineverse manually). This module is the automated
reconcile: it is consumed by ``scripts/healthcheck.py`` (the 6-hourly
scheduled healthcheck), which is the ONLY place the real network fetch runs.
The required ``quality`` CI gate never touches the network — the botsite app
never imports this module, and its tests exercise it exclusively through
``httpx.MockTransport``.

Design contract:

- **Fail-soft per URL**: every per-URL failure (non-200 status, timeout,
  connection error, malformed or missing URL, any surprise exception) becomes
  a FLAGGED finding row; ``probe_live_urls`` itself never raises. Whether a
  flagged finding affects exit status is the CALLER's convention
  (``healthcheck.py`` folds it into its exit-1-on-any-failure idiom).
- **Redirects are followed** (``follow_redirects=True``): today's only live
  URL is a bare Railway host (``https://web-production-97636.up.railway.app``)
  and hosting moves often interpose a 301/308 — a live game behind a redirect
  is still live. The FINAL response must be 200.
- **Honest coverage**: non-live entries are returned as ``skipped`` (slug +
  availability) so the caller can print an explicit "not probed" line — the
  probe never implies coverage it does not have. A registry that loads to
  ZERO entries is itself a flagged condition (missing/corrupt file suspected
  — the committed registry lists three games), mirroring the healthcheck's
  fleet-registry zero-lanes alert.
- Reads the registry through the SAME loader the /arcade page renders with
  (``botsite.arcade.load_games``), so probe coverage and page content can
  never disagree about what "live" means.
"""

from __future__ import annotations

import urllib.parse
from pathlib import Path
from typing import Any

import httpx

from . import arcade

TIMEOUT_S = 10.0
EXPECTED_STATUS = 200
USER_AGENT = "websites-healthcheck-arcade-probe"


def make_client() -> httpx.Client:
    """The real-network client used by scripts/healthcheck.py. Tests never
    call this — they inject an ``httpx.Client(transport=MockTransport(...))``."""
    return httpx.Client(
        timeout=TIMEOUT_S,
        follow_redirects=True,
        headers={"User-Agent": USER_AGENT},
    )


def probe_url(url: str, client: httpx.Client) -> tuple[bool, str]:
    """GET one URL; return ``(ok, note)``. Never raises — every failure mode
    degrades to a ``(False, reason)`` finding."""
    try:
        parts = urllib.parse.urlsplit(url)
    except ValueError as exc:
        return False, f"malformed URL ({exc})"
    if parts.scheme not in ("http", "https") or not parts.netloc:
        return False, f"malformed URL (no http(s) scheme/host in {url!r})"
    try:
        resp = client.get(url)
    except httpx.TimeoutException as exc:
        return False, f"timeout after {TIMEOUT_S:g}s ({type(exc).__name__})"
    except httpx.HTTPError as exc:
        return False, f"connection error ({type(exc).__name__}: {exc})"
    except Exception as exc:  # fail-soft: any surprise is a finding, not a crash
        return False, f"probe error ({type(exc).__name__}: {exc})"
    if resp.status_code == EXPECTED_STATUS:
        return True, str(EXPECTED_STATUS)
    return False, f"HTTP {resp.status_code}"


def probe_live_urls(
    path: Path | None = None, client: httpx.Client | None = None
) -> dict[str, Any]:
    """Probe every live-availability entry in the arcade registry.

    Returns a summary dict — never raises:

    - ``rows``: probed entries, each ``{"slug", "url", "ok", "note"}``
    - ``flagged``: the subset of ``rows`` with ``ok`` False
    - ``skipped``: non-live entries, each ``{"slug", "availability"}`` —
      honestly NOT probed
    - ``ok``: True iff the registry loaded non-empty and nothing was flagged
    - ``note``: one-line headline (counts, or the zero-entries alert)
    """
    games = arcade.load_games(path)
    if not games:
        return {
            "rows": [],
            "flagged": [],
            "skipped": [],
            "ok": False,
            "note": "registry loaded ZERO entries — missing/corrupt arcade.json suspected",
        }

    rows: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    own_client = client is None
    cli = client or make_client()
    try:
        for game in games:
            slug = game["slug"]
            if game["availability"] != "live":
                skipped.append({"slug": slug, "availability": game["availability"]})
                continue
            url = game.get("url")
            if not url:
                rows.append(
                    {"slug": slug, "url": None, "ok": False,
                     "note": 'availability "live" but no URL to probe'}
                )
                continue
            ok, note = probe_url(url, cli)
            rows.append({"slug": slug, "url": url, "ok": ok, "note": note})
    finally:
        if own_client:
            cli.close()

    flagged = [row for row in rows if not row["ok"]]
    note = (
        f"{len(rows)} live URL(s) probed, {len(flagged)} flagged, "
        f"{len(skipped)} non-live entr{'y' if len(skipped) == 1 else 'ies'} not probed"
    )
    return {
        "rows": rows,
        "flagged": flagged,
        "skipped": skipped,
        "ok": not flagged,
        "note": note,
    }
