"""Owner-console release-drift chip render test (2026-07-16).

The gated /owner/queue renders a release-drift chip beside each open ask's
askverify preflight chip, reusing #365's verdict via app/release_drift.py:
a done-detected ask whose gate is still up shows "⚠ drift: done-detected
but still gated"; a still-open (or otherwise non-drifting) ask shows no
chip. Read-only — no route, no write. The public /queue stays untouched.

Offline throughout, mirroring tests/test_owner_queue_preflight.py:
TestClient, owner_queue.overview patched to synthetic asks, and
askverify.annotate stubbed to attach canned probe verdicts so no probe
touches the network.
"""

from __future__ import annotations

import base64
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app import askverify, config, owner_assist, owner_queue, writeback  # noqa: E402
from app import owner  # noqa: E402
from app.main import app  # noqa: E402

OWNER_PW = "test-owner-pw"
SAME_ORIGIN = "http://testserver"

DONE_ASK = "Publish the lumen-drift v1.3 release on gba-homebrew"
OPEN_ASK = "Set SITE_PASSWORD on the botsite service"


def _basic(pw: str = OWNER_PW, user: str = "owner") -> dict:
    token = base64.b64encode(f"{user}:{pw}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


def _headers() -> dict:
    return {**_basic(), "Origin": SAME_ORIGIN}


def _ask(headline: str) -> dict:
    return {
        "what": headline,
        "text": "",
        "fields": {},
        "sources": [{"label": "lane", "kind": "lane", "age_human": "1h",
                     "age_hours": 1.0, "url": "https://example.test/src"}],
    }


def _overview_data(items) -> dict:
    return {
        "items": items,
        "lane_notes": [],
        "fleet_manager": {"state": "ok", "token_set": False, "url": "",
                          "items": [], "preamble": "", "body_html": "",
                          "reason": ""},
        "field_order": [],
        "summary": {"total": len(items), "deduped": 0,
                    "lanes_with_asks": 0, "lanes_total": 0},
        "unreadable_lanes": [],
        "lane_source": {"label": "", "url": ""},
    }


def _patch_overview(monkeypatch, items) -> None:
    async def fake(refresh=False):
        return _overview_data(items)

    monkeypatch.setattr(owner_queue, "overview", fake)


def _patch_verdicts(monkeypatch, verdict_by_headline: dict) -> None:
    """Stub askverify.annotate so each item gets a canned verdict keyed by
    its headline — no probe ever runs."""
    async def fake_annotate(items, refresh=False):
        for it in items:
            verdict = verdict_by_headline.get(askverify.headline_of(it))
            it["verify"] = askverify._verdict(verdict, "probe reason", "fake")
        return {"total": len(items), "machine_verified": 0}

    monkeypatch.setattr(askverify, "annotate", fake_annotate)


@pytest.fixture(autouse=True)
def _reset_state():
    owner.reset_rate_limits()
    owner_assist.reset_assist_state()
    yield
    owner.reset_rate_limits()
    owner_assist.reset_assist_state()


@pytest.fixture()
def client(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "SITE_PASSWORD", OWNER_PW)
    monkeypatch.setenv(writeback.ENV_DB_PATH, str(tmp_path / "wb.sqlite3"))
    with TestClient(app) as c:
        yield c


def test_drift_chip_shown_for_done_detected_ask_and_omitted_otherwise(client, monkeypatch):
    _patch_overview(monkeypatch, [_ask(DONE_ASK), _ask(OPEN_ASK)])
    _patch_verdicts(monkeypatch, {
        DONE_ASK: askverify.DONE,
        OPEN_ASK: askverify.STILL_OPEN,
    })
    r = client.get("/owner/queue", headers=_headers())
    assert r.status_code == 200
    # the done-detected ask drifts — chip present, exactly once
    assert "drift: done-detected but still gated" in r.text
    assert r.text.count("drift: done-detected but still gated") == 1
    # the still-open ask is healthy — no drift chip for it
    assert "blocker without probe" not in r.text


def test_no_drift_chip_when_every_ask_still_open(client, monkeypatch):
    _patch_overview(monkeypatch, [_ask(OPEN_ASK)])
    _patch_verdicts(monkeypatch, {OPEN_ASK: askverify.STILL_OPEN})
    r = client.get("/owner/queue", headers=_headers())
    assert r.status_code == 200
    assert "drift: done-detected but still gated" not in r.text


def test_public_queue_has_no_drift_chip(client, monkeypatch):
    # The public /queue renders the same asks but never the gated drift chip.
    _patch_overview(monkeypatch, [_ask(DONE_ASK)])
    _patch_verdicts(monkeypatch, {DONE_ASK: askverify.DONE})
    r = client.get("/queue")
    assert r.status_code == 200
    assert "drift: done-detected but still gated" not in r.text
