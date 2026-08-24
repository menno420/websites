"""Offline tests for the canonical eight-product directory (/directory).

Pins: one exact row and friendly public URL per audited product, explicit
public/read-only/archive boundaries, and measured liveness only.
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app import github, nav, web_presence  # noqa: E402
from app.main import app  # noqa: E402

REGISTRY = json.loads(web_presence.REGISTRY_PATH.read_text(encoding="utf-8"))

CANONICAL_PRODUCTS = {
    "control-plane": "https://control-plane-production-abb0.up.railway.app/",
    "superbot": "https://superbot-app.up.railway.app/",
    "superbot-dashboard": "https://superbot-dashboard.up.railway.app/",
    "program-review": "https://menno420.github.io/websites/",
    "product-forge": "https://menno420.github.io/product-forge/",
    "couch-legend": "https://menno420.github.io/couch-legend/",
    "gba-homebrew": "https://menno420.github.io/gba-homebrew/",
    "curious-research": "https://menno420.github.io/curious-research/",
}


def _result(url, status, ok, error=""):
    return {"ok": ok, "status": status, "data": None, "error": error,
            "fetched_at": "12:00:00 UTC", "cached": False, "url": url}


def _probes_up(monkeypatch):
    async def fake_get(url, refresh=False, raw=False, follow_redirects=False):
        return _result(url, 200, True)

    monkeypatch.setattr(github, "_get", fake_get)


def _probes_down(monkeypatch):
    async def fake_get(url, refresh=False, raw=False, follow_redirects=False):
        return _result(url, 0, False, "ConnectError: probe refused (offline test)")

    monkeypatch.setattr(github, "_get", fake_get)


# --- the page -----------------------------------------------------------


def test_directory_renders_canonical_eight_with_friendly_urls(monkeypatch):
    _probes_up(monkeypatch)
    with TestClient(app) as c:
        r = c.get("/directory")
    assert r.status_code == 200
    assert ">live portfolio</h2>" in r.text
    assert ">health</h2>" in r.text
    assert r.text.count('data-row-id="') == 8
    for product_id, url in CANONICAL_PRODUCTS.items():
        assert f'data-row-id="{product_id}"' in r.text
        assert f'href="{url}"' in r.text
    for project in ("websites", "product-forge", "couch-legend",
                    "gba-homebrew", "curious-research"):
        assert f"<h3>{project}</h3>" in r.text
    assert "Public read-only; owner actions in /admin are Discord-gated." in r.text
    assert "Public archive; the retired live assistant" in r.text
    assert "phase-1 RPG mining character-sheet demo over two mock characters" in r.text
    assert "external business surfaces" not in r.text
    assert "pending publish" not in r.text
    assert "no URL recorded" not in r.text
    # Phone-width rendering exposes every field as a labelled product card;
    # the public URL is not hidden behind a five-column sideways scroll.
    assert '<table class="portfolio-table">' in r.text
    assert r.text.count('data-label="public URL"') == 8
    assert ".card table.portfolio-table { display:block; min-width:0; }" in r.text
    assert ".portfolio-table .portfolio-value { min-width:0; overflow-wrap:anywhere; }" in r.text
    # the registry file is named on the page (single source of truth)
    assert "app/data/web_presence.json" in r.text


def test_registry_is_exactly_the_canonical_eight():
    assert {s["id"]: s["url"] for s in REGISTRY["sites"]} == CANONICAL_PRODUCTS


def test_probe_success_shows_live_with_as_of(monkeypatch):
    _probes_up(monkeypatch)
    with TestClient(app) as c:
        r = c.get("/directory")
    assert 'data-health="live"' in r.text
    assert "12:00:00 UTC" in r.text  # the as-of timestamp from the probe
    assert 'data-health="down"' not in r.text


def test_probe_failure_renders_honest_state_never_a_green_badge(monkeypatch):
    _probes_down(monkeypatch)
    with TestClient(app) as c:
        r = c.get("/directory")
    assert r.status_code == 200  # degrades, never 500s
    # NO fabricated liveness anywhere on the page
    assert 'data-health="live"' not in r.text
    assert 'data-health="down"' in r.text
    assert "probe refused (offline test)" in r.text
    assert r.text.count('data-health="down"') >= 8
    assert 'data-health="pending"' not in r.text
    assert 'data-health="no-url"' not in r.text


def test_only_the_eight_canonical_urls_are_probed(monkeypatch):
    calls = []

    async def fake_get(url, refresh=False, raw=False, follow_redirects=False):
        calls.append((url, follow_redirects))
        return _result(url, 200, True)

    monkeypatch.setattr(github, "_get", fake_get)
    with TestClient(app) as c:
        r = c.get("/directory")
    assert r.status_code == 200
    assert {url for url, _follow in calls} == set(CANONICAL_PRODUCTS.values())
    assert len(calls) == 8
    assert all(follow for _url, follow in calls)


def test_degraded_is_not_live(monkeypatch):
    async def fake_get(url, refresh=False, raw=False, follow_redirects=False):
        return _result(url, 503, False, "Service Unavailable")

    monkeypatch.setattr(github, "_get", fake_get)
    with TestClient(app) as c:
        r = c.get("/directory")
    assert 'data-health="live"' not in r.text
    assert 'data-health="degraded"' in r.text
    assert "degraded (HTTP 503)" in r.text


def test_unreadable_registry_banners_instead_of_500(monkeypatch, tmp_path):
    bad = tmp_path / "web_presence.json"
    bad.write_text("{not json", encoding="utf-8")
    reg = web_presence.load_registry(bad)
    assert reg["ok"] is False and "unreadable" in reg["error"]
    # route the whole page over the broken registry: 200 + banner, never a 500
    real_load = web_presence.load_registry
    monkeypatch.setattr(web_presence, "load_registry", lambda: real_load(bad))
    _probes_up(monkeypatch)
    with TestClient(app) as c:
        r = c.get("/directory")
    assert r.status_code == 200
    assert "registry unreadable" in r.text
    assert 'data-health="live"' not in r.text  # no rows, no invented health


def test_overview_classifies_without_a_network(monkeypatch):
    _probes_down(monkeypatch)
    data = asyncio.run(web_presence.overview())
    assert data["ok"] is True
    assert data["counts"]["probed"] == len(data["probed"])
    assert all(r["health"]["state"] == "down" for r in data["probed"])
    assert data["counts"]["down"] == len(data["probed"])
    assert data["counts"]["live"] == 0


# --- cross-link: the console home section map ----------------------------


def test_home_section_map_links_the_directory(monkeypatch):
    # full-offline fakes (the test_console_home pattern): the board's own
    # fan-out degrades honestly while the section map still renders
    async def fake_get(url, refresh=False, raw=False, follow_redirects=False):
        return _result(url, 0, False, "offline test")

    async def fake_fetch(repo, path, ref="main", refresh=False):
        return _result("", 404, False, "nf")

    async def fake_api(repo, subpath="", refresh=False):
        return _result("", 404, False, "nf")

    monkeypatch.setattr(github, "_get", fake_get)
    monkeypatch.setattr(github, "fetch_file", fake_fetch)
    monkeypatch.setattr(github, "repo_api", fake_api)
    with TestClient(app) as c:
        r = c.get("/")
    assert r.status_code == 200
    assert 'href="/directory"' in r.text
    assert nav.item("directory")["label"] in r.text
    # single source of truth: the home page LINKS the directory, it does not
    # duplicate the site list (no directory tables on the board)
    assert 'id="our-sites"' not in r.text
    assert 'id="external"' not in r.text


def test_directory_is_in_the_nav_manifest():
    assert "directory" in nav.keys()
    assert nav.category_for("directory") == "console"
    assert "/directory" in nav.all_hrefs()


# --- registry contract (other seats add rows by PR) -----------------------


def test_registry_rows_honor_the_schema():
    sites = REGISTRY["sites"]
    ids = [s["id"] for s in sites]
    assert len(ids) == len(set(ids)), "row ids must be unique"
    for s in sites:
        for field in ("id", "title", "section", "kind", "description",
                      "access", "status", "notes"):
            assert s.get(field) is not None, f"{s.get('id')}: missing {field}"
        assert s["section"] == "our-sites"
        assert s["status"] in web_presence.KNOWN_STATUSES
        if s.get("probe"):
            assert s.get("url"), f"{s['id']}: probe:true requires a url"
        if s["section"] == "our-sites":
            assert s.get("project") in REGISTRY["projects"], (
                f"{s['id']}: our-sites rows carry a known project"
            )
    assert len(sites) == 8
    assert all(s["status"] == "live-service" and s["probe"] for s in sites)


def test_registry_content_is_autoescaped(monkeypatch):
    """Registry rows are untrusted DATA — a hostile row renders escaped."""
    evil = {
        "ok": True,
        "error": "",
        "as_of": "2026-07-12",
        "projects": {"p": "<script>alert('proj')</script>"},
        "sites": [{
            "id": "evil",
            "title": "<script>alert('xss')</script>",
            "url": None,
            "section": "our-sites",
            "project": "p",
            "kind": "<img src=x onerror=alert(1)>",
            "description": "desc",
            "access": "Public.",
            "status": "url-unrecorded",
            "notes": "<b>notes</b>",
            "probe": False,
        }],
    }
    monkeypatch.setattr(web_presence, "load_registry", lambda: evil)
    _probes_up(monkeypatch)
    with TestClient(app) as c:
        r = c.get("/directory")
    assert r.status_code == 200
    assert "<script>alert(" not in r.text
    assert "&lt;script&gt;alert(" in r.text
    assert "<img src=x" not in r.text
    assert "<b>notes</b>" not in r.text
