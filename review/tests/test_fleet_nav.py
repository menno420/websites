"""Footer fleet-nav strip — review.

Slice S3: the footer carries a cross-service "fleet" strip (control-plane ·
botsite · dashboard · review). URLs vendored per service (no cross-service
import). Asserts all four fleet hrefs render and the current service is marked.
Network-free: the home page reads the committed snapshot."""

from __future__ import annotations

from fastapi.testclient import TestClient

from review.app import app

client = TestClient(app)

FLEET_HREFS = [
    "https://control-plane-production-abb0.up.railway.app",
    "https://botsite-production-cfd7.up.railway.app",
    "https://dashboard-production-a91b.up.railway.app",
    "https://review-production-fc91.up.railway.app",
]


def test_footer_fleet_strip_links_all_four_services():
    html = client.get("/").text
    for href in FLEET_HREFS:
        assert f'href="{href}"' in html, f"missing fleet link: {href}"
    # this service (review) is the current one — marked, not just listed
    assert 'aria-current="page"' in html
