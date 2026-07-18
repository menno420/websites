"""Offline tests for the ORDER 021 web-presence directory (/directory).

Pins: the three sections render with their seed rows; the reliable-grace
parallel copies carry the duplicate label (never presented as distinct
products); the console-home section map links the directory; and liveness is
NEVER fabricated — a failed probe renders down/degraded, a URL-less row an
honest absence, a pending-publish row "pending publish", and no green badge
appears without a real 2xx. Registry contract is pinned so other seats can
add rows by PR without breaking the page.
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

# The three old reliable-grace duplicate/superseded website surfaces (the f027
# review copy + the menno420/superbot dashboard/botsite) — the ONLY rows that
# may carry the duplicate label (OQ-RAILWAY-PROJECT-SPLIT parking / RETIRE
# targets at consolidation).
DUPLICATE_IDS = {"review-dup-f027", "botsite-dup-superbot-app", "dashboard-dup-superbot-dashboard"}

# Verified 2026-07-12 seed URLs that must render as links.
SEED_URLS = [
    "https://review-production-f027.up.railway.app",
    "https://web-production-97636.up.railway.app",
    "https://control-plane-production-abb0.up.railway.app",
    "https://review-production-fc91.up.railway.app",
    "https://botsite-production-cfd7.up.railway.app",
    "https://dashboard-production-a91b.up.railway.app",
]


def _result(url, status, ok, error=""):
    return {"ok": ok, "status": status, "data": None, "error": error,
            "fetched_at": "12:00:00 UTC", "cached": False, "url": url}


def _probes_up(monkeypatch):
    async def fake_get(url, refresh=False, raw=False):
        return _result(url, 200, True)

    monkeypatch.setattr(github, "_get", fake_get)


def _probes_down(monkeypatch):
    async def fake_get(url, refresh=False, raw=False):
        return _result(url, 0, False, "ConnectError: probe refused (offline test)")

    monkeypatch.setattr(github, "_get", fake_get)


# --- the page -----------------------------------------------------------


def test_directory_renders_three_sections_with_seeds(monkeypatch):
    _probes_up(monkeypatch)
    with TestClient(app) as c:
        r = c.get("/directory")
    assert r.status_code == 200
    # the three sections
    assert ">our sites</h2>" in r.text
    assert ">external business surfaces</h2>" in r.text
    assert ">health</h2>" in r.text
    # our-sites seeds: every verified URL is a real link
    for url in SEED_URLS:
        assert f'href="{url}"' in r.text
    # URL-less real surfaces render honestly (no dead buttons, no invented URL)
    assert "superbot worker (the real bot)" in r.text
    assert "superbot live control panel" in r.text
    assert "no URL recorded" in r.text
    # project grouping (the corrected 2026-07-12 fleet inventory)
    for project in ("superbot-websites", "reliable-grace", "superbot-mineverse"):
        assert f"<h3>{project}</h3>" in r.text
    # external seeds: venture-lab x3 + Lumen Drift + games-web, each pending
    for title in ("venture-lab product 1", "venture-lab product 2",
                  "venture-lab product 3", "Lumen Drift", "games-web arcade"):
        assert title in r.text
    assert "lumen-drift-v1.3 GitHub Release needs one owner click" in r.text
    # the registry file is named on the page (single source of truth)
    assert "app/data/web_presence.json" in r.text


def test_duplicates_carry_the_duplicate_label(monkeypatch):
    _probes_up(monkeypatch)
    with TestClient(app) as c:
        r = c.get("/directory")
    assert r.status_code == 200
    # exactly the three reliable-grace copies badge as duplicates
    assert r.text.count('data-status="duplicate"') == len(DUPLICATE_IDS)
    assert "duplicate (pending consolidation)" in r.text
    assert "OQ-RAILWAY-PROJECT-SPLIT" in r.text


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
    # unprobeable rows keep their own honest states (not "down", not "live")
    assert 'data-health="pending"' in r.text
    assert 'data-health="no-url"' in r.text


def test_pending_publish_rows_are_never_probed(monkeypatch):
    calls = []

    async def fake_get(url, refresh=False, raw=False):
        calls.append(url)
        return _result(url, 200, True)

    monkeypatch.setattr(github, "_get", fake_get)
    with TestClient(app) as c:
        r = c.get("/directory")
    assert r.status_code == 200
    # only rows with a recorded URL and probe:true were fetched
    probeable = {s["url"] for s in REGISTRY["sites"]
                 if s.get("url") and s.get("probe")}
    assert set(calls) == probeable
    # every pending row shows "pending publish" (external seeds)
    external = [s for s in REGISTRY["sites"] if s["section"] == "external"]
    assert r.text.count('data-health="pending"') == len(external)


def test_degraded_is_not_live(monkeypatch):
    async def fake_get(url, refresh=False, raw=False):
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
    async def fake_get(url, refresh=False, raw=False):
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
                      "status", "notes"):
            assert s.get(field) is not None, f"{s.get('id')}: missing {field}"
        assert s["section"] in ("our-sites", "external")
        assert s["status"] in web_presence.KNOWN_STATUSES
        if s.get("probe"):
            assert s.get("url"), f"{s['id']}: probe:true requires a url"
        if s["section"] == "our-sites":
            assert s.get("project") in REGISTRY["projects"], (
                f"{s['id']}: our-sites rows carry a known project"
            )
    dup_rows = {s["id"]: s for s in sites if s["status"] == "duplicate"}
    assert set(dup_rows) == DUPLICATE_IDS
    for s in dup_rows.values():
        assert s.get("duplicate_of") in set(ids), (
            f"{s['id']}: duplicate_of must reference an existing row"
        )
    for s in sites:
        if s["status"] == "pending-publish":
            assert s.get("unblocked_by"), f"{s['id']}: pending rows say what unblocks them"


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
