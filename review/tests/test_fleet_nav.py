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
    "https://superbot-app.up.railway.app",
    "https://superbot-dashboard.up.railway.app",
    # review's SELF-link is root-relative ("/"): the static exporter's
    # base-path pass rewrites it exactly once, where a hardcoded absolute
    # Pages URL was double-prefixed to /websites/websites/ by the host-root
    # feed rewrite (Codex #510 round 2, P1).
    "/",
]


def test_footer_fleet_strip_links_all_four_services():
    html = client.get("/").text
    for href in FLEET_HREFS:
        assert f'href="{href}"' in html, f"missing fleet link: {href}"
    # this service (review) is the current one — marked, not just listed
    assert 'aria-current="page"' in html
    # the absolute self-URL must NOT come back (the double-prefix source).
    assert 'href="https://menno420.github.io/websites/"' not in html
