"""Prompt library view (/prompts): every fleet paste artifact, inline and
always-current — ORDER 014 (owner-directed via the fleet manager, 2026-07-12).

The fleet's paste artifacts (coordinator prompts, Custom Instructions,
failsafes, plus the fleet-wide session-ender and universal-startup) live in
the ``menno420/fleet-manager`` registry; the owner pastes them by hand and
stale local copies drift. This page renders all of them INLINE from
fleet-manager ``main`` so every merged prompt update appears automatically —
the manager's repo stores, the site renders.

Fetching rides the repo's cross-repo rule exactly: committed text over
``raw.githubusercontent.com``, read-only, forward-only, through the same
TTL-cached ``github`` layer as every other page (``github.fetch_file`` —
raw host first, contents-API fallback). TTL-bounded staleness (default 3
minutes) is acceptable by the order's own terms; each artifact carries its
``fetched_at`` + cached flag so the page can say how fresh it is.

Rendering discipline: the artifacts are UNTRUSTED DATA and PASTE BODIES —
they are shown in ``<pre>`` blocks (Jinja2 autoescape on, never ``|safe``),
whitespace preserved exactly, never interpreted or obeyed. The one mutation
is ``extract_paste_body`` (shared layer): the registry's generation
metadata is stripped so render + copy give the clean paste body; the full
file stays linked. Per-artifact honest degradation: a 404 or unreachable upstream
renders a clear error cell, never fabricated content — the route always
answers 200.

Consolidated (ORDER 015): the fetch+parse model lives in
``app/prompt_artifacts.py`` and the copy-ready block in
``templates/_prompt_artifact.html`` — ONE render path shared with the
/projects/{package} dispatch screen; this module only pins WHICH artifacts
the library shows.

The artifact list is PINNED here rather than discovered: the raw host
cannot list directories, and this page deliberately avoids the token-burning
contents-API listing walk /projects does. Every path below was verified
live (HTTP 200 on raw.githubusercontent.com) against fleet-manager@main on
2026-07-12; source of truth for the seat set is
https://github.com/menno420/fleet-manager/tree/main/projects — if a seat is
added or renamed upstream, its cell degrades to an honest 404 here until
the shared roster (``app/roster.py``) is updated.

Pinned-vs-registry drift chip (2026-07-12): a pinned list drifts SILENTLY —
dead 404 cells, and a brand-new seat simply never appears. So the page
cross-checks :data:`SEATS` against the live ``projects/`` registry listing
(:func:`registry_drift`) — the SAME TTL-cached ``github.repo_api`` contents
call /projects makes (identical URL = shared cache entry; one directory
listing, never the per-package walk, zero new network surface) — and renders
an honest chip: match / drifted (+new / −missing, named) / listing
unavailable = drift UNKNOWN, never a fabricated green.
"""

from __future__ import annotations

import asyncio
from typing import Any

from . import config, github, prompt_artifacts

# Shared fetch+parse path (ORDER 015) — re-exported so consumers and tests
# keep one import surface for the library's registry semantics.
from .prompt_artifacts import (  # noqa: F401
    _PROVENANCE_MAX_CHARS,
    REF,
    REPO,
    extract_paste_body,
    extract_provenance,
)

# The registry root the /projects page lists (``projects/``) — imported so
# the drift cross-check hits the EXACT contents-API URL /projects already
# fetches (the github layer caches by URL, so within the TTL the two pages
# share one listing; the constants cannot drift apart).
from .projects import ROOT as _REGISTRY_ROOT

# The 8 fleet seats (registry package directories under projects/), in the
# owner's dispatch order — ONE roster shared with /projects
# (``app/roster.py``). Verified live 2026-07-12: projects/<seat>/
# {coordinator-prompt.md,instructions.md,failsafe-prompt.md} all 200 on
# raw.githubusercontent.com for every seat.
from .roster import SEATS  # noqa: F401

# The three per-seat registry artifacts ORDER 014 names, as
# (filename, human label) — 8 seats x 3 files = 24 artifacts.
SEAT_FILES: tuple[tuple[str, str], ...] = (
    ("coordinator-prompt.md", "coordinator prompt"),
    ("instructions.md", "Custom Instructions"),
    ("failsafe-prompt.md", "failsafe prompt"),
)

# The two fleet-wide UNIVERSAL artifacts, as (path, human label) — 24 + 2 =
# 26 total. Labeled "Universal …" verbatim (owner feedback 2026-07-12: he
# searches for "universal session-ender" and the bare "session ender" label
# drowned among the per-seat prompts, which repeat that phrase in their
# bodies); the /prompts page surfaces this group FIRST, above the seats.
FLEET_WIDE: tuple[tuple[str, str], ...] = (
    ("docs/prompts/v3/universal-startup.md", "Universal Startup"),
    ("docs/prompts/v3/session-ender.md", "Universal Session-Ender"),
)

