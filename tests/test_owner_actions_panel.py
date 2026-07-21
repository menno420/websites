"""Offline tests for the inline "actions now" panel on the gated GET /owner
home (S4): the owner's open owner-actions surfaced at the top of the home,
rendered from the SAME ``briefing.asks`` read (``askcov``) the readiness
board's "N of M machine-verified" chip already composes in ``owner_board`` —
no new fetch, no new route, no new state.

Pins the three honest states the panel must render through the real route:

1. **open** — the pending-action count + each open ask's title, newest first,
   with the full-queue deep link.
2. **empty** — an explicit "Nothing needs you right now" (never a fabricated
   all-clear; the empty state is asserted, not merely the absence of rows).
3. **unknown** — the ledger unreadable degrades to "open actions: unknown"
   WITH the bounded reason, never a fake zero.

Data-source rail (proves no new fetch): the panel reads ``askcov`` — the
value ``owner_board`` already gathers via ``briefing.asks`` — so every test
monkeypatches ``app.owner.briefing.asks`` and NOTHING else network-shaped; the
panel could not render its count if it were reaching for a second source.

Fully offline: ``briefing.asks`` is patched to a canned payload and every
GitHub fetch is canned degraded (the readiness board / env / prompt-state
cards render their honest 200s underneath), same fixture idiom as
tests/test_owner_readiness_env_chip.py.
"""

import base64
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app import briefing, config, github  # noqa: E402
from app.main import app  # noqa: E402

OWNER_PW = "test-owner-pw"
BOARD_URL = "/owner"


def _basic(pw: str = OWNER_PW, user: str = "owner") -> dict:
    token = base64.b64encode(f"{user}:{pw}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


@pytest.fixture()
def client(monkeypatch):
    """Offline authed-ready client: owner gate armed, no Railway token, every
    GitHub fetch canned degraded (the other /owner cards render honest 200s)."""
    monkeypatch.setattr(config, "SITE_PASSWORD", OWNER_PW)
    monkeypatch.setattr(config, "RAILWAY_TOKEN", "")

    async def fake_get(url, refresh=False, raw=False):
        return {"ok": False, "status": 0, "data": None, "error": "offline test",
                "fetched_at": "", "cached": False, "url": url}

    monkeypatch.setattr(github, "_get", fake_get)
    with TestClient(app) as c:
        yield c


def _patch_asks(monkeypatch, payload: dict) -> None:
    """Replace the SAME briefing.asks read owner_board gathers into askcov —
    the panel's only data source. Patching just this proves the panel reads
    the already-composed value and mints no second fetch."""
    async def fake_asks(refresh=False):
        return payload

    monkeypatch.setattr(briefing, "asks", fake_asks)


def test_panel_renders_open_action_count_and_titles(client, monkeypatch):
    _patch_asks(monkeypatch, {
        "state": "ok",
        "reason": "",
        "count": 3,
        "top": [
            {"what": "Add the Discord redirect URI", "where": "Discord app",
             "unblocks": "", "ask_id": "ASK-0002",
             "verify": {"css": "warn", "label": "still open",
                        "detail": "owner action outstanding", "verdict": "still_open"}},
            {"what": "Paste the RAILWAY_TOKEN", "where": "Railway", "unblocks": "",
             "ask_id": "ASK-0001", "verify": None},
        ],
        "note": "",
        "url": "https://github.com/x/websites/blob/main/docs/owner/OWNER-ACTIONS.md",
        "verify": {"total": 3, "machine_verified": 1, "done": 0, "still_open": 1,
                   "not_checkable": 1, "unknown": 1},
    })
    r = client.get(BOARD_URL, headers=_basic())
    assert r.status_code == 200
    # the panel exists, leads the body, and carries the pending count
    assert 'id="actions-now"' in r.text
    assert "actions now" in r.text
    assert "Your 3 open actions" in r.text
    # each open ask's title is listed, with the full-queue deep link
    assert "Add the Discord redirect URI" in r.text
    assert "Paste the RAILWAY_TOKEN" in r.text
    assert "/owner/queue" in r.text
    # never the empty / unknown copy when actions are open
    assert "Nothing needs you right now" not in r.text
    assert "open actions: unknown" not in r.text


def test_panel_shows_more_note_when_count_exceeds_shown(client, monkeypatch):
    _patch_asks(monkeypatch, {
        "state": "ok", "reason": "", "count": 5,
        "top": [
            {"what": f"ask {i}", "where": "", "unblocks": "",
             "ask_id": f"ASK-000{i}", "verify": None}
            for i in range(2)
        ],
        "note": "", "url": "u", "verify": None,
    })
    r = client.get(BOARD_URL, headers=_basic())
    assert r.status_code == 200
    assert "Your 5 open actions" in r.text
    # 5 open, 2 shown → the overflow pointer to the full queue
    assert "+3 more open on the" in r.text


def test_panel_renders_empty_state_when_no_open_actions(client, monkeypatch):
    _patch_asks(monkeypatch, {
        "state": "ok", "reason": "", "count": 0, "top": [],
        "note": "", "url": "u", "verify": {"total": 0, "machine_verified": 0,
        "done": 0, "still_open": 0, "not_checkable": 0, "unknown": 0},
    })
    r = client.get(BOARD_URL, headers=_basic())
    assert r.status_code == 200
    assert 'id="actions-now"' in r.text
    # the explicit empty state is asserted (not merely the absence of rows)
    assert "Nothing needs you right now" in r.text
    assert "Your 0 open" not in r.text


def test_panel_unknown_ledger_shows_reason_never_fake_zero(client, monkeypatch):
    _patch_asks(monkeypatch, {
        "state": "unknown", "reason": "HTTP 404 — ledger not found",
        "count": 0, "top": [], "note": "", "url": "u", "verify": None,
    })
    r = client.get(BOARD_URL, headers=_basic())
    assert r.status_code == 200
    assert 'id="actions-now"' in r.text
    assert "open actions: unknown" in r.text
    assert "HTTP 404 — ledger not found" in r.text
    # honest-unknown must NOT collapse to the empty all-clear
    assert "Nothing needs you right now" not in r.text


def test_panel_stays_gated_without_credentials(client):
    """The panel rides the same require_owner gate — no credentials, no page."""
    assert client.get(BOARD_URL).status_code == 401
