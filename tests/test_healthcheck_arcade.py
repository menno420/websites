"""Tests for the arcade URL drift pass (live+download) in scripts/healthcheck.py.

Offline: `botsite.arcade_probe.probe_registry_urls` (and, for the exit-code
test, the service `_probe` + registry check too) is monkeypatched so nothing
here ever touches the network; the probe's own fetch logic is unit-tested
against httpx.MockTransport in botsite/tests/test_arcade_probe.py. Same
module-load idiom as tests/test_healthcheck_registry.py.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
_MOD_PATH = REPO_ROOT / "scripts" / "healthcheck.py"

_spec = importlib.util.spec_from_file_location("_healthcheck_arcade", _MOD_PATH)
assert _spec and _spec.loader
healthcheck = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(healthcheck)


def _summary(rows=(), flagged=(), skipped=(), ok=True, note="x"):
    return {
        "rows": list(rows), "flagged": list(flagged),
        "skipped": list(skipped), "ok": ok, "note": note,
    }


def test_all_probed_urls_ok_passes(monkeypatch):
    rows = [{"slug": "mineverse", "availability": "live",
             "url": "https://example.com", "ok": True, "note": "200"}]
    monkeypatch.setattr(
        healthcheck.arcade_probe, "probe_registry_urls",
        lambda: _summary(rows=rows, note="1 URL(s) probed (live+download), 0 flagged"),
    )
    ok, lines = healthcheck.check_arcade_urls()
    assert ok is True
    assert any("mineverse" in ln and "PASS" in ln for ln in lines)


def test_dead_probed_url_is_flagged_and_fails_the_pass(monkeypatch):
    rows = [{"slug": "mineverse", "availability": "live",
             "url": "https://example.com", "ok": False, "note": "HTTP 404"}]
    monkeypatch.setattr(
        healthcheck.arcade_probe, "probe_registry_urls",
        lambda: _summary(rows=rows, flagged=rows, ok=False,
                         note="1 URL(s) probed (live+download), 1 flagged"),
    )
    ok, lines = healthcheck.check_arcade_urls()
    assert ok is False
    assert any("FLAGGED" in ln and "HTTP 404" in ln for ln in lines)


def test_per_row_output_shows_availability(monkeypatch):
    rows = [{"slug": "lumen-drift", "availability": "download",
             "url": "https://example.com/rom.zip", "ok": True, "note": "200"}]
    monkeypatch.setattr(
        healthcheck.arcade_probe, "probe_registry_urls",
        lambda: _summary(rows=rows, note="1 URL(s) probed (live+download), 0 flagged"),
    )
    ok, lines = healthcheck.check_arcade_urls()
    assert ok is True
    assert any("lumen-drift" in ln and "[download]" in ln for ln in lines)


def test_other_availability_entries_get_explicit_not_probed_lines(monkeypatch):
    skipped = [{"slug": "lumen-drift", "availability": "unavailable"}]
    monkeypatch.setattr(
        healthcheck.arcade_probe, "probe_registry_urls",
        lambda: _summary(skipped=skipped, note="0 URL(s) probed (live+download), 0 flagged"),
    )
    ok, lines = healthcheck.check_arcade_urls()
    assert ok is True
    assert any("lumen-drift" in ln and "not probed" in ln and "unavailable" in ln for ln in lines)


def test_probe_bug_degrades_to_fail_line_not_traceback(monkeypatch):
    def _boom():
        raise RuntimeError("wat")

    monkeypatch.setattr(healthcheck.arcade_probe, "probe_registry_urls", _boom)
    ok, lines = healthcheck.check_arcade_urls()
    assert ok is False
    assert any("probe raised RuntimeError" in ln for ln in lines)


def test_flagged_arcade_url_turns_main_exit_nonzero(monkeypatch, capsys):
    """The pass folds into the script's existing idiom: any failure = exit 1.
    Services + registry + tester-task + release-drift passes are stubbed
    healthy so the arcade flag is the only red (and nothing touches the
    network)."""
    monkeypatch.setattr(healthcheck, "_probe", lambda url: (200, ""))
    monkeypatch.setattr(healthcheck, "check_fleet_registry", lambda: (True, "2 lanes parsed"))
    monkeypatch.setattr(
        healthcheck.testing_probe, "probe_task_urls",
        lambda: _summary(note="0 open-task URL(s) probed, 0 flagged"),
    )
    monkeypatch.setattr(
        healthcheck, "check_release_drift",
        lambda: (True, ["0 blocker(s) across the 4 registries, 0 distinct ask(s) joined, 0 flagged"]),
    )
    monkeypatch.setattr(
        healthcheck, "check_catalog_sha_drift",
        lambda: (True, ["0 pinned entries checked, 0 flagged, 0 not pinned-provenance-shaped (not probed)"]),
    )
    rows = [{"slug": "mineverse", "availability": "live",
             "url": "https://example.com", "ok": False, "note": "HTTP 503"}]
    monkeypatch.setattr(
        healthcheck.arcade_probe, "probe_registry_urls",
        lambda: _summary(rows=rows, flagged=rows, ok=False,
                         note="1 URL(s) probed (live+download), 1 flagged"),
    )
    assert healthcheck.main() == 1
    out = capsys.readouterr().out
    assert "arcade URL drift probe (live+download): FAIL" in out
    assert "FLAGGED" in out and "HTTP 503" in out
    assert "RESULT: ONE OR MORE DOWN" in out


def test_healthy_arcade_keeps_main_exit_zero(monkeypatch, capsys):
    monkeypatch.setattr(healthcheck, "_probe", lambda url: (200, ""))
    monkeypatch.setattr(healthcheck, "check_fleet_registry", lambda: (True, "2 lanes parsed"))
    monkeypatch.setattr(
        healthcheck.testing_probe, "probe_task_urls",
        lambda: _summary(note="0 open-task URL(s) probed, 0 flagged"),
    )
    monkeypatch.setattr(
        healthcheck, "check_release_drift",
        lambda: (True, ["0 blocker(s) across the 4 registries, 0 distinct ask(s) joined, 0 flagged"]),
    )
    monkeypatch.setattr(
        healthcheck, "check_catalog_sha_drift",
        lambda: (True, ["0 pinned entries checked, 0 flagged, 0 not pinned-provenance-shaped (not probed)"]),
    )
    rows = [{"slug": "mineverse", "availability": "live",
             "url": "https://example.com", "ok": True, "note": "200"}]
    monkeypatch.setattr(
        healthcheck.arcade_probe, "probe_registry_urls",
        lambda: _summary(rows=rows, note="1 URL(s) probed (live+download), 0 flagged"),
    )
    assert healthcheck.main() == 0
    out = capsys.readouterr().out
    assert "arcade URL drift probe (live+download): PASS" in out
    assert "RESULT: all healthy" in out
