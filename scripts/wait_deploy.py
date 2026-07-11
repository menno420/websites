#!/usr/bin/env python3
"""Post-merge deploy-convergence poller: wait until the live services run a
given commit.

──────────────────────────────────────────────────────────────────────────────
PROVENANCE / KILL-SWITCH HEADER
  Why:   "Merge = deploy" — every merge to main should surface on all three
         Railway services' `/version` within minutes. Sessions verify this by
         hand-curling `/version` after every merge (twelve times in one
         continuous-mode night); this script turns that loop into one
         deterministic PASS/FAIL: poll until every service reports the
         expected sha, or time out with the honest per-service state.
  Added: 2026-07-11 (continuous-mode wake, backlog promotion; captured in
         .sessions/2026-07-10-gen2-walking-skeleton.md 💡).
  Trust: DETERMINISTIC (pure stdlib urllib + time); reuses the healthcheck
         service table shape. Never guesses — an unreachable /version counts
         as not-converged with its error shown.
  KILL-SWITCH: convenience helper, not infrastructure — DELETE this file if
         the deploy pipeline changes; nothing depends on it.
──────────────────────────────────────────────────────────────────────────────

Usage:  python3 scripts/wait_deploy.py <sha> [timeout_seconds]
        <sha> may be full or short (prefix match, min 7 chars).
        Default timeout 300s, poll every 10s.
Exit 0 = every service's /version sha matches <sha> before the timeout.
Exit 1 = timeout (per-service last-seen state printed) or bad usage.
"""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request

SERVICES = [
    ("control-plane", "https://control-plane-production-abb0.up.railway.app"),
    ("botsite", "https://botsite-production-cfd7.up.railway.app"),
    ("dashboard", "https://dashboard-production-a91b.up.railway.app"),
]
POLL_SECONDS = 10
DEFAULT_TIMEOUT = 300
MIN_SHA = 7


def fetch_sha(base_url: str) -> tuple[str, str]:
    """One service's deployed sha: ``(sha, "")`` or ``("", error)``."""
    try:
        with urllib.request.urlopen(f"{base_url}/version", timeout=15) as resp:
            data = json.load(resp)
        return str(data.get("sha") or ""), ""
    except Exception as exc:  # honest: the error IS the state
        return "", f"{type(exc).__name__}: {exc}"


def converged(deployed_sha: str, want: str) -> bool:
    """Prefix-tolerant sha match (full-or-short, never empty-matches)."""
    if not deployed_sha or not want or len(want) < MIN_SHA:
        return False
    return deployed_sha.startswith(want) or want.startswith(deployed_sha)


def main(argv: list[str]) -> int:
    if len(argv) < 2 or len(argv[1]) < MIN_SHA:
        print(f"usage: wait_deploy.py <sha (>= {MIN_SHA} chars)> [timeout_s]")
        return 1
    want = argv[1]
    timeout = int(argv[2]) if len(argv) > 2 else DEFAULT_TIMEOUT
    deadline = time.monotonic() + timeout

    last: dict[str, str] = {}
    while True:
        pending = []
        for name, base in SERVICES:
            sha, err = fetch_sha(base)
            last[name] = sha[:9] if sha else f"({err[:60]})"
            if not converged(sha, want):
                pending.append(name)
        if not pending:
            print(f"CONVERGED: all {len(SERVICES)} services at {want[:9]}")
            return 0
        if time.monotonic() >= deadline:
            print(f"TIMEOUT after {timeout}s waiting for {want[:9]}:")
            for name, _ in SERVICES:
                mark = "ok " if name not in pending else "…  "
                print(f"  {mark} {name:<14} last seen: {last[name]}")
            return 1
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
