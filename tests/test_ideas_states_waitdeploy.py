"""Offline unit tests for slice 13: the /ideas lifecycle-state surfacing
(front-matter extraction, per-repo counts, ?state= filter that narrows the
list but never the truth) and the wait_deploy sha-convergence helpers.
"""

import importlib.util
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app import github, ideas  # noqa: E402
from app.main import app  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "wait_deploy", Path(__file__).resolve().parents[1] / "scripts" / "wait_deploy.py"
)
wait_deploy = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(wait_deploy)


# --------------------------------------------------------------------------- #
# extract_state
# --------------------------------------------------------------------------- #


def test_extract_state_from_frontmatter_only():
    fm = "---\nstate: captured\norigin: x\n---\n\n# t\n\nbody\n"
    assert ideas.extract_state(fm) == "captured"
    # a body sentence mentioning state: must NOT classify the idea
    body_only = "# t\n\nstate: built is mentioned here\n"
    assert ideas.extract_state(body_only) == ""
    # unknown token -> unstated, never guessed into a stage
    weird = "---\nstate: percolating\n---\n\n# t\n"
    assert ideas.extract_state(weird) == ""
    assert ideas.extract_state("") == ""


# --------------------------------------------------------------------------- #
# repo_ideas counts + overview filter
# --------------------------------------------------------------------------- #

_FILES = [
    {"type": "file", "name": f"idea-{n}.md", "path": f"docs/ideas/idea-{n}.md",
     "html_url": ""}
    for n in ("a", "b", "c")
]
_CONTENT = {
    "docs/ideas/idea-a.md": "---\nstate: captured\n---\n\n# A\n\none a\n",
    "docs/ideas/idea-b.md": "---\nstate: built\n---\n\n# B\n\none b\n",
    "docs/ideas/idea-c.md": "# C\n\nno front-matter here\n",
}


def _res(ok=True, status=200, data=None, error=""):
    return {"ok": ok, "status": status, "data": data, "error": error,
            "fetched_at": "", "cached": False, "url": ""}


def _mock(monkeypatch):
    async def fake_api(repo, subpath="", refresh=False):
        if subpath.endswith("/contents/docs/ideas") and repo == "websites":
            return _res(data=_FILES)
        return _res(ok=False, status=404, data=None, error="nf")

    async def fake_fetch(repo, path, ref="main", refresh=False):
        if path in _CONTENT:
            return _res(data=_CONTENT[path])
        return _res(ok=False, status=404, data=None, error="nf")

    monkeypatch.setattr(github, "repo_api", fake_api)
    monkeypatch.setattr(github, "fetch_file", fake_fetch)


def test_repo_state_counts_and_badges(monkeypatch):
    import asyncio

    _mock(monkeypatch)
    repos = asyncio.run(ideas.overview())
    r = next(x for x in repos if x["repo"] == "websites")
    assert r["state_counts"] == {"captured": 1, "built": 1, "unstated": 1}
    states = {i["name"]: i["state"] for i in r["ideas"]}
    assert states == {"idea-a.md": "captured", "idea-b.md": "built",
                      "idea-c.md": ""}


def test_overview_state_filter_narrows_list_not_counts(monkeypatch):
    import asyncio

    _mock(monkeypatch)
    repos = asyncio.run(ideas.overview(state="built"))
    r = next(x for x in repos if x["repo"] == "websites")
    assert [i["name"] for i in r["ideas"]] == ["idea-b.md"]
    assert r["state_counts"]["captured"] == 1  # counts stay full
    # unstated is filterable too
    repos = asyncio.run(ideas.overview(state="unstated"))
    r = next(x for x in repos if x["repo"] == "websites")
    assert [i["name"] for i in r["ideas"]] == ["idea-c.md"]
    # unknown filter: flagged, nothing dropped
    repos = asyncio.run(ideas.overview(state="bogus"))
    r = next(x for x in repos if x["repo"] == "websites")
    assert r["state_filter_known"] is False and len(r["ideas"]) == 3


def test_ideas_page_renders_chips_and_badges(monkeypatch):
    _mock(monkeypatch)
    client = TestClient(app)
    r = client.get("/ideas")
    assert r.status_code == 200
    assert "1 captured" in r.text and "1 built" in r.text and "1 unstated" in r.text
    assert 'href="/ideas?state=built"' in r.text

    r = client.get("/ideas?state=bogus")
    assert r.status_code == 200 and "unknown state" in r.text


# --------------------------------------------------------------------------- #
# wait_deploy helpers
# --------------------------------------------------------------------------- #


def test_converged_prefix_tolerant_never_empty():
    full = "a" * 40
    assert wait_deploy.converged(full, full) is True
    assert wait_deploy.converged(full, full[:9]) is True   # short want
    assert wait_deploy.converged(full[:9], full) is True   # short deployed
    assert wait_deploy.converged(full, "b" * 9) is False
    assert wait_deploy.converged("", full) is False
    assert wait_deploy.converged(full, "abc") is False     # below MIN_SHA
