"""Offline tests for ORDER 015: the consolidated prompt-render path.

Both prompt surfaces — the /prompts library (ORDER 014) and the
/projects/{package} dispatch screen (Owner Launch Console) — must render
fleet-manager registry artifacts through ONE shared implementation:
``app/prompt_artifacts.py`` (fetch + canonical artifact model over the
TTL-cached ``github`` layer) and ``templates/_prompt_artifact.html`` (the
copy-ready block; copy path stays the shared ``static/copycode.js``).

Pinned here: the shared model's contract, byte-identical body rendering on
both URLs for the same upstream file (happy, hostile-escaped, and failed
fetches), the dispatch screen's link to the canonical /prompts library, and
the single-source-of-truth delegation (``prompts``/``projects`` re-export
the shared helpers rather than keeping forks). Network-free:
``github.fetch_file`` / ``github.repo_api`` are monkeypatched.
"""

import asyncio
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app import github, projects, prompt_artifacts, prompts, roster  # noqa: E402
from app.main import app  # noqa: E402


def _res(ok=True, status=200, data=None, error="", cached=False):
    return {"ok": ok, "status": status, "data": data, "error": error,
            "fetched_at": "12:00:00 UTC", "cached": cached, "url": ""}


# --------------------------------------------------------------------------- #
# the shared artifact model
# --------------------------------------------------------------------------- #


def test_build_artifact_canonical_shape_ok_and_failure():
    ok = prompt_artifacts.build_artifact(
        "projects/websites/coordinator-prompt.md", "coordinator prompt",
        _res(data="<!-- v7 · 2026-07-12 · reg copy -->\nBODY\n", cached=True),
        seat="websites",
    )
    assert ok["ok"] and ok["text"].endswith("BODY\n")
    assert ok["seat"] == "websites" and ok["label"] == "coordinator prompt"
    assert ok["provenance"] == "v7 · 2026-07-12 · reg copy"
    assert ok["cached"] and ok["fetched_at"] == "12:00:00 UTC"
    assert ok["chars"] == len(ok["text"]) and ok["error"] == ""
    assert ok["github_url"].endswith(
        "/fleet-manager/blob/main/projects/websites/coordinator-prompt.md"
    )

    bad = prompt_artifacts.build_artifact(
        "projects/websites/failsafe-prompt.md", "failsafe prompt",
        _res(ok=False, status=404, data=None, error="Not Found"),
    )
    assert not bad["ok"] and bad["text"] is None and bad["seat"] is None
    assert bad["error"] == "Not Found" and bad["chars"] == 0
    # keys identical either way — one model, no per-surface variants
    assert set(ok) == set(bad)


def test_fetch_artifact_rides_the_shared_github_layer(monkeypatch):
    calls = []

    async def fake_fetch(repo, path, ref="main", refresh=False):
        calls.append((repo, path, ref, refresh))
        return _res(data="BODY\n")

    async def run():
        monkeypatch.setattr(github, "fetch_file", fake_fetch)
        return await prompt_artifacts.fetch_artifact(
            "docs/prompts/v3/session-ender.md", "session ender", refresh=True
        )

    art = asyncio.run(run())
    assert calls == [("fleet-manager", "docs/prompts/v3/session-ender.md",
                      "main", True)]
    assert art["ok"] and art["text"] == "BODY\n"


def test_single_source_of_truth_no_forked_helpers():
    """The library and dispatch modules DELEGATE to the shared path — the
    old per-module forks (extract_provenance, _blob_url, REPO) are gone."""
    assert prompts.extract_provenance is prompt_artifacts.extract_provenance
    assert prompts.REPO is prompt_artifacts.REPO
    assert projects.REPO is prompt_artifacts.REPO
    assert projects._blob_url is prompt_artifacts.blob_url


def test_seat_roster_single_source_and_order():
    """The seat roster lives ONCE (``app/roster.py``) — the /prompts library
    and the /projects dispatch order both derive from it, pinned to the
    owner's seats so the two surfaces can never drift."""
    assert prompts.SEATS is roster.SEATS
    assert projects._START_ORDER is roster.START_ORDER
    assert prompts.SEATS == (
        "fleet-manager",
        "venture-lab",
        "superbot-world",
        "superbot-2.0",
        "ideas-lab",
        "game-lab",
        "self-improvement",
        "websites",
        "curious-research",
    )
    assert prompts.SEATS == tuple(a[0] for a in projects._START_ORDER)
    assert [projects.start_rank(s) for s in prompts.SEATS] == list(
        range(len(prompts.SEATS))
    )


