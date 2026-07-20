"""ORDER 021: the web-presence directory — every web surface we own, one page.

Single source of truth is the committed registry ``app/data/web_presence.json``
(other seats add rows by PR). It is read from disk AT REQUEST TIME (no build
step; the file is tiny), and liveness is probed through the SAME shared
TTL-cached raw fetch the readiness board's deploy-drift cell rides
(``github._get(url, raw=True)`` — the raw client carries no GitHub token, so
nothing leaks to third-party hosts). Honesty rules, matching the rest of the
console:

* a probe result is never invented — ``live`` requires an actual 2xx from the
  target this TTL window; any other HTTP answer is ``degraded (HTTP n)``, a
  network failure is ``down``, and a row with no URL renders an honest
  "nothing to probe" state, never a green badge or a dead button;
* duplicate rows (the reliable-grace parallel copies of the websites estate,
  pending OQ-RAILWAY-PROJECT-SPLIT) stay labeled duplicates — the directory
  must not present them as distinct products;
* a malformed/unreadable registry degrades to a banner on a 200 page,
  never a 500.

Registry content is untrusted DATA: it is passed to the template as plain
values and autoescaped there — never marked safe, never interpolated into
markup here.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from . import github

REGISTRY_PATH = Path(__file__).parent / "data" / "web_presence.json"

# Row statuses the registry may carry (documented in the JSON's schema_note).
KNOWN_STATUSES = {"live-service", "duplicate", "url-unrecorded", "pending-publish"}


def load_registry(path: Path = REGISTRY_PATH) -> dict:
    """Read the committed registry — request-time, honest on failure.

    Returns ``{ok, error, as_of, projects, sites}``; a missing/corrupt file
    yields ``ok=False`` with the reason and empty rows (the page banners it).
    """
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return {
            "ok": False,
            "error": f"registry unreadable ({type(exc).__name__}: {exc})",
            "as_of": "",
            "projects": {},
            "sites": [],
        }
    sites = raw.get("sites") if isinstance(raw, dict) else None
    if not isinstance(sites, list):
        return {
            "ok": False,
            "error": "registry has no 'sites' list",
            "as_of": "",
            "projects": {},
            "sites": [],
        }
    return {
        "ok": True,
        "error": "",
        "as_of": str(raw.get("as_of") or ""),
        "projects": raw.get("projects") if isinstance(raw.get("projects"), dict) else {},
        "sites": [dict(r) for r in sites if isinstance(r, dict)],
    }


def _classify(res: dict) -> dict:
    """One probe result → an honest health cell. ``live`` ONLY on a real 2xx."""
    status = res.get("status", 0)
    if res.get("ok"):
        return {
            "state": "live",
            "label": "live",
            "detail": f"HTTP {status}",
            "as_of": res.get("fetched_at", ""),
            "cached": bool(res.get("cached")),
        }
    if status:
        return {
            "state": "degraded",
            "label": f"degraded (HTTP {status})",
            "detail": (res.get("error") or f"HTTP {status}").strip(),
            "as_of": res.get("fetched_at", ""),
            "cached": bool(res.get("cached")),
        }
    return {
        "state": "down",
        "label": "down",
        "detail": res.get("error") or "no HTTP response",
        "as_of": res.get("fetched_at", ""),
        "cached": bool(res.get("cached")),
    }


def _unprobed_health(row: dict) -> dict:
    """The honest no-probe states — never a green badge without a probe."""
    if row.get("status") == "pending-publish":
        return {
            "state": "pending",
            "label": "pending publish",
            "detail": "not published yet — nothing to probe",
            "as_of": "",
            "cached": False,
        }
    if not row.get("url"):
        return {
            "state": "no-url",
            "label": "no URL recorded",
            "detail": "nothing to probe — an honest absence, not a dead link",
            "as_of": "",
            "cached": False,
        }
    return {
        "state": "unprobed",
        "label": "not probed",
        "detail": "probe disabled for this row",
        "as_of": "",
        "cached": False,
    }


async def overview(refresh: bool = False) -> dict:
    """The /directory payload: registry rows + live health, grouped for render.

    Probes run concurrently over the shared TTL cache; ``refresh=True``
    (?refresh=1 upstream) bypasses it like every other page.
    """
    reg = load_registry()
    rows = reg["sites"]

    probed = [r for r in rows if r.get("url") and r.get("probe")]
    # follow_redirects=True: a release-download row (e.g. the Lumen Drift .gba)
    # 302-redirects to a CDN, so probing to the FINAL status is what tells the
    # truth — a bare 302 is a false "degraded", not a dead link. This is the
    # ONLY github._get caller that opts in; askverify's raw-302 login signal
    # keeps the default no-follow behavior.
    results = await asyncio.gather(
        *[
            github._get(r["url"], refresh=refresh, raw=True, follow_redirects=True)
            for r in probed
        ]
    )
    for r, res in zip(probed, results):
        r["health"] = _classify(res)
    for r in rows:
        if "health" not in r:
            r["health"] = _unprobed_health(r)
        if r.get("status") not in KNOWN_STATUSES:
            r["status_unknown"] = True

    our_sites = [r for r in rows if r.get("section") == "our-sites"]
    external = [r for r in rows if r.get("section") == "external"]
    unclassified = [r for r in rows if r.get("section") not in ("our-sites", "external")]

    # our-sites grouped by Railway project / estate, registry order preserved.
    groups: list[dict] = []
    by_project: dict[str, dict] = {}
    for r in our_sites:
        key = str(r.get("project") or "unassigned")
        if key not in by_project:
            by_project[key] = {
                "project": key,
                "note": str(reg["projects"].get(key) or ""),
                "rows": [],
            }
            groups.append(by_project[key])
        by_project[key]["rows"].append(r)

    counts = {"live": 0, "degraded": 0, "down": 0}
    for r in probed:
        state = r["health"]["state"]
        if state in counts:
            counts[state] += 1
    probe_as_of = max((r["health"]["as_of"] for r in probed), default="")

    return {
        "ok": reg["ok"],
        "error": reg["error"],
        "as_of": reg["as_of"],
        "our_sites": our_sites,
        "our_sites_groups": groups,
        "external": external,
        "unclassified": unclassified,
        "probed": probed,
        "counts": {**counts, "probed": len(probed), "total": len(rows)},
        "probe_as_of": probe_as_of,
    }
