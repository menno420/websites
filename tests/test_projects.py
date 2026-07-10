"""Offline unit tests for /projects (ORDER 009 increment 1): the fleet-manager
``projects/`` registry render — package cards with role-classified files +
meta.md deployed-state, and the honest degradation ladder (empty while the
registry is still landing upstream / not-configured / unavailable) — the
route always answers 200, never fabricates a package.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app import config, github, projects  # noqa: E402
from app.main import app  # noqa: E402


def _res(ok=True, status=200, data=None, error=""):
    return {"ok": ok, "status": status, "data": data, "error": error,
            "fetched_at": "", "cached": False, "url": ""}


# --------------------------------------------------------------------------- #
# helpers: role classification + state extraction
# --------------------------------------------------------------------------- #


def test_classify_role_heuristics():
    assert projects.classify_role("meta.md")[0] == "meta"
    assert projects.classify_role("project-instructions.md")[0] == "instructions"
    assert projects.classify_role("coordinator-prompt.md")[0] == "coordinator"
    assert projects.classify_role("setup-script.sh")[0] == "setup"
    assert projects.classify_role("failsafe.md")[0] == "failsafe"
    assert projects.classify_role("routine-prompt.md")[0] == "routine"
    assert projects.classify_role("notes.txt")[0] == "other"


def test_extract_state_tolerant_forms_and_honest_absence():
    assert projects.extract_state("deployed: live on Railway") == "live on Railway"
    assert projects.extract_state("**Status:** armed · v2") == "armed · v2"
    assert projects.extract_state("state = pasted 2026-07-10") == "pasted 2026-07-10"
    # no state-like line -> "" (rendered as an honest "state unknown")
    assert projects.extract_state("# meta\n\njust prose here") == ""
    assert projects.extract_state("") == ""


# --------------------------------------------------------------------------- #
# overview: degradation ladder
# --------------------------------------------------------------------------- #


def test_overview_empty_state_when_registry_not_landed(monkeypatch):
    """A 404 on projects/ is the EXPECTED launch state (the registry is being
    created upstream right now) — state 'empty', never an error banner."""

    async def fake_api(repo, subpath="", refresh=False):
        return _res(ok=False, status=404, data=None, error="Not Found")

    async def run():
        monkeypatch.setattr(github, "repo_api", fake_api)
        return await projects.overview()

    out = asyncio.run(run())
    assert out["state"] == "empty"
    assert "still landing" in out["reason"] and out["packages"] == []


def test_overview_not_configured_vs_unavailable(monkeypatch):
    async def fake_api(repo, subpath="", refresh=False):
        return _res(ok=False, status=403, data=None, error="rate limited")

    async def run():
        monkeypatch.setattr(github, "repo_api", fake_api)
        return await projects.overview()

    monkeypatch.setattr(config, "GITHUB_TOKEN", "")
    out = asyncio.run(run())
    assert out["state"] == "not-configured" and "GITHUB_TOKEN" in out["reason"]

    monkeypatch.setattr(config, "GITHUB_TOKEN", "tok")
    out = asyncio.run(run())
    assert out["state"] == "unavailable" and "rate limited" in out["reason"]


def test_overview_dir_exists_but_no_packages_is_empty(monkeypatch):
    async def fake_api(repo, subpath="", refresh=False):
        return _res(data=[])

    async def run():
        monkeypatch.setattr(github, "repo_api", fake_api)
        return await projects.overview()

    out = asyncio.run(run())
    assert out["state"] == "empty" and out["packages"] == []


# --------------------------------------------------------------------------- #
# overview: happy path
# --------------------------------------------------------------------------- #

_ROOT_LISTING = [
    {"type": "dir", "name": "websites", "path": "projects/websites"},
    {"type": "file", "name": "README.md", "path": "projects/README.md"},
]

_PKG_LISTING = [
    {"type": "file", "path": "projects/websites/meta.md"},
    {"type": "file", "path": "projects/websites/project-instructions.md"},
    {"type": "file", "path": "projects/websites/setup-script.sh"},
    {"type": "file", "path": "projects/websites/failsafe.md"},
]

_META_MD = "# websites package\n\ndeployed: pasted to console 2026-07-10\n"


def _happy_api(monkeypatch):
    async def fake_api(repo, subpath="", refresh=False):
        if subpath.endswith("/contents/projects"):
            return _res(data=_ROOT_LISTING)
        if subpath.endswith("/contents/projects/websites"):
            return _res(data=_PKG_LISTING)
        return _res(ok=False, status=404, data=None, error="nf")

    async def fake_fetch(repo, path, ref="main", refresh=False):
        if path == "projects/websites/meta.md":
            return _res(data=_META_MD)
        return _res(ok=False, status=404, data=None, error="nf")

    monkeypatch.setattr(github, "repo_api", fake_api)
    monkeypatch.setattr(github, "fetch_file", fake_fetch)


def test_overview_renders_package_cards(monkeypatch):
    async def run():
        _happy_api(monkeypatch)
        return await projects.overview()

    out = asyncio.run(run())
    assert out["state"] == "ok"
    assert [f["name"] for f in out["root_files"]] == ["README.md"]
    assert len(out["packages"]) == 1
    pkg = out["packages"][0]
    assert pkg["name"] == "websites" and pkg["error"] is None
    # role-first ordering: meta before instructions before setup/failsafe
    roles = [f["role"] for f in pkg["files"]]
    assert roles == ["meta", "instructions", "setup", "failsafe"]
    assert pkg["state"] == "pasted to console 2026-07-10"
    assert "<h1" in pkg["meta_html"]  # meta.md rendered as sanitized markdown
    assert pkg["github_url"].endswith("/fleet-manager/tree/main/projects/websites")


# --------------------------------------------------------------------------- #
# routes
# --------------------------------------------------------------------------- #


def test_projects_route_empty_state_is_200_with_banner(monkeypatch):
    async def fake_api(repo, subpath="", refresh=False):
        return _res(ok=False, status=404, data=None, error="Not Found")

    monkeypatch.setattr(github, "repo_api", fake_api)
    client = TestClient(app)
    r = client.get("/projects")
    assert r.status_code == 200
    assert "registry not landed yet" in r.text
    # nav carries the new link
    assert 'href="/projects"' in r.text


def test_projects_route_happy_renders_cards_and_json(monkeypatch):
    _happy_api(monkeypatch)
    client = TestClient(app)
    r = client.get("/projects")
    assert r.status_code == 200
    assert "websites" in r.text and "Custom Instructions" in r.text
    assert "pasted to console 2026-07-10" in r.text

    rj = client.get("/projects.json")
    assert rj.status_code == 200
    d = rj.json()
    assert d["state"] == "ok" and d["packages"][0]["name"] == "websites"
    # rendered HTML dropped from the JSON payload (HTML-view concern)
    assert "meta_html" not in d["packages"][0]
