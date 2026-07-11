"""Offline unit tests for slice 18: the board-row heartbeat chip
(fleet.heartbeat_freshness + board render) and the `tooling:` capability
token (KNOWN_KEYS leak-guard + /fleet row with the ritual-only warning).
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app import fleet, github  # noqa: E402
from app.main import app  # noqa: E402


def _res(ok=True, status=200, data=None, error=""):
    return {"ok": ok, "status": status, "data": data, "error": error,
            "fetched_at": "", "cached": False, "url": ""}


_FRESH_STATUS = (
    "# websites · status\nupdated: 2100-01-01T00:00Z\nhealth: green (ok)\n"
)
_NO_STAMP_STATUS = "# x · status\nphase: no updated line here\n"


# --------------------------------------------------------------------------- #
# heartbeat_freshness
# --------------------------------------------------------------------------- #


def test_heartbeat_freshness_ok_and_honest_none(monkeypatch):
    async def fake_fetch(repo, path, ref="main", refresh=False):
        if repo == "fresh":
            return _res(data=_FRESH_STATUS)
        if repo == "unstamped":
            return _res(data=_NO_STAMP_STATUS)
        return _res(ok=False, status=404, data=None, error="nf")

    monkeypatch.setattr(github, "fetch_file", fake_fetch)

    fresh = asyncio.run(fleet.heartbeat_freshness("fresh"))
    assert fresh is not None and fresh["ok"] is True and "age_hours" in fresh

    # no readable heartbeat -> None (no chip, never a guessed age)
    assert asyncio.run(fleet.heartbeat_freshness("missing")) is None
    # heartbeat exists but updated: does not parse -> None (honest)
    assert asyncio.run(fleet.heartbeat_freshness("unstamped")) is None


def test_board_renders_heartbeat_chip(monkeypatch):
    async def fake_get(url, refresh=False, raw=False):
        return {"ok": False, "status": 0, "data": None, "error": "offline test",
                "fetched_at": "", "cached": False, "url": url}

    async def fake_fetch(repo, path, ref="main", refresh=False):
        if repo == "websites" and path == "control/status.md":
            return _res(data=_FRESH_STATUS)
        return _res(ok=False, status=404, data=None, error="nf")

    async def fake_api(repo, subpath="", refresh=False):
        return _res(ok=False, status=404, data=None, error="nf")

    monkeypatch.setattr(github, "_get", fake_get)
    monkeypatch.setattr(github, "fetch_file", fake_fetch)
    monkeypatch.setattr(github, "repo_api", fake_api)
    with TestClient(app) as c:
        r = c.get("/")
    assert r.status_code == 200
    assert "lane heartbeat:" in r.text
    assert r.text.count("lane heartbeat:") == 1  # only the repo with a heartbeat
    assert 'href="/fleet"' in r.text  # chip deep-links the fleet page


def test_board_no_heartbeat_chip_when_all_unreadable(monkeypatch):
    async def fake_get(url, refresh=False, raw=False):
        return {"ok": False, "status": 0, "data": None, "error": "offline test",
                "fetched_at": "", "cached": False, "url": url}

    async def fail(repo, path, ref="main", refresh=False):
        return _res(ok=False, status=503, data=None, error="offline")

    async def fail_api(repo, subpath="", refresh=False):
        return _res(ok=False, status=503, data=None, error="offline")

    monkeypatch.setattr(github, "_get", fake_get)
    monkeypatch.setattr(github, "fetch_file", fail)
    monkeypatch.setattr(github, "repo_api", fail_api)
    with TestClient(app) as c:
        r = c.get("/")
    assert r.status_code == 200 and "lane heartbeat:" not in r.text


# --------------------------------------------------------------------------- #
# tooling: token
# --------------------------------------------------------------------------- #


def test_tooling_is_known_key_and_never_leaks():
    text = (
        "# lane · status\nupdated: 2026-07-11T07:00Z\nhealth: green (ok)\n"
        "blockers: none\n"
        "tooling: ritual-only\n"
        "orders: acked=001 done=001\n"
    )
    fields = fleet.parse_status(text, "lane")["fields"]
    assert fields["tooling"] == "ritual-only"
    assert "tooling" not in fields["blockers"]


def test_fleet_page_flags_ritual_only_tooling(monkeypatch):
    body = (
        "# lane · status\nupdated: 2026-07-11T07:00Z\nhealth: green (ok)\n"
        "tooling: ritual-only\n"
    )

    async def fake_fetch(repo, path, ref="main", refresh=False):
        if path.startswith("control/status"):
            return _res(data=body)
        return _res(ok=False, status=404, data=None, error="nf")

    async def fake_api(repo, subpath="", refresh=False):
        return _res(ok=False, status=404, data=None, error="nf")

    monkeypatch.setattr(github, "fetch_file", fake_fetch)
    monkeypatch.setattr(github, "repo_api", fake_api)
    r = TestClient(app).get("/fleet")
    assert r.status_code == 200
    assert "<th>tooling</th>" in r.text and "cannot land work" in r.text
