"""Drift guard: the wake-ritual docs and scripts/open_work.py agree.

The open-work sweep (docs/ideas/open-pr-awareness-at-wake-2026-07-10.md,
doc-step slice 2026-07-13) lives in two docs — the routine-prompt WAKE
paste block and the project-instructions ROUTINE-FIRED state table — and
one script. These tests pin them together so renaming a classifier state
in the script breaks the build until the docs follow. Pure file reads:
the script is parsed as text, never executed; no subprocess, no network.
"""

import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT = _ROOT / "scripts" / "open_work.py"
_ROUTINE_PROMPT = _ROOT / "docs" / "project" / "routine-prompt.md"
_INSTRUCTIONS = _ROOT / "docs" / "project" / "project-instructions.md"

# The states the classifier is known to emit today — a floor, so the
# regex extraction below can never silently degrade to an empty set.
_KNOWN_STATES = {"PR-OPEN", "PR-LESS", "NO-DIFF", "MERGED-STALE", "PR-UNKNOWN"}


def _script_state_labels() -> set[str]:
    """State labels regexed out of the script SOURCE (literal quoted
    ALL-CAPS tokens like "PR-OPEN") — the source is the truth the docs
    must track."""
    src = _SCRIPT.read_text(encoding="utf-8")
    labels = set(re.findall(r'"([A-Z][A-Z-]{2,})"', src))
    assert _KNOWN_STATES <= labels, (
        f"state extraction lost known labels — got {sorted(labels)}; "
        "did scripts/open_work.py stop using quoted ALL-CAPS state strings?"
    )
    return labels


def test_open_work_script_exists():
    assert _SCRIPT.is_file(), "scripts/open_work.py is gone — the wake-ritual docs point at it"


def test_routine_prompt_mentions_the_sweep():
    assert "open_work.py" in _ROUTINE_PROMPT.read_text(encoding="utf-8"), (
        "docs/project/routine-prompt.md lost its open-work sweep step"
    )


def test_project_instructions_mention_the_sweep():
    assert "open_work.py" in _INSTRUCTIONS.read_text(encoding="utf-8"), (
        "docs/project/project-instructions.md lost its open-work sweep line"
    )


def test_every_script_state_appears_in_the_instructions_table():
    """A state renamed or added in scripts/open_work.py must show up in the
    ROUTINE-FIRED state table, or this reddens the PR."""
    text = _INSTRUCTIONS.read_text(encoding="utf-8")
    missing = sorted(label for label in _script_state_labels() if label not in text)
    assert not missing, (
        f"scripts/open_work.py states missing from the project-instructions "
        f"state table: {missing}"
    )
