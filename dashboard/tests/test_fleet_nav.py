"""Footer fleet-nav strip — dashboard.

Slice S3: the footer carries a cross-service "fleet" strip (control-plane ·
botsite · dashboard · review). URLs vendored per service (no cross-service
import). Asserts all four fleet hrefs render and the current service is marked."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from dashboard import app as app_module
from dashboard import control_plane as cp
from dashboard import data_source as ds
from dashboard.tests.test_dashboard import ARCADE_FIXTURE, CONSOLE_FIXTURE, DASHBOARD_FIXTURE

FLEET_HREFS = [
    "https://control-plane-production-abb0.up.railway.app",
    "https://botsite-production-cfd7.up.railway.app",
    "https://dashboard-production-a91b.up.railway.app",
    "https://review-production-fc91.up.railway.app",
]


@pytest.fixture()
def client():
    ds.clear_cache()
    cp.controller.clear()
    ds.prime_cache(ds.DASHBOARD_JSON_URL, DASHBOARD_FIXTURE)
    ds.prime_cache(ds.CONSOLE_JSON_URL, CONSOLE_FIXTURE)
    ds.prime_cache(ds.ARCADE_JSON_URL, ARCADE_FIXTURE)
    ds.prime_cache(ds.RELEASES_JSON_URL, {"entries": [], "drift_count": 0})
    ds.set_client(ds.make_client())  # never actually hit (cache is warm)
    with TestClient(app_module.app) as c:
        yield c
    ds.clear_cache()
    cp.controller.clear()


def test_footer_fleet_strip_links_all_four_services(client):
    html = client.get("/").text
    for href in FLEET_HREFS:
        assert f'href="{href}"' in html, f"missing fleet link: {href}"
    # this service (dashboard) is the current one — marked, not just listed
    assert 'aria-current="page"' in html