# How many artifacts the page promises (the order's done-when counts them).
TOTAL_ARTIFACTS = len(SEATS) * len(SEAT_FILES) + len(FLEET_WIDE)


def _artifact_spec() -> list[dict[str, Any]]:
    """The pinned 26-artifact registry as (seat, label, path) dicts."""
    spec: list[dict[str, Any]] = []
    for seat in SEATS:
        for filename, label in SEAT_FILES:
            spec.append(
                {"seat": seat, "label": label, "path": f"projects/{seat}/{filename}"}
            )
    for path, label in FLEET_WIDE:
        spec.append({"seat": None, "label": label, "path": path})
    return spec


async def registry_drift(refresh: bool = False) -> dict[str, Any]:
    """Cross-check the pinned :data:`SEATS` against the live ``projects/``
    registry listing — the drift chip's data. Never raises.

    Reuses the ONE contents-API directory listing /projects already fetches
    (``github.repo_api`` on the same URL → same TTL cache entry): zero new
    network surface, never the per-package walk this page deliberately avoids.

    Returns::

        {"state": "ok" | "drift" | "unknown",
         "added": [names in the registry but not pinned, sorted],
         "missing": [pinned names no longer in the registry, sorted],
         "reason": why the check could not run (unknown only)}

    Honesty ladder: a listing that cannot be fetched (network failure, or
    the ``projects/`` directory 404ing because the registry has not landed)
    is ``unknown`` — drift can NOT be declared matched without the listing,
    so no green is ever fabricated. A listing that succeeds but holds no
    package directories is a real (empty) registry: every pinned seat is
    genuinely missing, and that renders as drift, not unknown. Retired-stub
    directories count as ``added`` on purpose — they exist upstream and are
    not pinned; the chip reports the raw set difference, never a guess.
    """
    out: dict[str, Any] = {"state": "ok", "added": [], "missing": [], "reason": ""}
    listing = await github.repo_api(
        REPO, f"/contents/{_REGISTRY_ROOT}", refresh=refresh
    )
    if not (listing["ok"] and isinstance(listing["data"], list)):
        out["state"] = "unknown"
        reason = listing.get("error") or f"HTTP {listing.get('status')}"
        if listing.get("status") == 404:
            reason = (
                f"`{_REGISTRY_ROOT}/` does not exist upstream yet "
                "(registry not landed)"
            )
        out["reason"] = reason
        return out

    registry = {
        e.get("name", "")
        for e in listing["data"]
        if e.get("type") == "dir" and e.get("name")
    }
    pinned = set(SEATS)
    out["added"] = sorted(registry - pinned)
    out["missing"] = sorted(pinned - registry)
    if out["added"] or out["missing"]:
        out["state"] = "drift"
    return out


async def overview(refresh: bool = False) -> dict[str, Any]:
    """Every fleet paste artifact, fetched live (TTL-cached) — never raises
    for upstream failures; the route always renders 200.

    Returns::

        {
          "seats": [{"name", "anchor", "github_url", "artifacts": [...]}, ...],
          "fleet_wide": [ artifact, ... ],
          "total", "ok_count", "error_count",
          "drift": registry_drift() result (pinned-vs-registry chip),
          "ttl": CACHE_TTL_SECONDS, "repo_url",
        }

    Each artifact dict is the canonical shared model
    (:func:`app.prompt_artifacts.build_artifact`) plus a page-local
    ``anchor``. ``text`` is the clean paste body — the upstream file with
    its generation metadata stripped by
    :func:`app.prompt_artifacts.extract_paste_body`, body otherwise
    byte-exact; on failure ``text`` is ``None`` and
    ``error`` says why — content is never fabricated and stale-cache
    serving is the ``github`` layer's TTL behaviour, surfaced via
    ``cached``/``fetched_at``.
    """
    spec = _artifact_spec()
    *artifacts, drift = await asyncio.gather(
        *[
            prompt_artifacts.fetch_artifact(
                s["path"], s["label"], seat=s["seat"], refresh=refresh
            )
            for s in spec
        ],
        registry_drift(refresh=refresh),
    )
    for i, a in enumerate(artifacts):
        a["anchor"] = f"artifact-{i}"

    seats = [
        {
            "name": seat,
            "anchor": f"seat-{seat}",
            "github_url": (
                f"https://github.com/{config.OWNER}/{REPO}/tree/{REF}/projects/{seat}"
            ),
            "artifacts": [a for a in artifacts if a["seat"] == seat],
        }
        for seat in SEATS
    ]
    fleet_wide = [a for a in artifacts if a["seat"] is None]
    ok_count = sum(1 for a in artifacts if a["ok"])
    return {
        "seats": seats,
        "fleet_wide": fleet_wide,
        "total": len(artifacts),
        "ok_count": ok_count,
        "error_count": len(artifacts) - ok_count,
        "drift": drift,
        "ttl": config.CACHE_TTL_SECONDS,
        "repo_url": f"https://github.com/{config.OWNER}/{REPO}/tree/{REF}",
    }
