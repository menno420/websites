#!/usr/bin/env python3
"""Review-row auto-check: does this diff owe a fleet review-queue row?

──────────────────────────────────────────────────────────────────────────────
PROVENANCE / KILL-SWITCH HEADER
  Why:   The fleet review-queue (`fleet-manager docs/review-queue.md`) carries
         a BINDING rule: every merged PR with >50 changed lines of
         runtime/product code (excluding docs/, control/, .sessions/, and
         pure test additions) MUST get a row, appended by its own session
         before close. Enforcement was memory — 116 merged PRs / zero rows
         was the documented failure state, and this repo shipped #67/#72/
         #75/#77 over the bar unflagged. This script makes "a row is owed"
         mechanical; appending the row stays a fleet-manager write (which
         websites sessions cannot do — flag it to the manager).
  Added: 2026-07-11 (continuous-mode wake; captured in
         .sessions/2026-07-10-order-009-reviews.md 💡).
  Trust: DETERMINISTIC over `git diff --numstat`. The classifier is pure and
         unit-tested; binary files (numstat `-`) count 0 (honest: unknown
         line count, never guessed).
  KILL-SWITCH: convenience helper — DELETE if the fleet rule changes;
         nothing depends on it.
──────────────────────────────────────────────────────────────────────────────

Usage:  python3 scripts/review_row_check.py [range]
        range defaults to origin/main...HEAD (the working branch's diff);
        pass e.g. 'abc123^!' to check one merged commit.
Exit 0 always (informational): prints RUNTIME LINES + ROW OWED / no row owed.
"""

from __future__ import annotations

import subprocess
import sys

THRESHOLD = 50

# The ledger's exclusions: docs/, control/, .sessions/, and pure test
# additions. Test paths in this repo: tests/, botsite/tests/,
# dashboard/tests/. Markdown anywhere is documentation.
_EXCLUDE_PREFIXES = ("docs/", "control/", ".sessions/", ".substrate/")
_TEST_MARKERS = ("/tests/", "tests/")


def is_runtime_path(path: str) -> bool:
    """True when a changed path counts toward the ledger's 50-line rule."""
    if path.startswith(_EXCLUDE_PREFIXES):
        return False
    if path.endswith(".md"):
        return False
    if path.startswith("tests/") or "/tests/" in path:
        return False
    return True


def runtime_lines(numstat: str) -> tuple[int, list[tuple[int, str]]]:
    """Sum changed runtime lines from ``git diff --numstat`` output.

    Returns ``(total, [(lines, path), …])`` for the counted files. Binary
    files report ``-`` in numstat and count 0 (unknown, never guessed).
    """
    total = 0
    counted: list[tuple[int, str]] = []
    for line in (numstat or "").splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        added, deleted, path = parts
        if not is_runtime_path(path):
            continue
        n = 0
        if added.isdigit():
            n += int(added)
        if deleted.isdigit():
            n += int(deleted)
        total += n
        counted.append((n, path))
    return total, counted


def main(argv: list[str]) -> int:
    rng = argv[1] if len(argv) > 1 else "origin/main...HEAD"
    res = subprocess.run(
        ["git", "diff", "--numstat", rng],
        capture_output=True, text=True, check=False,
    )
    if res.returncode != 0:
        print(f"error: git diff failed for {rng!r}: {res.stderr.strip()}")
        return 0  # informational tool — never a gate
    total, counted = runtime_lines(res.stdout)
    print(f"runtime/product changed lines in {rng}: {total}")
    for n, path in sorted(counted, reverse=True)[:10]:
        print(f"  {n:>6}  {path}")
    if total > THRESHOLD:
        print(f"\nROW OWED: > {THRESHOLD} runtime lines — the fleet "
              "review-queue's binding rule applies. Appending the row is a "
              "fleet-manager write; flag it to the manager in the heartbeat.")
    else:
        print(f"\nno row owed (threshold {THRESHOLD}).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
