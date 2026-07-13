"""Offline unit tests for /projects (ORDER 009 increment 1): the fleet-manager
``projects/`` registry render — package cards with role-classified files +
meta.md deployed-state, and the honest degradation ladder (empty while the
registry is still landing upstream / not-configured / unavailable) — the
route always answers 200, never fabricates a package.

Owner Launch Console additions (single-screen dispatch, 2026-07-12): the
seats-first index split + owner start order, the /projects/{package}
dispatch screen (full role-file content, copy-ready; meta fields honest
about absence), registry-validated package names (unknown / traversal
shapes → 404), and the same degradation ladder on the detail page.
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


def test_overview_non_list_2xx_payload_is_unavailable(monkeypatch):
    """An ok envelope whose data is not a directory listing (non-JSON 2xx)
    renders as 'unavailable' with the shared honest shape reason — never as
    an empty registry (github.classify_listing)."""

    async def fake_api(repo, subpath="", refresh=False):
        return _res(ok=True, status=200, data="<!doctype html>oops")

    async def run():
        monkeypatch.setattr(github, "repo_api", fake_api)
        return await projects.overview()

    monkeypatch.setattr(config, "GITHUB_TOKEN", "tok")
    out = asyncio.run(run())
    assert out["state"] == "unavailable"
    assert out["reason"] == "unexpected listing payload (HTTP 200)"
    assert out["packages"] == []


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
    # category nav carries the page's group (projects ∈ console)
    assert 'href="/console"' in r.text


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


# --------------------------------------------------------------------------- #
# dispatch console: stub detection + owner start order
# --------------------------------------------------------------------------- #


def test_start_rank_owner_order_and_aliases():
    order = [
        "fleet-manager", "venture-lab", "superbot-world", "superbot-2.0",
        "ideas-lab", "game-lab", "self-improvement", "websites",
    ]
    ranks = [projects.start_rank(n) for n in order]
    assert ranks == sorted(ranks) and len(set(ranks)) == len(ranks)
    # aliases share the slot; normalization tolerates case and underscores
    assert projects.start_rank("project-manager") == projects.start_rank(
        "fleet-manager"
    )
    assert projects.start_rank("superbot-next") == projects.start_rank(
        "superbot-2.0"
    )
    assert projects.start_rank("Self_Improvement") == projects.start_rank(
        "self-improvement"
    )
    # unmatched names rank after every matched one
    assert projects.start_rank("zeta-experiment") > projects.start_rank("websites")


def test_is_stub_tolerant_and_fail_active():
    # state line spellings
    assert projects.is_stub("retired", "")
    assert projects.is_stub("merged into superbot-next", "")
    assert projects.is_stub("stub — see superbot-2.0", "")
    # body spellings (unambiguous words only)
    assert projects.is_stub("", "# old\n\nThis package is retired.\n")
    assert projects.is_stub("", "# old\n\nmerged into superbot-next\n")
    # fail-ACTIVE: live states, prose about PRs merging, absent meta
    assert not projects.is_stub("live on Railway", "")
    assert not projects.is_stub("", "# pkg\n\nPR #12 merged, all green.\n")
    assert not projects.is_stub("", "")


_MULTI_ROOT = [
    {"type": "dir", "name": n, "path": f"projects/{n}"}
    for n in ["old-lab", "websites", "zeta-experiment", "superbot-2.0",
              "venture-lab"]
]

_MULTI_METAS = {
    "projects/old-lab/meta.md": "# old-lab\n\nstatus: retired — merged into superbot-next\n",
    "projects/websites/meta.md": "deployed: live\n",
    "projects/superbot-2.0/meta.md": "state: pasted\n",
    "projects/venture-lab/meta.md": "# venture-lab\n\nprose only\n",
    "projects/zeta-experiment/meta.md": "# zeta\n\nprose only\n",
}


def _multi_api(monkeypatch):
    async def fake_api(repo, subpath="", refresh=False):
        if subpath.endswith("/contents/projects"):
            return _res(data=_MULTI_ROOT)
        for d in _MULTI_ROOT:
            if subpath.endswith(f"/contents/{d['path']}"):
                return _res(data=[
                    {"type": "file", "path": f"{d['path']}/meta.md"},
                ])
        return _res(ok=False, status=404, data=None, error="nf")

    async def fake_fetch(repo, path, ref="main", refresh=False):
        if path in _MULTI_METAS:
            return _res(data=_MULTI_METAS[path])
        return _res(ok=False, status=404, data=None, error="nf")

    monkeypatch.setattr(github, "repo_api", fake_api)
    monkeypatch.setattr(github, "fetch_file", fake_fetch)


def test_overview_seats_first_in_start_order_stubs_last(monkeypatch):
    async def run():
        _multi_api(monkeypatch)
        return await projects.overview()

    out = asyncio.run(run())
    assert out["state"] == "ok"
    names = [p["name"] for p in out["packages"]]
    # owner start order for matched seats, unmatched after (alphabetical),
    # stubs dead last
    assert names == ["venture-lab", "superbot-2.0", "websites",
                     "zeta-experiment", "old-lab"]
    stubs = [p["name"] for p in out["packages"] if p["stub"]]
    assert stubs == ["old-lab"]
    assert out["packages"][0]["detail_url"] == "/projects/venture-lab"


def test_projects_index_splits_seats_and_collapses_stubs(monkeypatch):
    _multi_api(monkeypatch)
    client = TestClient(app)
    r = client.get("/projects")
    assert r.status_code == 200
    # seat cards link to the dispatch screen
    assert 'href="/projects/websites"' in r.text
    assert "open dispatch" in r.text
    # stubs collapsed under a <details> section, never hidden entirely
    assert "<details>" in r.text
    assert "Retired / merged stubs (1)" in r.text
    assert 'href="/projects/old-lab"' in r.text
    # seats render before the stub section
    assert r.text.index("venture-lab") < r.text.index("Retired / merged stubs")


# --------------------------------------------------------------------------- #
# dispatch console: seat role-coverage chips (backlog bullet, 2026-07-12)
# --------------------------------------------------------------------------- #


def test_role_coverage_derived_from_listing():
    """Coverage comes from the role-classified listing alone — one chip per
    dispatch-critical role (instructions / coordinator / failsafe), in that
    order, present-or-missing."""
    files = [
        {"role": "meta"}, {"role": "instructions"}, {"role": "failsafe"},
        {"role": "other"},
    ]
    cov = projects.role_coverage(files)
    assert [c["role"] for c in cov] == ["instructions", "coordinator",
                                        "failsafe"]
    assert [c["present"] for c in cov] == [True, False, True]
    assert cov[0]["label"] == "Custom Instructions"
    # empty listing -> every dispatch role honestly absent
    assert all(not c["present"] for c in projects.role_coverage([]))


def test_overview_coverage_and_dispatch_ready_flag(monkeypatch):
    """_happy_api's package has instructions + failsafe but NO coordinator:
    the chip row marks the gap and the seat is not dispatch-ready."""

    async def run():
        _happy_api(monkeypatch)
        return await projects.overview()

    out = asyncio.run(run())
    pkg = out["packages"][0]
    assert {c["role"]: c["present"] for c in pkg["coverage"]} == {
        "instructions": True, "coordinator": False, "failsafe": True,
    }
    assert pkg["dispatch_ready"] is False


def test_coverage_unknown_when_package_unlistable(monkeypatch):
    """A package whose listing failed shows NO chips — coverage is honest
    unknown ([] / None), never a fabricated ✗ row."""

    async def fake_api(repo, subpath="", refresh=False):
        if subpath.endswith("/contents/projects"):
            return _res(data=_ROOT_LISTING)
        return _res(ok=False, status=502, data=None, error="bad gateway")

    async def run():
        monkeypatch.setattr(github, "repo_api", fake_api)
        return await projects.overview()

    out = asyncio.run(run())
    pkg = out["packages"][0]
    assert pkg["error"] and pkg["coverage"] == []
    assert pkg["dispatch_ready"] is None

    monkeypatch.setattr(github, "repo_api", fake_api)
    r = TestClient(app).get("/projects")
    assert r.status_code == 200
    assert "✗" not in r.text  # no chip row invented for the errored card


def test_projects_index_renders_coverage_chips_incomplete_seat(monkeypatch):
    _happy_api(monkeypatch)
    r = TestClient(app).get("/projects")
    assert r.status_code == 200
    assert "instructions ✓" in r.text
    assert "coordinator ✗" in r.text
    assert "failsafe ✓" in r.text
    assert "NOT dispatch-ready" in r.text
    # index summary counts the launchable seats
    assert "0 of 1" in r.text and "dispatch-ready" in r.text


def test_projects_index_renders_coverage_chips_ready_seat(monkeypatch):
    """A package carrying all three dispatch-critical roles reads
    dispatch-ready — all chips ✓ (reuses the full detail listing)."""

    async def fake_api(repo, subpath="", refresh=False):
        if subpath.endswith("/contents/projects"):
            return _res(data=[
                {"type": "dir", "name": "websites",
                 "path": "projects/websites"},
            ])
        if subpath.endswith("/contents/projects/websites"):
            return _res(data=_DETAIL_LISTING)
        return _res(ok=False, status=404, data=None, error="nf")

    async def fake_fetch(repo, path, ref="main", refresh=False):
        if path in _DETAIL_TEXTS:
            return _res(data=_DETAIL_TEXTS[path])
        return _res(ok=False, status=404, data=None, error="nf")

    monkeypatch.setattr(github, "repo_api", fake_api)
    monkeypatch.setattr(github, "fetch_file", fake_fetch)
    r = TestClient(app).get("/projects")
    assert r.status_code == 200
    assert "instructions ✓" in r.text
    assert "coordinator ✓" in r.text
    assert "failsafe ✓" in r.text
    assert "NOT dispatch-ready" not in r.text and "✗" not in r.text
    assert "1 of 1" in r.text and "dispatch-ready" in r.text

    # /projects.json carries the coverage structures (contract pinned in
    # tests/test_json_contracts.py)
    monkeypatch.setattr(github, "repo_api", fake_api)
    monkeypatch.setattr(github, "fetch_file", fake_fetch)
    d = TestClient(app).get("/projects.json").json()
    pkg = d["packages"][0]
    assert pkg["dispatch_ready"] is True
    assert all(c["present"] for c in pkg["coverage"])


# --------------------------------------------------------------------------- #
# dispatch console: /projects/{package} detail
# --------------------------------------------------------------------------- #

_DETAIL_LISTING = [
    {"type": "file", "path": "projects/websites/meta.md"},
    {"type": "file", "path": "projects/websites/project-instructions.md"},
    {"type": "file", "path": "projects/websites/coordinator-prompt.md"},
    {"type": "file", "path": "projects/websites/setup-script.sh"},
    {"type": "file", "path": "projects/websites/failsafe.md"},
    {"type": "file", "path": "projects/websites/routine-prompt.md"},
    {"type": "file", "path": "projects/websites/notes.txt"},
]

_DETAIL_META = (
    "# websites package\n\n"
    "**Status:** deployed 2026-07-11\n"
    "environment: websites-prod\n"
    "Project: https://claude.ai/project/abc-123\n"
)

_DETAIL_TEXTS = {
    "projects/websites/meta.md": _DETAIL_META,
    "projects/websites/project-instructions.md": "FULL CUSTOM INSTRUCTIONS TEXT",
    "projects/websites/coordinator-prompt.md": "FULL COORDINATOR PROMPT TEXT",
    "projects/websites/setup-script.sh": "#!/bin/sh\necho setup",
    "projects/websites/failsafe.md": "failsafe cron: armed hourly",
    "projects/websites/routine-prompt.md": "wake routine prompt",
}


def _detail_api(monkeypatch, fail_paths=()):
    async def fake_api(repo, subpath="", refresh=False):
        if subpath.endswith("/contents/projects"):
            return _res(data=[
                {"type": "dir", "name": "websites", "path": "projects/websites"},
            ])
        if subpath.endswith("/contents/projects/websites"):
            return _res(data=_DETAIL_LISTING)
        return _res(ok=False, status=404, data=None, error="nf")

    async def fake_fetch(repo, path, ref="main", refresh=False):
        if path in fail_paths:
            return _res(ok=False, status=502, data=None, error="bad gateway")
        if path in _DETAIL_TEXTS:
            return _res(data=_DETAIL_TEXTS[path])
        return _res(ok=False, status=404, data=None, error="nf")

    monkeypatch.setattr(github, "repo_api", fake_api)
    monkeypatch.setattr(github, "fetch_file", fake_fetch)


def test_detail_happy_full_content_and_meta_fields(monkeypatch):
    async def run():
        _detail_api(monkeypatch)
        return await projects.detail("websites")

    out = asyncio.run(run())
    assert out["state"] == "ok"
    pkg = out["package"]
    by_role = {f["role"]: f for f in pkg["files"]}
    # every recognized role file carries its FULL raw content
    for role in ("meta", "instructions", "coordinator", "setup", "failsafe",
                 "routine"):
        assert by_role[role]["text"] == _DETAIL_TEXTS[by_role[role]["path"]]
        assert by_role[role]["fetch_error"] is None
    # "other" files stay link-only (no content fetch)
    assert by_role["other"]["name"] == "notes.txt"
    assert by_role["other"]["text"] is None
    # meta fields extracted best-effort, never invented
    assert pkg["state"] == "deployed 2026-07-11"
    assert out["env"] == "websites-prod"
    assert out["project_url"] == "https://claude.ai/project/abc-123"
    assert out["failsafe"] is not None
    assert out["failsafe"]["role"] == "failsafe"


def test_detail_meta_fields_absent_render_unknown(monkeypatch):
    """No env / Project URL / state line in meta.md -> honest empties."""

    async def fake_api(repo, subpath="", refresh=False):
        if subpath.endswith("/contents/projects"):
            return _res(data=[
                {"type": "dir", "name": "websites", "path": "projects/websites"},
            ])
        if subpath.endswith("/contents/projects/websites"):
            return _res(data=[
                {"type": "file", "path": "projects/websites/meta.md"},
            ])
        return _res(ok=False, status=404, data=None, error="nf")

    async def fake_fetch(repo, path, ref="main", refresh=False):
        return _res(data="# bare meta\n\nprose only\n")

    async def run():
        monkeypatch.setattr(github, "repo_api", fake_api)
        monkeypatch.setattr(github, "fetch_file", fake_fetch)
        return await projects.detail("websites")

    out = asyncio.run(run())
    assert out["state"] == "ok"
    assert out["env"] == "" and out["project_url"] == ""
    assert out["package"]["state"] == ""
    assert out["failsafe"] is None

    client = TestClient(app)
    r = client.get("/projects/websites")
    assert r.status_code == 200
    assert "unknown" in r.text and "none recorded" in r.text
    assert "no failsafe file recognized" in r.text


def test_detail_rejects_unknown_and_traversal_names(monkeypatch):
    async def run(name):
        _detail_api(monkeypatch)
        return await projects.detail(name)

    assert asyncio.run(run("not-in-registry"))["state"] == "not-found"
    assert asyncio.run(run("../secrets"))["state"] == "not-found"
    assert asyncio.run(run(".."))["state"] == "not-found"
    assert asyncio.run(run(""))["state"] == "not-found"

    _detail_api(monkeypatch)
    client = TestClient(app)
    r = client.get("/projects/not-in-registry")
    assert r.status_code == 404
    assert "unknown package" in r.text


def test_detail_route_renders_copy_ready_dispatch_screen(monkeypatch):
    _detail_api(monkeypatch)
    client = TestClient(app)
    r = client.get("/projects/websites")
    assert r.status_code == 200
    # full role-file content in <pre> blocks, copy button JS attached
    assert "<pre>" in r.text
    assert "FULL CUSTOM INSTRUCTIONS TEXT" in r.text
    assert "FULL COORDINATOR PROMPT TEXT" in r.text
    assert 'src="/static/copycode.js"' in r.text
    # dispatch checklist with the failsafe file linked
    assert "dispatch checklist" in r.text
    assert "Custom Instructions" in r.text
    assert "failsafe cron is armed" in r.text
    assert 'href="#file-' in r.text
    # meta fields surfaced
    assert "deployed 2026-07-11" in r.text
    assert "websites-prod" in r.text
    assert 'href="https://claude.ai/project/abc-123"' in r.text
    # "other" files listed honestly, link-only
    assert "notes.txt" in r.text


def test_detail_per_file_fetch_error_degrades_per_cell(monkeypatch):
    _detail_api(
        monkeypatch, fail_paths=("projects/websites/coordinator-prompt.md",)
    )
    client = TestClient(app)
    r = client.get("/projects/websites")
    assert r.status_code == 200
    assert "bad gateway" in r.text  # the failed cell says why
    assert "FULL CUSTOM INSTRUCTIONS TEXT" in r.text  # siblings still render
    assert "FULL COORDINATOR PROMPT TEXT" not in r.text  # never fabricated


def test_detail_degraded_registry_states(monkeypatch):
    async def fake_api(repo, subpath="", refresh=False):
        return _res(ok=False, status=403, data=None, error="rate limited")

    monkeypatch.setattr(github, "repo_api", fake_api)
    client = TestClient(app)

    monkeypatch.setattr(config, "GITHUB_TOKEN", "")
    r = client.get("/projects/websites")
    assert r.status_code == 200
    assert "not configured" in r.text and "GITHUB_TOKEN" in r.text

    monkeypatch.setattr(config, "GITHUB_TOKEN", "tok")
    r = client.get("/projects/websites")
    assert r.status_code == 200
    assert "unavailable" in r.text and "rate limited" in r.text


def test_detail_empty_registry_is_banner_not_404(monkeypatch):
    async def fake_api(repo, subpath="", refresh=False):
        return _res(ok=False, status=404, data=None, error="Not Found")

    monkeypatch.setattr(github, "repo_api", fake_api)
    client = TestClient(app)
    r = client.get("/projects/websites")
    assert r.status_code == 200
    assert "registry not landed yet" in r.text
