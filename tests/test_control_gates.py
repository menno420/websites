"""Regression pins for the quality.yml control gates (PR #125 port).

The control fast lane runs ``bootstrap.py check --strict --status-only``
(a control-only PR must still prove its heartbeat) and both lanes run the
inbox append-only + ORDER-grammar gate (``--inbox-base <merge-base blob>``).
Those behaviors were validated BY HAND at port time; these tests drive the
REAL CLI the workflow runs (the ``test_born_red_session_gate.py`` pattern)
so an engine regression reds the suite instead of surfacing on a live
control PR — possibly a manager's inbox append.

Pinned lanes (all asserted via ``subprocess`` returncodes, never ``$?``
after a pipeline — the slice-25 validation gotcha):

  1. clean heartbeat  → ``--status-only`` exit 0
  2. broken heartbeat → exit 1 with ``[status-no-heartbeat]``
  3. inbox rewrite (an ORDER erased vs the base) → exit 1 with
     ``[inbox-not-append]``
  4. pure ORDER append → exit 0
  5. malformed append (non-ORDER text) → exit 1 with
     ``[inbox-order-grammar]``
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BOOTSTRAP = REPO_ROOT / "bootstrap.py"

_STATUS_OK = """# fixture · status
updated: 2026-07-11T12:00:00Z
phase: fixture heartbeat for the control-gate tests.
health: green (fixture)
orders: acked=001-002 done=001
"""

_STATUS_BROKEN = """# fixture · status
no heartbeat here
"""

_ORDER = """
## ORDER {nnn} · {ts} · status: new
priority: P3
executor: fixture seat
do: {do}
why: fixture.
done-when: n/a.
provenance: fixture.
"""

_INBOX_BASE = (
    "# fixture · inbox\n"
    + _ORDER.format(nnn="001", ts="2026-07-10T10:00:00Z", do="first fixture order.")
    + _ORDER.format(nnn="002", ts="2026-07-10T11:00:00Z", do="second fixture order.")
)


def _make_install(tmp_path: Path) -> Path:
    """Minimal substrate install: config + control files + the REAL
    quality.yml (the engine's enforcement-wiring guard wants a workflow
    that runs ``check --strict`` — same trick as the born-red gate tests)."""
    target = tmp_path / "install"
    (target / ".sessions").mkdir(parents=True)
    (target / ".substrate").mkdir()
    (target / "docs").mkdir()
    (target / "control").mkdir()
    (target / ".github" / "workflows").mkdir(parents=True)
    (target / "substrate.config.json").write_text(
        (REPO_ROOT / "substrate.config.json").read_text()
    )
    (target / ".github" / "workflows" / "quality.yml").write_text(
        (REPO_ROOT / ".github" / "workflows" / "quality.yml").read_text()
    )
    (target / "control" / "status.md").write_text(_STATUS_OK)
    (target / "control" / "inbox.md").write_text(_INBOX_BASE)
    return target


def _check(target: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(BOOTSTRAP), "check", "--target", str(target),
         "--strict", "--status-only", *extra],
        capture_output=True,
        text=True,
    )


def _write_base(tmp_path: Path) -> Path:
    base = tmp_path / "inbox.base.md"
    base.write_text(_INBOX_BASE)
    return base


def test_clean_heartbeat_passes_status_only(tmp_path):
    target = _make_install(tmp_path)
    res = _check(target)
    assert res.returncode == 0, res.stdout + res.stderr
    assert "control-status check passed" in res.stdout


def test_broken_heartbeat_reds_the_fast_lane(tmp_path):
    """A heartbeat-breaking control PR must NOT merge green (the pre-#125
    hole: the fast lane short-circuited with no validation at all)."""
    target = _make_install(tmp_path)
    (target / "control" / "status.md").write_text(_STATUS_BROKEN)
    res = _check(target)
    assert res.returncode == 1, res.stdout + res.stderr
    assert "[status-no-heartbeat]" in res.stdout


def test_inbox_rewrite_reds_append_only_gate(tmp_path):
    """Erasing an existing ORDER vs the merge-base is a protocol violation
    (one-writer / append-only law) — must red, never merge green."""
    target = _make_install(tmp_path)
    base = _write_base(tmp_path)
    # ORDER 002 deleted: keep only the header + ORDER 001 block.
    mutated = _INBOX_BASE.split("\n## ORDER 002")[0] + "\n"
    (target / "control" / "inbox.md").write_text(mutated)
    res = _check(target, "--inbox-base", str(base))
    assert res.returncode == 1, res.stdout + res.stderr
    assert "[inbox-not-append]" in res.stdout


def test_pure_order_append_passes(tmp_path):
    """The manager's normal write — a new ORDER appended at the end —
    must stay green (the gate must not block legitimate order traffic)."""
    target = _make_install(tmp_path)
    base = _write_base(tmp_path)
    appended = _INBOX_BASE + _ORDER.format(
        nnn="003", ts="2026-07-11T12:30:00Z", do="appended fixture order."
    )
    (target / "control" / "inbox.md").write_text(appended)
    res = _check(target, "--inbox-base", str(base))
    assert res.returncode == 0, res.stdout + res.stderr


def test_malformed_append_reds_order_grammar(tmp_path):
    """Appended content that is not a well-formed ORDER block reds on
    grammar — append-only alone is not enough to keep the inbox machine-
    readable."""
    target = _make_install(tmp_path)
    base = _write_base(tmp_path)
    (target / "control" / "inbox.md").write_text(
        _INBOX_BASE + "\nsome stray non-ORDER text appended\n"
    )
    res = _check(target, "--inbox-base", str(base))
    assert res.returncode == 1, res.stdout + res.stderr
    assert "[inbox-order-grammar]" in res.stdout
