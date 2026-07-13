"""Module-level env-parse hardening for the control-plane (ORDER 026 finding).

On Railway an empty-string env entry is NOT "unset": before this hardening a
bare module-level ``int(os.environ.get(..., "180"))`` meant ``int("")`` —
crashing the whole service at import (docs/CAPABILITIES.md, 2026-07-13).
These tests pin the fix: empty, unset and malformed values ALL fall back to
the documented default, and the module survives import (reload) with a
hostile environment set.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import config  # noqa: E402

# (env var name, documented default) — the four module-level int parses.
INT_VARS = [
    ("CACHE_TTL_SECONDS", 180),
    ("AUTOREFRESH_SECONDS", 45),
    ("FLEET_STALE_HOURS", 12),
    ("CLAIM_STALE_HOURS", 24),
]


def test_env_int_empty_string_falls_back(monkeypatch):
    monkeypatch.setenv("X_TEST_INT", "")
    assert config._env_int("X_TEST_INT", 42) == 42


def test_env_int_unset_falls_back(monkeypatch):
    monkeypatch.delenv("X_TEST_INT", raising=False)
    assert config._env_int("X_TEST_INT", 42) == 42


def test_env_int_garbage_falls_back(monkeypatch):
    monkeypatch.setenv("X_TEST_INT", "abc")
    assert config._env_int("X_TEST_INT", 42) == 42


def test_env_int_valid_value_wins(monkeypatch):
    monkeypatch.setenv("X_TEST_INT", "7")
    assert config._env_int("X_TEST_INT", 42) == 7


def test_import_survives_hostile_env(monkeypatch):
    """The original crash class: reload app.config with every int var hostile."""
    for hostile in ("", "abc"):
        for name, _default in INT_VARS:
            monkeypatch.setenv(name, hostile)
        try:
            importlib.reload(config)
            for name, default in INT_VARS:
                assert getattr(config, name) == default, (name, hostile)
        finally:
            monkeypatch.undo()
            importlib.reload(config)  # restore module state for other tests
