"""Tests for the `/fleet` registry live-parse smoke check in
scripts/healthcheck.py (retro A3; repointed 2026-07-11 to the fleet-manager
registry after the superbot manifest was superseded).

Offline: the live `_probe`/urllib fetch is monkeypatched so these never hit the
network; they exercise `check_fleet_registry()`'s parse-and-assert logic
against the SAME `app.fleet` parser `/fleet` renders with.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
_MOD_PATH = REPO_ROOT / "scripts" / "healthcheck.py"

_spec = importlib.util.spec_from_file_location("_healthcheck", _MOD_PATH)
assert _spec and _spec.loader
healthcheck = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(healthcheck)

_GOOD_REGISTRY = """
LANES = [
    {"lane": "retro (no repo)", "repo": None, "disposition": "registry-only",
     "tokens": ["retro"]},
    {"lane": "websites", "repo": "websites", "disposition": "live",
     "tokens": ["websites"]},
]
"""


class _FakeResponse:
    def __init__(self, body: bytes):
        self._body = body

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_check_fleet_registry_passes_on_well_formed_registry(monkeypatch):
    monkeypatch.setattr(
        healthcheck.urllib.request,
        "urlopen",
        lambda req, timeout=None: _FakeResponse(_GOOD_REGISTRY.encode("utf-8")),
    )
    ok, note = healthcheck.check_fleet_registry()
    assert ok is True
    assert "1 lanes parsed" in note


def test_check_fleet_registry_fails_on_zero_lanes(monkeypatch):
    """A registry reformat/move that yields no lanes must FAIL loud, not
    degrade silently — this exact alert caught the 2026-07-11 manifest
    supersession on schedule run 2."""
    monkeypatch.setattr(
        healthcheck.urllib.request,
        "urlopen",
        lambda req, timeout=None: _FakeResponse(b"no registry literal here"),
    )
    ok, note = healthcheck.check_fleet_registry()
    assert ok is False
    assert "ZERO lanes" in note


def test_check_fleet_registry_fails_on_fetch_error(monkeypatch):
    def _raise(req, timeout=None):
        raise OSError("boom")

    monkeypatch.setattr(healthcheck.urllib.request, "urlopen", _raise)
    ok, note = healthcheck.check_fleet_registry()
    assert ok is False
    assert "fetch failed" in note
