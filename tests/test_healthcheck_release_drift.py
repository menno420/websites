"""Tests for the release-drift flag pass (registry blockers vs askverify)
in scripts/healthcheck.py.

Offline: the registry collection (`_collect_registry_blockers`) is
monkeypatched to synthetic blocker rows and the askverify REGISTRY entries'
probes are monkeypatched to canned coroutines (monkeypatch.setitem on the
entry dict — the SAME object `askverify.match` resolves by exact id), so
the pass runs its REAL join + annotate machinery with nothing ever touching
the network. For the exit-code tests the other four passes are stubbed
healthy too. Same module-load idiom as tests/test_healthcheck_arcade.py.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
_MOD_PATH = REPO_ROOT / "scripts" / "healthcheck.py"

_spec = importlib.util.spec_from_file_location("_healthcheck_release_drift", _MOD_PATH)
assert _spec and _spec.loader
healthcheck = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(healthcheck)

askverify = healthcheck.askverify


def _blocker(ask_id):
    """A normalized blocker row exactly as botsite/blockers.py emits it."""
    return {"owner_action": "an owner click", "unblocks": "the card goes live", "ask_id": ask_id}


def _stub_blocker_rows(monkeypatch, rows):
    monkeypatch.setattr(healthcheck, "_collect_registry_blockers", lambda: list(rows))


def _install_probe(monkeypatch, ask_id, verdict, detail="probe detail"):
    """Replace the REGISTRY entry's probe (resolved by exact ask id) with a
    canned coroutine; returns the call-count list for dedupe assertions."""
    calls = []

    async def fake_probe(refresh=False):
        calls.append(ask_id)
        return askverify._verdict(verdict, detail, f"fake-{ask_id}")

    entry = next(e for e in askverify.REGISTRY if e.get("ask_id") == ask_id)
    monkeypatch.setitem(entry, "probe", fake_probe)
    return calls


def test_done_detected_with_blocker_still_gated_is_flagged_and_fails(monkeypatch):
    _stub_blocker_rows(monkeypatch, [("arcade", "lumen-drift", _blocker("ASK-0010"))])
    _install_probe(monkeypatch, "ASK-0010", askverify.DONE, "release tag exists")
    ok, lines = healthcheck.check_release_drift()
    assert ok is False
    assert any(
        "arcade/lumen-drift" in ln and "FLAGGED" in ln and "ASK-0010" in ln
        and "drift: ask done-detected but registry still gated" in ln
        for ln in lines
    )


def test_still_open_probe_is_a_pass_row(monkeypatch):
    _stub_blocker_rows(monkeypatch, [("arcade", "games-web", _blocker("ASK-0011"))])
    _install_probe(monkeypatch, "ASK-0011", askverify.STILL_OPEN, "no Pages site (404)")
    ok, lines = healthcheck.check_release_drift()
    assert ok is True
    assert any(
        "arcade/games-web" in ln and "PASS" in ln and "ASK-0011" in ln and "still-open" in ln
        for ln in lines
    )


def test_probe_less_ask_is_honest_info_and_does_not_fail(monkeypatch):
    # ASK-0012 (Gumroad publish pass) is registered probe=None with the
    # honest reason — the pass must report it, never flag it.
    _stub_blocker_rows(monkeypatch, [("catalog", "de-papieren-sinaasappel", _blocker("ASK-0012"))])
    ok, lines = healthcheck.check_release_drift()
    assert ok is True
    assert any(
        "catalog/de-papieren-sinaasappel" in ln and "ASK-0012" in ln
        and "not machine-checkable" in ln and "FLAGGED" not in ln
        for ln in lines
    )


def test_probe_error_degrades_to_unknown_and_does_not_fail(monkeypatch):
    _stub_blocker_rows(monkeypatch, [("arcade", "lumen-drift", _blocker("ASK-0010"))])

    async def boom(refresh=False):
        raise RuntimeError("wat")

    entry = next(e for e in askverify.REGISTRY if e.get("ask_id") == "ASK-0010")
    monkeypatch.setitem(entry, "probe", boom)
    ok, lines = healthcheck.check_release_drift()
    assert ok is True
    assert any(
        "arcade/lumen-drift" in ln and "ASK-0010" in ln and "unknown" in ln
        and "FLAGGED" not in ln
        for ln in lines
    )


def test_unmatched_ask_id_is_flagged_as_ledger_drift(monkeypatch):
    _stub_blocker_rows(monkeypatch, [("products", "ghost-card", _blocker("ASK-9999"))])
    ok, lines = healthcheck.check_release_drift()
    assert ok is False
    assert any(
        "products/ghost-card" in ln and "FLAGGED" in ln and "ASK-9999" in ln
        and "ledger drift: ask_id matches no askverify entry" in ln
        for ln in lines
    )


def test_shared_ask_id_is_probed_once_but_every_row_reported(monkeypatch):
    # One ask gating many cards (the ASK-0012-gates-14-cards shape) must
    # cost ONE probe per run, with a verdict row per blocker regardless.
    rows = [
        ("catalog", "card-one", _blocker("ASK-0010")),
        ("catalog", "card-two", _blocker("ASK-0010")),
        ("products", "card-three", _blocker("ASK-0010")),
    ]
    _stub_blocker_rows(monkeypatch, rows)
    calls = _install_probe(monkeypatch, "ASK-0010", askverify.STILL_OPEN, "still gated upstream")
    ok, lines = healthcheck.check_release_drift()
    assert ok is True
    assert calls == ["ASK-0010"]  # exactly one probe run
    for ref in ("catalog/card-one", "catalog/card-two", "products/card-three"):
        assert any(ref in ln and "PASS" in ln for ln in lines)


def test_id_less_blocker_is_info_only_and_does_not_fail(monkeypatch):
    _stub_blocker_rows(monkeypatch, [("puddle-museum", "nl", _blocker(None))])
    ok, lines = healthcheck.check_release_drift()
    assert ok is True
    assert any(
        "puddle-museum/nl" in ln and "<no ask_id>" in ln and "FLAGGED" not in ln
        for ln in lines
    )


def test_collection_bug_degrades_to_fail_line_not_traceback(monkeypatch):
    def _boom():
        raise RuntimeError("wat")

    monkeypatch.setattr(healthcheck, "_collect_registry_blockers", _boom)
    ok, lines = healthcheck.check_release_drift()
    assert ok is False
    assert any("registry collection raised RuntimeError" in ln for ln in lines)


# --------------------------------------------------------------------------- #
# Exit-code integration — the pass folds into main()'s existing idiom.
# --------------------------------------------------------------------------- #
def _summary(rows=(), flagged=(), skipped=(), ok=True, note="x"):
    return {
        "rows": list(rows), "flagged": list(flagged),
        "skipped": list(skipped), "ok": ok, "note": note,
    }


def _stub_everything_else_healthy(monkeypatch):
    """Exit-code tests: services + registry + arcade + tester-task stubbed
    healthy so the release-drift pass is the only variable — and nothing
    touches the network."""
    monkeypatch.setattr(healthcheck, "_probe", lambda url: (200, ""))
    monkeypatch.setattr(healthcheck, "check_fleet_registry", lambda: (True, "2 lanes parsed"))
    monkeypatch.setattr(
        healthcheck.arcade_probe, "probe_registry_urls",
        lambda: _summary(note="1 URL(s) probed (live+download), 0 flagged"),
    )
    monkeypatch.setattr(
        healthcheck.testing_probe, "probe_task_urls",
        lambda: _summary(note="0 open-task URL(s) probed, 0 flagged"),
    )


def test_release_drift_turns_main_exit_nonzero(monkeypatch, capsys):
    _stub_everything_else_healthy(monkeypatch)
    _stub_blocker_rows(monkeypatch, [("arcade", "lumen-drift", _blocker("ASK-0010"))])
    _install_probe(monkeypatch, "ASK-0010", askverify.DONE, "release tag exists")
    assert healthcheck.main() == 1
    out = capsys.readouterr().out
    assert "release-drift flag (registry blockers vs askverify): FAIL" in out
    assert "FLAGGED" in out and "registry still gated" in out
    assert "RESULT: ONE OR MORE DOWN" in out


def test_no_drift_keeps_main_exit_zero(monkeypatch, capsys):
    _stub_everything_else_healthy(monkeypatch)
    _stub_blocker_rows(monkeypatch, [("arcade", "games-web", _blocker("ASK-0011"))])
    _install_probe(monkeypatch, "ASK-0011", askverify.STILL_OPEN, "no Pages site (404)")
    assert healthcheck.main() == 0
    out = capsys.readouterr().out
    assert "release-drift flag (registry blockers vs askverify): PASS" in out
    assert "RESULT: all healthy" in out
