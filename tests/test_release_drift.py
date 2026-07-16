"""Unit tests for the shared release-drift classifier (app/release_drift.py).

The classifier is the ONE source of truth for the drift verdict that
scripts/healthcheck.py's release-drift pass and /owner/queue's drift chip
both render. Pure — no network, no files, no botsite import: every input
the two callers already hold is passed in directly.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import askverify, release_drift  # noqa: E402


# --------------------------------------------------------------------------- #
# classify — every drift kind + the healthy pass row
# --------------------------------------------------------------------------- #
def test_id_less_blocker_is_info_never_flagged():
    v = release_drift.classify(None, entry_exists=False, verdict=None)
    assert v["kind"] == release_drift.ID_LESS
    assert v["flagged"] is False
    assert v["mark"] == "info"
    assert v["token"] == "<no ask_id>"
    assert v["reason"] == "blocker carries no ledger id — nothing to join"


def test_unregistered_ask_id_is_ledger_drift_and_flags():
    v = release_drift.classify("ASK-9999", entry_exists=False, verdict=None)
    assert v["kind"] == release_drift.LEDGER_DRIFT
    assert v["flagged"] is True
    assert v["mark"] == "FLAGGED"
    assert v["token"] == "ASK-9999"
    assert "ledger drift: ask_id matches no askverify entry" in v["reason"]


def test_done_detected_while_gated_is_drift_and_flags():
    v = release_drift.classify(
        "ASK-0010", entry_exists=True, verdict=askverify.DONE
    )
    assert v["kind"] == release_drift.DONE_GATED
    assert v["flagged"] is True
    assert v["mark"] == "FLAGGED"
    assert "drift: ask done-detected but registry still gated" in v["reason"]


def test_still_open_is_the_healthy_pass_row():
    v = release_drift.classify(
        "ASK-0011", entry_exists=True, verdict=askverify.STILL_OPEN
    )
    assert v["kind"] == release_drift.STILL_OPEN
    assert v["flagged"] is False
    assert v["mark"] == "PASS"
    assert "still-open — registry gate matches reality" in v["reason"]


def test_not_checkable_is_honest_info_with_detail():
    v = release_drift.classify(
        "ASK-0012",
        entry_exists=True,
        verdict=askverify.NOT_CHECKABLE,
        detail="Gumroad listing state not observable",
    )
    assert v["kind"] == release_drift.NOT_CHECKABLE
    assert v["flagged"] is False
    assert v["mark"] == "info"
    assert "not machine-checkable — Gumroad listing state not observable" in v["reason"]


def test_not_checkable_without_detail_falls_back():
    v = release_drift.classify(
        "ASK-0012", entry_exists=True, verdict=askverify.NOT_CHECKABLE
    )
    assert "not machine-checkable — no probe registered" in v["reason"]


def test_unknown_verdict_is_info_never_flagged():
    v = release_drift.classify(
        "ASK-0010",
        entry_exists=True,
        verdict=askverify.UNKNOWN,
        detail="probe timed out",
    )
    assert v["kind"] == release_drift.UNKNOWN
    assert v["flagged"] is False
    assert v["mark"] == "info"
    assert "unknown — probe timed out" in v["reason"]


def test_none_verdict_degrades_to_unknown_never_invents_state():
    v = release_drift.classify("ASK-0010", entry_exists=True, verdict=None)
    assert v["kind"] == release_drift.UNKNOWN
    assert v["flagged"] is False
    assert "unknown — probe could not tell" in v["reason"]


# --------------------------------------------------------------------------- #
# chip — the owner-console projection: a badge for a drifting open ask only
# --------------------------------------------------------------------------- #
def _verify(verdict: str, detail: str = "") -> dict:
    return askverify._verdict(verdict, detail, "fake-probe")


def test_chip_shown_for_done_detected_open_ask():
    c = release_drift.chip(_verify(askverify.DONE, "release tag exists"))
    assert c is not None
    assert c["css"] == "warn"
    assert "drift" in c["label"] and "done-detected but still gated" in c["label"]
    # the probe reason rides in the hover title
    assert "release tag exists" in c["title"]


def test_chip_omitted_for_still_open_ask():
    assert release_drift.chip(_verify(askverify.STILL_OPEN, "no Pages site")) is None


def test_chip_omitted_for_not_checkable_ask():
    assert release_drift.chip(_verify(askverify.NOT_CHECKABLE, "no probe")) is None


def test_chip_omitted_for_unknown_ask():
    assert release_drift.chip(_verify(askverify.UNKNOWN, "timed out")) is None


def test_chip_omitted_when_no_verify():
    assert release_drift.chip(None) is None
    assert release_drift.chip({}) is None
