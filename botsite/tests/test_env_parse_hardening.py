"""Module-level env-parse hardening for the botsite (ORDER 026 finding).

On Railway an empty-string env entry is NOT "unset": before this hardening
``int(os.environ.get("SITE_CACHE_TTL_SECONDS", "180"))`` meant ``int("")`` —
crashing the service at import (docs/CAPABILITIES.md, 2026-07-13). These
tests pin the fix: empty, unset and malformed values all fall back to the
documented default, and the module survives import with a hostile value set.
"""

from __future__ import annotations

import importlib

from botsite import data_source as ds


def test_env_int_empty_string_falls_back(monkeypatch):
    monkeypatch.setenv("X_TEST_INT", "")
    assert ds._env_int("X_TEST_INT", 42) == 42


def test_env_int_unset_falls_back(monkeypatch):
    monkeypatch.delenv("X_TEST_INT", raising=False)
    assert ds._env_int("X_TEST_INT", 42) == 42


def test_env_int_garbage_falls_back(monkeypatch):
    monkeypatch.setenv("X_TEST_INT", "abc")
    assert ds._env_int("X_TEST_INT", 42) == 42


def test_env_int_valid_value_wins(monkeypatch):
    monkeypatch.setenv("X_TEST_INT", "7")
    assert ds._env_int("X_TEST_INT", 42) == 7


def test_import_survives_hostile_env(monkeypatch):
    """The original crash class: reload with SITE_CACHE_TTL_SECONDS hostile."""
    for hostile in ("", "abc"):
        monkeypatch.setenv("SITE_CACHE_TTL_SECONDS", hostile)
        try:
            importlib.reload(ds)
            assert ds.CACHE_TTL_SECONDS == 180, hostile
        finally:
            monkeypatch.undo()
            importlib.reload(ds)  # restore module state for other tests
