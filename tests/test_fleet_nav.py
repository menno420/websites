"""Footer fleet-nav strip — control-plane (app/).

Slice S3: every service's footer now carries a small cross-service "fleet" strip
so a visitor can move between control-plane · botsite · dashboard · review. The
four live URLs are vendored per service (no cross-service import). This asserts
all four fleet hrefs render on a representative page and the current service is
marked (aria-current)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import github  # noqa: E402
from app.main import app  # noqa: E402

FLEET_HREFS = [
    "https://control-plane-production-abb0.up.railway.app",
    "https://botsite-production-cfd7.up.railway.app",
    "https://dashboard-production-a91b.up.railway.app",
    "https://review-production-fc91.up.railway.app",
]


@pytest.fixture()
def client(monkeypatch):
    async def fake_get(url, refresh=False, raw=False):
        return {
            "ok": False, "status": 0, "data": None, "error": "offline test",
            "fetched_at": "", "cached": False, "url": url,
        }

    monkeypatch.setattr(github, "_get", fake_get)
    with TestClient(app) as c:
        yield c


def test_footer_fleet_strip_links_all_four_services(client):
    html = client.get("/").text
    for href in FLEET_HREFS:
        assert f'href="{href}"' in html, f"missing fleet link: {href}"
    # this service (control-plane) is the current one — marked, not just listed
    assert 'aria-current="page"' in html
