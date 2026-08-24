"""Pin for the scripts/healthcheck.py SERVICES table (2026-07-13).

The review service went LIVE 2026-07-12 and RETIRED 2026-08-20 into a
GitHub Pages static export (keep-bot-only consolidation; websites decisions
ledger) — this checker probes RAILWAY services only, so the table now
carries the three that remain, each with its canonical superbot-websites
production URL. The static review record keeps rendering-layer coverage in
scripts/smoke_crawl.py instead.

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
    "botsite": "https://superbot-app.up.railway.app",
    "dashboard": "https://superbot-dashboard.up.railway.app",
}


def test_services_table_covers_the_three_railway_services():
    assert dict(healthcheck.SERVICES) == EXPECTED_SERVICES


def test_review_railway_urls_never_return():
    """review retired to GitHub Pages 2026-08-20 — neither its old canonical
    fc91 URL nor the long-deleted f027 copy may re-enter this table (a
    re-added entry would probe a deleted service red every 6 hours)."""
    urls = dict(healthcheck.SERVICES)
    assert "review" not in urls
    assert all("fc91" not in base and "f027" not in base for base in urls.values())


def test_service_base_urls_have_no_trailing_slash():
    """main() concatenates base + endpoint ("/healthz", "/") — a trailing
    slash would probe //healthz."""
    for _label, base in healthcheck.SERVICES:
        assert not base.endswith("/")
