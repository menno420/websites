"""C10 — single-source guard for the Railway `/version` deploy-probe URLs.

The readiness board's deploy-drift cell probes each websites service's public
``/version`` endpoint. Those probe URLs live in ONE place —
``app.config.SERVICE_DEPLOY_TARGETS`` (``app/readiness.py::_deploy_board`` and
``app/askverify.py`` both source from it). Separately, ``app/railway.py::SERVICES``
hardcodes the SAME Railway hosts (base URL, no ``/version`` suffix) for the gated
``/owner/environments`` page.

Two independent hardcoded host lists is exactly the drift risk: re-provision a
service on Railway (its host changes) and update one list but not the other, and
the deploy-drift board probes a stale host while the environments page shows the
new one — silently, with no test to catch it. ``test_check_no_ambient_railway_ids``
guards Railway *IDs*; nothing tied these ``/version`` URLs to a single, consistent
source. This does.

Read-only / source-level: no network, no app-behavior change.
"""

from __future__ import annotations

import re
from pathlib import Path

from app import config, railway

REPO_ROOT = Path(__file__).resolve().parent.parent
APP_DIR = REPO_ROOT / "app"

# A full Railway `/version` probe-URL literal, e.g.
#   https://botsite-production-cfd7.up.railway.app/version
_PROBE_URL_RE = re.compile(r"https?://[\w.-]+\.up\.railway\.app/version")


def _services_by_name() -> dict[str, dict]:
    return {s["name"]: s for s in railway.SERVICES}


def test_probe_url_literal_lives_only_in_config():
    """No ``app/`` module other than config.py may hardcode a `/version` probe URL.

    Anything that needs a probe URL must read ``config.SERVICE_DEPLOY_TARGETS``;
    a stray literal elsewhere is a second source that can drift.
    """
    offenders: list[str] = []
    for py in sorted(APP_DIR.rglob("*.py")):
        if py.name == "config.py":
            continue
        for i, line in enumerate(py.read_text().splitlines(), 1):
            if _PROBE_URL_RE.search(line):
                rel = py.relative_to(REPO_ROOT)
                offenders.append(f"{rel}:{i}: {line.strip()}")
    assert offenders == [], (
        "`/version` probe URLs must live only in app/config.py "
        "SERVICE_DEPLOY_TARGETS; found stray literal(s):\n" + "\n".join(offenders)
    )


def test_config_probe_urls_are_present_in_config_source():
    """Sanity: the single source really is config.py (guard can't pass vacuously)."""
    src = (APP_DIR / "config.py").read_text()
    live = [u for u in config.SERVICE_DEPLOY_TARGETS.values() if u]
    assert live, "expected at least one non-None deploy target"
    for url in live:
        assert url in src, f"{url!r} not found as a literal in app/config.py"


def test_control_plane_is_self_no_network_hop():
    """control-plane reads its own deployed sha from env — url must be None."""
    assert config.SERVICE_DEPLOY_TARGETS["control-plane"] is None


def test_every_non_none_target_is_a_version_url():
    for name, url in config.SERVICE_DEPLOY_TARGETS.items():
        if url is None:
            continue
        assert _PROBE_URL_RE.fullmatch(url), (
            f"{name} deploy target {url!r} is not a *.up.railway.app/version URL"
        )


def test_deploy_targets_and_railway_services_cover_same_names():
    """The two hardcoded lists must describe the same set of services."""
    assert set(config.SERVICE_DEPLOY_TARGETS) == set(_services_by_name()), (
        "SERVICE_DEPLOY_TARGETS and railway.SERVICES describe different service "
        "sets — one was edited without the other"
    )


def test_probe_host_matches_railway_services_host():
    """Each service's `/version` probe host must equal its railway.SERVICES base host.

    This is the drift catch: strip ``/version`` from the config probe URL and it
    must equal the base ``url`` app/railway.py advertises for the same service.
    A re-provision that touches only one list trips here.
    """
    svcs = _services_by_name()
    for name, url in config.SERVICE_DEPLOY_TARGETS.items():
        if url is None:
            continue
        probe_base = url.removesuffix("/version")
        service_base = svcs[name]["url"].rstrip("/")
        assert probe_base == service_base, (
            f"{name}: deploy-probe host {probe_base!r} (config) != environments "
            f"host {service_base!r} (railway.SERVICES) — a re-provision drifted "
            "one list from the other"
        )
