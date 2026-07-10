#!/usr/bin/env python3
"""Post-deploy healthcheck: GET /healthz and / on the three live services, plus
the `/fleet` manifest live-parse smoke check.

──────────────────────────────────────────────────────────────────────────────
PROVENANCE / KILL-SWITCH HEADER
  Why:   "Merge = deploy" — each service auto-redeploys on merge to main. This
         is the reusable post-deploy verification habit: one command confirms
         all three Railway services answer `/healthz` and serve their public
         `/` with HTTP 200. Beats hand-curling three URLs after every merge.
  Added: 2026-07-09 (websites hardening pass, PR #19, [D-0015]).
  Trust: DETERMINISTIC (pure stdlib urllib) — but UNVERIFIED as a habit; sanity
         check its verdict against a manual curl a few times before trusting.
  KILL-SWITCH: if the URLs change or this proves flaky/noisy over several
         sessions, update the SERVICES table or DELETE this file. It is a
         convenience helper, not infrastructure.
──────────────────────────────────────────────────────────────────────────────

All three services are PUBLIC (2026-07-09 auth-drop), so `/` is expected 200.

The manifest check (retro A3 / queue-state NEXT item 2) fetches the manager's
LIVE `fleet-manifest.md` (menno420/superbot) and asserts the SAME parser
`/fleet` uses (`app.fleet.parse_manifest` + `manifest_to_lanes`) still yields a
non-empty, well-formed lane set. `/fleet` itself degrades a bad parse to the
`config.FLEET_LANES` fallback with an honest on-page banner — safe, but silent
to anyone not looking at the page. This check is what alerts a manifest
reformat instead of letting it degrade unnoticed.

Usage:  python3 scripts/healthcheck.py
Exit 0 = every checked endpoint returned its expected status AND the manifest
parsed to a non-empty lane set; exit 1 = any of those fail.
"""

from __future__ import annotations

import os
import sys
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import config, fleet  # noqa: E402  (path setup must run first)

# (label, base URL). Endpoints checked per service: /healthz and / (both expect
# 200 now that all three are public).
SERVICES = [
    ("control-plane", "https://control-plane-production-abb0.up.railway.app"),
    ("botsite", "https://botsite-production-cfd7.up.railway.app"),
    ("dashboard", "https://dashboard-production-a91b.up.railway.app"),
]
ENDPOINTS = ("/healthz", "/")
EXPECTED = 200
TIMEOUT = 15

MANIFEST_URL = (
    f"{config.GITHUB_RAW_BASE}/{config.OWNER}/{fleet.MANIFEST_REPO}/main/"
    f"{fleet.MANIFEST_PATH}"
)


def _probe(url: str) -> tuple[int, str]:
    """Return (status_code, note). Network/HTTP errors degrade to (0, reason)."""
    req = urllib.request.Request(url, method="GET", headers={"User-Agent": "healthcheck"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return resp.status, ""
    except urllib.error.HTTPError as exc:  # a real HTTP status (e.g. 404/500)
        return exc.code, exc.reason or ""
    except (urllib.error.URLError, OSError, ValueError) as exc:
        return 0, str(getattr(exc, "reason", exc))


def check_fleet_manifest() -> tuple[bool, str]:
    """Fetch the live fleet-manifest and assert it parses to a non-empty,
    well-formed lane set — see the module docstring for why this exists."""
    req = urllib.request.Request(MANIFEST_URL, headers={"User-Agent": "healthcheck"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            text = resp.read().decode("utf-8")
    except (urllib.error.URLError, OSError, ValueError) as exc:
        return False, f"fetch failed: {getattr(exc, 'reason', exc)}"

    try:
        lanes = fleet.manifest_to_lanes(fleet.parse_manifest(text))
    except Exception as exc:  # defensive: a parser bug shouldn't crash the check
        return False, f"parse raised {type(exc).__name__}: {exc}"

    if not lanes:
        return False, "parsed to ZERO lanes — manifest reformat suspected"

    unresolved = [lane["lane"] for lane in lanes if not lane.get("repo") or not lane.get("status_path")]
    if unresolved:
        return False, f"lanes with unresolved repo/status_path: {unresolved}"

    return True, f"{len(lanes)} lanes parsed"


def main() -> int:
    rows: list[tuple[str, str, int, bool, str]] = []
    ok_all = True
    for label, base in SERVICES:
        for ep in ENDPOINTS:
            status, note = _probe(base + ep)
            ok = status == EXPECTED
            ok_all = ok_all and ok
            rows.append((label, ep, status, ok, note))

    width = max(len(lbl) for lbl, _ in SERVICES)
    print(f"{'service'.ljust(width)}  {'endpoint':9}  status  ok")
    print(f"{'-' * width}  {'-' * 9}  ------  --")
    for label, ep, status, ok, note in rows:
        mark = "PASS" if ok else "FAIL"
        shown = str(status) if status else "DOWN"
        extra = f"  ({note})" if note and not ok else ""
        print(f"{label.ljust(width)}  {ep:9}  {shown:>6}  {mark}{extra}")

    manifest_ok, manifest_note = check_fleet_manifest()
    ok_all = ok_all and manifest_ok
    print()
    print(f"fleet-manifest live parse: {'PASS' if manifest_ok else 'FAIL'} ({manifest_note})")

    print()
    print("RESULT:", "all healthy" if ok_all else "ONE OR MORE DOWN")
    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
