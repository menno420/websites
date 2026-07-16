"""Tests for the tester-task URL liveness pass (open tasks) in
scripts/healthcheck.py.

Offline: `botsite.testing_probe.probe_task_urls` (and, for the exit-code
tests, the service `_probe` + registry check + arcade probe too) is
monkeypatched so nothing here ever touches the network; the probe's own
fetch logic is unit-tested against httpx.MockTransport in
botsite/tests/test_testing_probe.py. Same module-load idiom as
tests/test_healthcheck_arcade.py.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
_MOD_PATH = REPO_ROOT / "scripts" / "healthcheck.py"

_spec = importlib.util.spec_from_file_location("_healthcheck_testing", _MOD_PATH)
assert _spec and _spec.loader
healthcheck = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(healthcheck)


def _summary(rows=(), flagged=(), skipped=(), ok=True, note="x"):
    return {
        "rows": list(rows), "flagged": list(flagged),
        "skipped": list(skipped), "ok": ok, "note": note,
    }


def _stub_everything_else_healthy(monkeypatch):
    """Exit-code tests: services + registry + arcade + release-drift stubbed
    healthy so the tester-task pass is the only variable — and nothing
    touches the network."""
    monkeypatch.setattr(healthcheck, "_probe", lambda url: (200, ""))
    monkeypatch.setattr(healthcheck, "check_fleet_registry", lambda: (True, "2 lanes parsed"))
    monkeypatch.setattr(
        healthcheck.arcade_probe, "probe_registry_urls",
        lambda: _summary(note="1 URL(s) probed (live+download), 0 flagged"),
    )
    monkeypatch.setattr(
        healthcheck, "check_release_drift",
        lambda: (True, ["0 blocker(s) across the 4 registries, 0 distinct ask(s) joined, 0 flagged"]),
    )


def test_all_probed_task_urls_ok_passes(monkeypatch):
    rows = [{"id": "site-review-botsite", "status": "open",
             "url": "https://example.com", "ok": True, "note": "200"}]
    monkeypatch.setattr(
        healthcheck.testing_probe, "probe_task_urls",
        lambda: _summary(rows=rows, note="1 open-task URL(s) probed, 0 flagged"),
    )
    ok, lines = healthcheck.check_testing_urls()
    assert ok is True
    assert any("site-review-botsite" in ln and "PASS" in ln for ln in lines)


def test_dead_task_url_is_flagged_and_fails_the_pass(monkeypatch):
    rows = [{"id": "site-review-botsite", "status": "open",
             "url": "https://example.com", "ok": False, "note": "HTTP 404"}]
    monkeypatch.setattr(
        healthcheck.testing_probe, "probe_task_urls",
        lambda: _summary(rows=rows, flagged=rows, ok=False,
                         note="1 open-task URL(s) probed, 1 flagged"),
    )
    ok, lines = healthcheck.check_testing_urls()
    assert ok is False
    assert any("FLAGGED" in ln and "HTTP 404" in ln for ln in lines)


def test_per_row_output_shows_status(monkeypatch):
    rows = [{"id": "walkthrough-botsite-first-visit", "status": "open",
             "url": "https://example.com", "ok": True, "note": "200"}]
    monkeypatch.setattr(
        healthcheck.testing_probe, "probe_task_urls",
        lambda: _summary(rows=rows, note="1 open-task URL(s) probed, 0 flagged"),
    )
    ok, lines = healthcheck.check_testing_urls()
    assert ok is True
    assert any("walkthrough-botsite-first-visit" in ln and "[open]" in ln for ln in lines)


def test_non_open_tasks_get_explicit_not_probed_lines(monkeypatch):
    skipped = [{"id": "game-test-lumen-drift", "status": "coming-soon"}]
    monkeypatch.setattr(
        healthcheck.testing_probe, "probe_task_urls",
        lambda: _summary(skipped=skipped, note="0 open-task URL(s) probed, 0 flagged"),
    )
    ok, lines = healthcheck.check_testing_urls()
    assert ok is True
    assert any(
        "game-test-lumen-drift" in ln and "not probed" in ln and "coming-soon" in ln
        for ln in lines
    )


def test_probe_bug_degrades_to_fail_line_not_traceback(monkeypatch):
    def _boom():
        raise RuntimeError("wat")

    monkeypatch.setattr(healthcheck.testing_probe, "probe_task_urls", _boom)
    ok, lines = healthcheck.check_testing_urls()
    assert ok is False
    assert any("probe raised RuntimeError" in ln for ln in lines)


def test_flagged_task_url_turns_main_exit_nonzero(monkeypatch, capsys):
    """The pass folds into the script's existing idiom: any failure = exit 1.
    Everything else is stubbed healthy so the tester-task flag is the only red."""
    _stub_everything_else_healthy(monkeypatch)
    rows = [{"id": "site-review-dashboard", "status": "open",
             "url": "https://example.com", "ok": False, "note": "HTTP 502"}]
    monkeypatch.setattr(
        healthcheck.testing_probe, "probe_task_urls",
        lambda: _summary(rows=rows, flagged=rows, ok=False,
                         note="1 open-task URL(s) probed, 1 flagged"),
    )
    assert healthcheck.main() == 1
    out = capsys.readouterr().out
    assert "tester-task URL liveness guard (open tasks): FAIL" in out
    assert "FLAGGED" in out and "HTTP 502" in out
    assert "RESULT: ONE OR MORE DOWN" in out


def test_healthy_tasks_keep_main_exit_zero(monkeypatch, capsys):
    _stub_everything_else_healthy(monkeypatch)
    rows = [{"id": "site-review-dashboard", "status": "open",
             "url": "https://example.com", "ok": True, "note": "200"}]
    monkeypatch.setattr(
        healthcheck.testing_probe, "probe_task_urls",
        lambda: _summary(rows=rows, note="1 open-task URL(s) probed, 0 flagged"),
    )
    assert healthcheck.main() == 0
    out = capsys.readouterr().out
    assert "tester-task URL liveness guard (open tasks): PASS" in out
    assert "RESULT: all healthy" in out