# --------------------------------------------------------------------------- #
# fixtures: one registry serving BOTH surfaces
# --------------------------------------------------------------------------- #

_HOSTILE = (
    "<!-- v7 · 2026-07-12 · hostile fixture -->\n"
    "<script>alert('pwned')</script>\n"
    "  indented   whitespace\tand tabs preserved\n"
)

_BODIES = {
    "projects/websites/coordinator-prompt.md":
        "<!-- v7 · 2026-07-12 · reg copy -->\nCOORD PROMPT BODY\n",
    "projects/websites/instructions.md": _HOSTILE,
    "projects/websites/failsafe-prompt.md": "failsafe body\n",
}


def _both_surfaces(monkeypatch, fail_paths=()):
    """fleet-manager fixture: /prompts fetches the pinned registry;
    /projects/websites lists + fetches the same three files."""

    async def fake_api(repo, subpath="", refresh=False):
        if subpath.endswith("/contents/projects"):
            return _res(data=[{"type": "dir", "name": "websites",
                               "path": "projects/websites"}])
        if subpath.endswith("/contents/projects/websites"):
            return _res(data=[
                {"type": "file", "path": p} for p in _BODIES
            ])
        return _res(ok=False, status=404, data=None, error="nf")

    async def fake_fetch(repo, path, ref="main", refresh=False):
        assert repo == "fleet-manager" and ref == "main"
        if path in fail_paths:
            return _res(ok=False, status=502, data=None, error="bad gateway")
        if path in _BODIES:
            return _res(data=_BODIES[path])
        return _res(ok=False, status=404, data=None, error="Not Found")

    monkeypatch.setattr(github, "repo_api", fake_api)
    monkeypatch.setattr(github, "fetch_file", fake_fetch)


def _pre_blocks(html):
    return re.findall(r"<pre>(.*?)</pre>", html, flags=re.DOTALL)


# --------------------------------------------------------------------------- #
# both URLs render the SAME content through the shared path
# --------------------------------------------------------------------------- #


def test_both_surfaces_render_identical_bodies(monkeypatch):
    _both_surfaces(monkeypatch)
    client = TestClient(app)
    lib = client.get("/prompts")
    disp = client.get("/projects/websites")
    assert lib.status_code == 200 and disp.status_code == 200

    lib_pre = set(_pre_blocks(lib.text))
    disp_pre = set(_pre_blocks(disp.text))
    # every dispatch-rendered body appears byte-identically on the library
    # page (escaped through the same autoescaped partial)
    assert disp_pre and disp_pre <= lib_pre
    assert any("COORD PROMPT BODY" in b for b in disp_pre)
    # hostile content escaped IDENTICALLY on both — never marked safe
    for r in (lib, disp):
        assert "<script>alert" not in r.text
        assert "&lt;script&gt;alert(&#39;pwned&#39;)&lt;/script&gt;" in r.text
        assert "  indented   whitespace\tand tabs preserved" in r.text
    # shared-block furniture on BOTH surfaces: provenance + freshness + copy
    for r in (lib, disp):
        assert "v7 · 2026-07-12 · reg copy" in r.text
        assert "live fetch" in r.text
        assert 'src="/static/copycode.js"' in r.text


def test_failed_fetch_degrades_identically_on_both(monkeypatch):
    _both_surfaces(
        monkeypatch, fail_paths=("projects/websites/coordinator-prompt.md",)
    )
    client = TestClient(app)
    for url in ("/prompts", "/projects/websites"):
        r = client.get(url)
        assert r.status_code == 200
        # the shared partial's honest error cell, verbatim on both
        assert "bad gateway" in r.text
        assert ("nothing shown rather than a stale fabrication"
                in " ".join(r.text.split()))
        assert "COORD PROMPT BODY" not in r.text  # never fabricated
        # siblings still render
        assert "failsafe body" in r.text


def test_dispatch_screen_links_to_canonical_prompt_library(monkeypatch):
    """ORDER 015: /prompts is the canonical page for FINDING prompts — the
    dispatch screen links to it."""
    _both_surfaces(monkeypatch)
    r = TestClient(app).get("/projects/websites")
    assert r.status_code == 200
    assert 'href="/prompts"' in r.text
