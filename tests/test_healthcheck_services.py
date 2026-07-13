"""Pin for the scripts/healthcheck.py SERVICES table (2026-07-13).

The review service went LIVE 2026-07-12 (owner-created; documented in
docs/current-state.md + app/config.py) but the healthcheck SERVICES table
was never extended — a coverage gap found by a prior session. This pin
keeps the table honest: all four services present, each with its canonical
documented production URL (review = the f027 deployment; the fc91 copy is
the labeled "parallel copy" and is deliberately NOT probed).

Offline: these assert the committed table only — no network.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
_MOD_PATH = REPO_ROOT / "scripts" / "healthcheck.py"

_spec = importlib.util.spec_from_file_location("_healthcheck_services", _MOD_PATH)
assert _spec and _spec.loader
healthcheck = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(healthcheck)

EXPECTED_SERVICES = {
    "control-plane": "https://control-plane-production-abb0.up.railway.app",
    "botsite": "https://botsite-production-cfd7.up.railway.app",
    "dashboard": "https://dashboard-production-a91b.up.railway.app",
    "review": "https://review-production-f027.up.railway.app",
}


def test_services_table_covers_all_four_services():
    assert dict(healthcheck.SERVICES) == EXPECTED_SERVICES


def test_review_service_probes_canonical_f027_url():
    """The review entry must point at the canonical f027 deployment
    (app/config.py SERVICE_DEPLOY_TARGETS + docs/current-state.md), never the fc91
    parallel copy."""
    urls = dict(healthcheck.SERVICES)
    assert urls["review"] == "https://review-production-f027.up.railway.app"
    assert all("fc91" not in base for base in urls.values())


def test_service_base_urls_have_no_trailing_slash():
    """main() concatenates base + endpoint ("/healthz", "/") — a trailing
    slash would probe //healthz."""
    for _label, base in healthcheck.SERVICES:
        assert not base.endswith("/")
