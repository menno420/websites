"""The repository catalogue is the one owner-facing estate model.

Operational lane and dispatch views remain available under names that describe
their actual jobs.  The old HTML routes are reversible redirects; their JSON
contracts remain separate compatibility surfaces.
"""

from pathlib import Path

from fastapi.testclient import TestClient

from app import nav
from app.main import app


def test_legacy_estate_html_routes_repoint_to_repos():
    with TestClient(app) as client:
        for path in ("/fleet", "/projects", "/freshness"):
            response = client.get(path, follow_redirects=False)
            assert response.status_code == 307, path
            assert response.headers["location"] == "/repos"
            assert "fleet heartbeat" not in response.text
            assert "Project-package registry" not in response.text


def test_legacy_dispatch_deep_link_is_reversible():
    with TestClient(app) as client:
        response = client.get("/projects/websites", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/dispatch/websites"


def test_nav_has_one_estate_home_and_names_operational_views():
    hrefs = set(nav.all_hrefs())
    assert "/repos" in hrefs
    assert {"/fleet", "/projects", "/freshness"}.isdisjoint(hrefs)
    assert {"/lanes", "/dispatch"} <= hrefs
    assert nav.item("repos")["href"] == "/repos"


def test_owner_facing_templates_do_not_link_legacy_html_routes():
    templates = Path(__file__).parents[1] / "app" / "templates"
    bad: list[str] = []
    for path in templates.glob("*.html"):
        text = path.read_text(encoding="utf-8")
        for href in ('href="/fleet"', 'href="/projects"', 'href="/freshness"'):
            if href in text:
                bad.append(f"{path.name}: {href}")
    assert not bad, "legacy owner links remain: " + ", ".join(bad)

