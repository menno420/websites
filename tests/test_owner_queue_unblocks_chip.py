"""Render test for the owner-queue "unblocks N cards" chip.

The gated /owner/queue page annotates each open ask with the count of
public product cards its ask_id gates (app/card_gating.py) and renders an
"unblocks N cards" chip beside the existing verify chip. This test drives
the real route behind the owner gate and asserts the chip appears for an ask
that gates ≥1 card, hides for an ask that gates none, and pluralizes
honestly. Offline throughout (every GitHub seam faked), mirroring
tests/test_owner_queue_preflight.py.
"""

from __future__ import annotations

import base64
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app import card_gating, config, github, owner, owner_queue  # noqa: E402
from app.main import app  # noqa: E402

OWNER_PW = "test-owner-pw"


def _basic(pw: str = OWNER_PW, user: str = "owner") -> dict:
    token = base64.b64encode(f"{user}:{pw}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


def _offline(url=""):
    return {"ok": False, "status": 0, "data": None, "error": "offline test",
            "fetched_at": "", "cached": False, "url": url}


def _ask(headline: str, ask_id: str | None) -> dict:
    return {
        "what": headline,
        "text": "",
        "ask_id": ask_id,
        "fields": {},
        "sources": [{"label": "lane", "kind": "lane", "age_human": "1h",
                     "url": "https://example.test/src"}],
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


@pytest.fixture(autouse=True)
def _reset_state():
    owner.reset_rate_limits()
    yield
    owner.reset_rate_limits()


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setattr(config, "SITE_PASSWORD", OWNER_PW)

    async def fake_get(url, refresh=False, raw=False):
        return _offline(url)

    monkeypatch.setattr(github, "_get", fake_get)
    with TestClient(app) as c:
        yield c


def _patch_overview(monkeypatch, items) -> None:
    async def fake(refresh=False):
        return _overview_data(items)

    monkeypatch.setattr(owner_queue, "overview", fake)


def _patch_gating(monkeypatch, mapping) -> None:
    monkeypatch.setattr(
        card_gating, "load_gating", lambda data_dir=None: mapping
    )


def test_chip_shows_for_ask_gating_cards(client, monkeypatch):
    _patch_overview(monkeypatch, [
        _ask("The multi-gate owner action", "ASK-0500"),
    ])
    _patch_gating(monkeypatch, {
        "ASK-0500": [
            {"registry": "catalog", "slug": "a", "title": "Card Alpha"},
            {"registry": "products", "slug": "b", "title": "Card Beta"},
            {"registry": "catalog", "slug": "c", "title": "Card Gamma"},
        ],
    })
    r = client.get("/owner/queue", headers=_basic())
    assert r.status_code == 200
    assert "unblocks 3 cards" in r.text
    # the tooltip names the gated cards across registries
    assert "catalog: Card Alpha" in r.text
    assert "products: Card Beta" in r.text


def test_chip_singular_pluralizes_honestly(client, monkeypatch):
    _patch_overview(monkeypatch, [
        _ask("The single-gate owner action", "ASK-0501"),
    ])
    _patch_gating(monkeypatch, {
        "ASK-0501": [{"registry": "arcade", "slug": "z", "title": "Only One"}],
    })
    r = client.get("/owner/queue", headers=_basic())
    assert r.status_code == 200
    assert "unblocks 1 card" in r.text
    assert "unblocks 1 cards" not in r.text


def test_chip_hidden_when_no_cards_gated(client, monkeypatch):
    _patch_overview(monkeypatch, [
        _ask("An ask gating nothing", "ASK-0502"),
        _ask("A legacy ask with no id", None),
    ])
    _patch_gating(monkeypatch, {})  # nothing gated
    r = client.get("/owner/queue", headers=_basic())
    assert r.status_code == 200
    assert "unblocks" not in r.text


def test_chip_renders_over_committed_registries(client, monkeypatch):
    """End-to-end with the REAL card_gating over the committed registries:
    an ask carrying a known gating id (ASK-0012, the Gumroad publish pass)
    surfaces a non-zero chip — no gating monkeypatch."""
    _patch_overview(monkeypatch, [
        _ask("One Gumroad publish click", "ASK-0012"),
    ])
    r = client.get("/owner/queue", headers=_basic())
    assert r.status_code == 200
    assert "unblocks" in r.text and "cards" in r.text
