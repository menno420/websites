"""Tests for the ambient-Railway-ID guard (scripts/check_no_ambient_railway_ids.py).

Verifies the guard passes on the real repo, flags every env-read shape of the
three ambient IDs, ignores the SAFE explicit websites IDs, and fails when the
doc warning is missing.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
_MOD_PATH = REPO_ROOT / "scripts" / "check_no_ambient_railway_ids.py"

_spec = importlib.util.spec_from_file_location("_ambient_guard", _MOD_PATH)
assert _spec and _spec.loader
guard = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(guard)


def test_guard_passes_on_clean_repo():
    """The real repo must be clean: no code reads an ambient ID."""
    assert guard.scan_code() == []


def test_doc_warning_present_on_real_repo():
    """A safety doc must carry the three-ID warning."""
    assert guard.check_doc_warning() == []


def test_main_returns_zero_on_clean_repo():
    assert guard.main() == 0


def test_env_read_patterns_flag_every_shape():
    """Each env-read shape of each ambient ID must match a pattern."""
    for ident in guard.AMBIENT_IDS:
        samples = [
            f'os.environ["{ident}"]',
            f"os.environ.get('{ident}')",
            f'os.getenv("{ident}")',
            f"${{{ident}}}",
            f"${ident}",
        ]
        for sample in samples:
            assert any(
                p.search(sample) for p in guard.ENV_READ_PATTERNS
            ), f"expected a pattern to flag: {sample!r}"


def test_safe_explicit_websites_ids_are_not_flagged():
    """The hardcoded superbot-websites literals must NOT trip the guard."""
    safe_lines = [
        'PROJECT_ID = "70198ece-cbc0-484e-86d9-f8a1eca4f045"',
        'ENV_ID = "31485ecd-b3fe-4a8f-b136-337f6f099dc2"',
        'SERVICE_ID = "2c840017-a505-4144-b2ff-b2450430a7d9"',
    ]
    for line in safe_lines:
        assert not any(p.search(line) for p in guard.ENV_READ_PATTERNS)


def test_planted_violation_is_detected():
    """A planted env-read of an ambient ID must be reported by scan_code()."""
    plant = REPO_ROOT / "tools" / "_ambient_plant_tmp.py"
    plant.write_text('import os\nx = os.environ["RAILWAY_PROJECT_ID"]\n')
    try:
        violations = guard.scan_code(["tools/_ambient_plant_tmp.py"])
        assert any("_ambient_plant_tmp.py" in v for v in violations), violations
        assert any("RAILWAY_PROJECT_ID" in v for v in violations)
    finally:
        plant.unlink(missing_ok=True)
