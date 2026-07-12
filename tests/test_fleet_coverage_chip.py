"""Offline tests for the /fleet coverage-chip rollup (backlog bullet,
2026-07-12): ``projects.coverage_rollup`` reduces the EXISTING per-seat
instructions/coordinator/failsafe coverage (``projects.role_coverage``, the
same TTL-cached registry data /projects renders — zero new network surface)
to one "packages incomplete: N" cell on the `/fleet` monitoring surface.

Honesty ladder pinned here: complete → green; N incomplete → amber with the
seats NAMED; registry unreadable/empty or a seat's own listing failed →
unknown, never a fabricated zero/green. `/fleet.json` carries the same
rollup (key set pinned in tests/test_fleet_json_contract.py).
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app import github, projects  # noqa: E402
from app.main import app  # noqa: E402


def _res(ok=True, status=200, data=None, error=""):
    return {"ok": ok, "status": status, "data": data, "error": error,
            "fetched_at": "", "cached": False, "url": ""}


def _dir(name):
    return {"type": "dir", "name": name, "path": f"projects/{name}"}


def _files(*names):
    return [{"type": "file", "path": p} for p in names]


_COMPLETE = _files(
    "projects/{n}/project-instructions.md",
    "projects/{n}/coordinator-prompt.md",
    "projects/{n}/failsafe.md",
)


def _complete_listing(name):
    return [{"type": "file", "path": f["path"].format(n=name)}
            for f in _COMPLETE]


def _incomplete_listing(name):
    # instructions + failsafe, NO coordinator
    return _files(
        f"projects/{name}/project-instructions.md",
        f"projects/{name}/failsafe.md",
    )


def _mock_api(monkeypatch, listings, default_status=404, default_error="nf"):
    """github.repo_api fake dispatching on the exact subpath; everything
    else (fleet's /commits, /pulls, unknown paths) 404s honestly."""

    async def fake_api(repo, subpath="", refresh=False):
        if subpath in listings:
            return listings[subpath]
        return _res(ok=False, status=default_status, data=None,
                    error=default_error)

    monkeypatch.setattr(github, "repo_api", fake_api)


def _mock_fetch_404(monkeypatch):
    async def fake_fetch(repo, path, ref="main", refresh=False):
        return _res(ok=False, status=404, data=None, error="nf")

    monkeypatch.setattr(github, "fetch_file", fake_fetch)


# --------------------------------------------------------------------------- #
# coverage_rollup — the reduction itself
# --------------------------------------------------------------------------- #


def test_rollup_full_coverage(monkeypatch):
    _mock_api(monkeypatch, {
        "/contents/projects": _res(data=[_dir("alpha"), _dir("beta")]),
        "/contents/projects/alpha": _res(data=_complete_listing("alpha")),
        "/contents/projects/beta": _res(data=_complete_listing("beta")),
    })
    _mock_fetch_404(monkeypatch)
    out = asyncio.run(projects.coverage_rollup())
    assert out["state"] == "ok"
    assert out["seats"] == 2 and out["complete"] == 2
    assert out["incomplete"] == 0 and out["incomplete_names"] == []
    assert out["unlistable"] == 0


def test_rollup_partial_names_the_incomplete_seats(monkeypatch):
    _mock_api(monkeypatch, {
        "/contents/projects": _res(data=[_dir("alpha"), _dir("beta")]),
        "/contents/projects/alpha": _res(data=_complete_listing("alpha")),
        "/contents/projects/beta": _res(data=_incomplete_listing("beta")),
    })
    _mock_fetch_404(monkeypatch)
    out = asyncio.run(projects.coverage_rollup())
    assert out["state"] == "ok"
    assert out["incomplete"] == 1 and out["incomplete_names"] == ["beta"]
    assert out["complete"] == 1 and out["seats"] == 2


def test_rollup_registry_missing_is_unknown_not_zero(monkeypatch):
    """projects/ 404s (registry not landed) → overview state 'empty' →
    rollup UNKNOWN with the reason — never 'incomplete: 0'."""
    _mock_api(monkeypatch, {})  # everything 404
    _mock_fetch_404(monkeypatch)
    out = asyncio.run(projects.coverage_rollup())
    assert out["state"] == "unknown" and out["reason"]
    assert out["incomplete"] == 0 and out["seats"] == 0


def test_rollup_registry_unavailable_is_unknown(monkeypatch):
    _mock_api(monkeypatch, {}, default_status=502,
              default_error="bad gateway")
    _mock_fetch_404(monkeypatch)
    out = asyncio.run(projects.coverage_rollup())
    assert out["state"] == "unknown"
    assert "bad gateway" in out["reason"]


def test_rollup_unlistable_seat_is_never_complete_or_incomplete(monkeypatch):
    """A seat whose own listing failed counts as unlistable — coverage
    unknown for it, so the green 'complete' claim is impossible."""
    _mock_api(monkeypatch, {
        "/contents/projects": _res(data=[_dir("alpha"), _dir("beta")]),
        "/contents/projects/alpha": _res(data=_complete_listing("alpha")),
        # beta's listing 404s via the default
    })
    _mock_fetch_404(monkeypatch)
    out = asyncio.run(projects.coverage_rollup())
    assert out["state"] == "ok"
    assert out["complete"] == 1 and out["incomplete"] == 0
    assert out["unlistable"] == 1 and out["unlistable_names"] == ["beta"]


def test_rollup_excludes_retired_stubs(monkeypatch):
    """Stubs are outside the rollup population (same as the /projects
    'N of M dispatch-ready' summary); a registry of ONLY stubs has no
    seats to check → honest unknown."""
    _mock_api(monkeypatch, {
        "/contents/projects": _res(data=[_dir("old-lab")]),
        "/contents/projects/old-lab": _res(
            data=_files("projects/old-lab/meta.md")),
    })

    async def fake_fetch(repo, path, ref="main", refresh=False):
        if path == "projects/old-lab/meta.md":
            return _res(data="# old-lab\n\nstate: retired — merged into x\n")
        return _res(ok=False, status=404, data=None, error="nf")

    monkeypatch.setattr(github, "fetch_file", fake_fetch)
    out = asyncio.run(projects.coverage_rollup())
    assert out["state"] == "unknown"
    assert "no active seat" in out["reason"]


# --------------------------------------------------------------------------- #
# /fleet page — the rendered chip states
# --------------------------------------------------------------------------- #


def test_fleet_renders_amber_incomplete_chip_with_names(monkeypatch):
    _mock_api(monkeypatch, {
        "/contents/projects": _res(data=[_dir("alpha"), _dir("beta")]),
        "/contents/projects/alpha": _res(data=_complete_listing("alpha")),
        "/contents/projects/beta": _res(data=_incomplete_listing("beta")),
    })
    _mock_fetch_404(monkeypatch)
    r = TestClient(app).get("/fleet")
    assert r.status_code == 200
    assert "packages incomplete: 1" in r.text
    assert "<code>beta</code>" in r.text  # the incomplete seat is NAMED
    assert "coverage: complete" not in r.text


def test_fleet_renders_green_complete_chip(monkeypatch):
    _mock_api(monkeypatch, {
        "/contents/projects": _res(data=[_dir("alpha"), _dir("beta")]),
        "/contents/projects/alpha": _res(data=_complete_listing("alpha")),
        "/contents/projects/beta": _res(data=_complete_listing("beta")),
    })
    _mock_fetch_404(monkeypatch)
    r = TestClient(app).get("/fleet")
    assert r.status_code == 200
    assert "coverage: complete (2 seats)" in r.text
    assert "packages incomplete" not in r.text


def test_fleet_renders_unknown_chip_when_registry_unreadable(monkeypatch):
    """No coverage data → an honest unknown chip — never a fabricated
    'packages incomplete: 0' and never a green."""
    _mock_api(monkeypatch, {}, default_status=502, default_error="bad gateway")
    _mock_fetch_404(monkeypatch)
    r = TestClient(app).get("/fleet")
    assert r.status_code == 200
    assert "coverage unknown" in r.text
    assert "packages incomplete" not in r.text
    assert "coverage: complete" not in r.text


def test_fleet_renders_unknown_chip_for_unlistable_seat(monkeypatch):
    """All listed seats complete but one seat unlistable → NOT green:
    the chip says coverage is unknown for that seat."""
    _mock_api(monkeypatch, {
        "/contents/projects": _res(data=[_dir("alpha"), _dir("beta")]),
        "/contents/projects/alpha": _res(data=_complete_listing("alpha")),
    })
    _mock_fetch_404(monkeypatch)
    r = TestClient(app).get("/fleet")
    assert r.status_code == 200
    assert "coverage unknown for 1 seat" in r.text
    assert "coverage: complete" not in r.text
    assert "packages incomplete" not in r.text


# --------------------------------------------------------------------------- #
# /fleet.json — the rollup travels to machine consumers
# --------------------------------------------------------------------------- #


def test_fleet_json_carries_coverage_rollup(monkeypatch):
    _mock_api(monkeypatch, {
        "/contents/projects": _res(data=[_dir("alpha"), _dir("beta")]),
        "/contents/projects/alpha": _res(data=_complete_listing("alpha")),
        "/contents/projects/beta": _res(data=_incomplete_listing("beta")),
    })
    _mock_fetch_404(monkeypatch)
    d = TestClient(app).get("/fleet.json").json()
    cov = d["coverage"]
    assert cov["state"] == "ok"
    assert cov["incomplete"] == 1 and cov["incomplete_names"] == ["beta"]
    assert cov["seats"] == 2 and cov["complete"] == 1
