"""Fast-lane grammar-pin map drift pin (backlog idea, 2026-07-13).

``.github/workflows/quality.yml``'s "control fast lane" step hard-codes a
shell mapping — a control-only diff touching a specific machine-read
control file still runs the ONE pytest pin file guarding that file's
grammar, even though the fast lane otherwise skips the full suite. Nothing
ever EXECUTES that mapping in the full lane: rename a pin test, or add a
fourth machine-read control file without a matching trigger, and the gate
goes hollow while staying green — the exact merge-lag class PR #314 closed
for the outbox pin itself (``test_outbox_grammar_pin.py``).

This test parses the shell block straight out of the workflow file (never
hand-copies the mapping) and asserts two things stay true: (1) every pin
test file the workflow references actually exists on disk, and (2) the set
of control-file triggers matches exactly the paths this repo's own code
machine-reads as control data (``app.briefing.OUTBOX_PATH``, the
``status_path`` convention pinned by ``test_own_heartbeat.py``, and the
``control/claims/`` prefix ``control/claims/README.md`` documents). A pin
test renamed on disk, or a trigger silently dropped/added without its
match on the other side, reddens THIS file instead of decaying invisibly.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from app.briefing import OUTBOX_PATH  # noqa: E402

WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "quality.yml"

# The exact machine-read control-file triggers this repo's own code cares
# about — kept as a literal set (not derived) so a change on EITHER side
# (a new machine-read control file, or a new/removed workflow trigger)
# shows up as a mismatch here rather than silently drifting apart.
EXPECTED_TRIGGERS = {
    OUTBOX_PATH: "tests/test_outbox_grammar_pin.py",
    "control/status.md": "tests/test_own_heartbeat.py",
    "control/claims/": "tests/test_claims_drift_gate.py",
}

# Matches one `if printf '%s\n' "$files" | grep {-Fxq|-q} '[^]<trigger>'; then`
# block followed by its `pin_tests=...tests/<name>.py"` assignment line.
# The exact-match trigger (`-Fxq`) has no `^` anchor; the prefix trigger
# (`-q '^control/claims/'`) does — stripped so both compare as plain paths.
_TRIGGER_RE = re.compile(
    r"grep\s+-\w+\s+'\^?([^']+)'\s*;\s*then\s*\n\s*pin_tests="
    r'"[^"]*?(tests/\S+?\.py)"',
)


def _parse_pin_map() -> dict[str, str]:
    text = WORKFLOW_PATH.read_text(encoding="utf-8")
    lane_start = text.index("id: lane")
    # Scope the parse to the control-fast-lane step only — the next step
    # boundary is the first "- name:" line after the lane step starts.
    rest = text[lane_start:]
    next_step = re.search(r"\n\s*- name:", rest[1:])
    block = rest[: next_step.start() + 1] if next_step else rest
    return {trigger: test for trigger, test in _TRIGGER_RE.findall(block)}


def test_workflow_file_exists():
    assert WORKFLOW_PATH.is_file(), f"expected {WORKFLOW_PATH} to exist"


def test_pin_map_matches_expected_triggers():
    parsed = _parse_pin_map()
    assert parsed, (
        "no grep-trigger -> pin_tests pairs found in quality.yml's control "
        "fast lane step — the shell was restructured; update this pin's "
        "regex (and re-verify the mapping by hand) alongside it"
    )
    assert parsed == EXPECTED_TRIGGERS, (
        f"quality.yml's fast-lane pin map drifted from what this repo's "
        f"code actually machine-reads as control data.\n"
        f"  workflow has:  {parsed}\n"
        f"  expected:      {EXPECTED_TRIGGERS}\n"
        f"Either a machine-read control file gained/lost its CI pin, or "
        f"this test's EXPECTED_TRIGGERS is stale — fix whichever is wrong."
    )


def test_every_pinned_test_file_exists_on_disk():
    parsed = _parse_pin_map()
    missing = [test for test in parsed.values() if not (REPO_ROOT / test).is_file()]
    assert not missing, (
        f"quality.yml's fast lane references pin test file(s) that don't "
        f"exist on disk (renamed or deleted without updating the "
        f"workflow): {missing}"
    )
