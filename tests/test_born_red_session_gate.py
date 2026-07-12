"""Regression guard for the born-red session gate (repro of PR #19).

PR #19 auto-merged an effectively-empty PR because the vendored (pre-1.0.0)
substrate engine had two holes that let a *born-red* session card (Status
``in-progress``) sail through ``check --strict --require-session-log``:

  * Hole #1 — the checker only verified the required MARKERS were present; it
    never inspected the Status VALUE, so an ``in-progress`` card passed strict.
  * Hole #2 — the "current" card was picked newest-by-mtime, but a fresh CI
    checkout flattens every mtime to checkout time, so an OLD ``complete`` card
    could be selected over THIS PR's ``in-progress`` one and mask it.

Both are fixed at kit v1.0.0 (re-vendored ``bootstrap.py``): ``status_in_progress``
holds the gate on the Status value (not allowlistable), and ``check
--session-log <file>`` selects the card explicitly (the diff-aware selection the
``quality`` workflow derives from the PR diff) instead of guessing by mtime.

These tests drive the REAL CLI the CI gate runs, so a regression re-opening
either hole reddens the suite.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BOOTSTRAP = REPO_ROOT / "bootstrap.py"
CONFIG = REPO_ROOT / "substrate.config.json"

_COMPLETE_CARD = """# {title}

> **Status:** `complete`

- **📊 Model:** test-model · low · fixture

Real close-out prose. 💡 Session idea: something worth keeping.

## Previous-session review
The prior session did fine.
"""

_IN_PROGRESS_CARD = """# {title}

> **Status:** `in-progress`

About to start work. 💡 Session idea: the born-red gate fix.

## Previous-session review
The prior session did fine.
"""


def _make_install(tmp_path: Path) -> Path:
    """Build a minimal substrate install with a stale-complete + a born-red card.

    The complete card is written first and its mtime is bumped to be the NEWEST
    afterwards, reproducing the CI-checkout flattening in which the stale card
    would win a newest-by-mtime guess (Hole #2).
    """
    target = tmp_path / "install"
    (target / ".sessions").mkdir(parents=True)
    (target / ".substrate").mkdir()
    (target / "docs").mkdir()
    (target / "substrate.config.json").write_text(CONFIG.read_text())
    # The engine's enforcement-wiring guard requires a workflow that runs
    # `check --strict`; give the install the real quality.yml so the fixture
    # exercises the actual wired gate, not a stub.
    (target / ".github" / "workflows").mkdir(parents=True)
    (target / ".github" / "workflows" / "quality.yml").write_text(
        (REPO_ROOT / ".github" / "workflows" / "quality.yml").read_text(),
    )

    old = target / ".sessions" / "2026-07-01-old-done.md"
    born_red = target / ".sessions" / "2026-07-09-born-red.md"
    born_red.write_text(_IN_PROGRESS_CARD.format(title="2026-07-09 born-red"))
    time.sleep(0.02)
    old.write_text(_COMPLETE_CARD.format(title="2026-07-01 old-done"))
    # Make the STALE complete card the newest by mtime — the worst case.
    now = time.time()
    import os

    os.utime(born_red, (now - 100, now - 100))
    os.utime(old, (now, now))
    return target


def _check(target: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(BOOTSTRAP), "check", "--target", str(target),
         "--strict", "--require-session-log", *extra],
        capture_output=True,
        text=True,
    )


def test_direction_a_in_progress_card_fails(tmp_path):
    """Direction A: diff-aware selection of the born-red card must FAIL (exit 1)."""
    target = _make_install(tmp_path)
    res = _check(target, "--session-log", ".sessions/2026-07-09-born-red.md")
    assert res.returncode == 1, res.stdout + res.stderr
    assert "in-progress" in res.stdout.lower()


def test_direction_b_complete_card_passes(tmp_path):
    """Direction B: the same card flipped to complete must PASS (exit 0)."""
    target = _make_install(tmp_path)
    card = target / ".sessions" / "2026-07-09-born-red.md"
    card.write_text(_COMPLETE_CARD.format(title="2026-07-09 born-red"))
    res = _check(target, "--session-log", ".sessions/2026-07-09-born-red.md")
    assert res.returncode == 0, res.stdout + res.stderr
    assert "complete" in res.stdout.lower()


def test_diff_aware_selection_beats_mtime(tmp_path):
    """Hole #2: --session-log targets the named card regardless of mtime.

    The stale complete card is the newest by mtime, so a bare (mtime-fallback)
    check would wrongly pass — but the diff-aware --session-log names the
    born-red card the PR added, and that must fail.
    """
    target = _make_install(tmp_path)
    diff_aware = _check(target, "--session-log", ".sessions/2026-07-09-born-red.md")
    assert diff_aware.returncode == 1, diff_aware.stdout + diff_aware.stderr
    assert "2026-07-09-born-red.md" in diff_aware.stdout


def test_config_names_kit_v1(tmp_path):
    """The vendored engine's version pin: config records the adopted release.

    Bumped 1.0.0 -> 1.2.0 by the D-0019 §4.3 upgrade (PR #31), then
    1.2.0 -> 1.6.0 by the D-0026 §4.3 upgrade, then 1.6.0 -> 1.7.0 and
    1.7.0 -> 1.7.1 by the 2026-07-10 distribution-wave §4.3 upgrades, then
    1.7.1 -> 1.8.0 by the 2026-07-11 v1.8.0 distribution upgrade, then
    1.8.0 -> 1.9.0 by the 2026-07-11 v1.9.0 distribution upgrade, then
    1.9.0 -> 1.10.0 by the 2026-07-11 v1.10.0 distribution upgrade, then
    1.10.0 -> 1.10.1 by the 2026-07-11 v1.10.1 distribution upgrade, then
    1.10.1 -> 1.11.0 by the 2026-07-11 v1.11.0 distribution upgrade, then
    1.11.0 -> 1.12.0 by the 2026-07-11 v1.12.0 distribution upgrade, then
    1.12.0 -> 1.12.1 by the 2026-07-11 v1.12.1 distribution upgrade, then
    1.12.1 -> 1.13.0 by the 2026-07-12 v1.13.0 distribution upgrade. Keep this
    an EXACT pin on purpose: an upgrade must consciously move it, and a silent
    re-vendor without recording `kit_version` reddens here.
    """
    cfg = json.loads(CONFIG.read_text())
    assert cfg.get("kit_version") == "1.13.0"
    assert "status_in_progress" in BOOTSTRAP.read_text()
