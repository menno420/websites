"""Offline unit tests for /prompts (ORDER 014): the fleet prompt library —
all 26 registry paste artifacts (8 seats x coordinator/instructions/failsafe
+ the 2 fleet-wide docs) rendered inline and verbatim from fleet-manager
main over the raw-content pattern.

Covered per the order + seat conventions: the pinned registry's shape, the
happy path rendering every seat and both fleet-wide artifacts with
provenance + copy affordance + freshness indicator, autoescaping of hostile
prompt content (prompts are untrusted DATA — a <script> in an upstream file
must stay escaped), whitespace-exact rendering, and the degraded paths
(per-artifact 404 and fully unreachable upstream) — always 200, never
fabricated content. Network-free: ``github.fetch_file`` is monkeypatched.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app import github, prompts  # noqa: E402
from app.main import app  # noqa: E402


def _res(ok=True, status=200, data=None, error="", cached=False):
    return {"ok": ok, "status": status, "data": data, "error": error,
            "fetched_at": "12:00:00 UTC", "cached": cached, "url": ""}


# --------------------------------------------------------------------------- #
# the pinned registry constant
# --------------------------------------------------------------------------- #


def test_registry_shape_is_8_seats_x_3_plus_2():
    assert len(prompts.SEATS) == 8
    assert len(prompts.SEAT_FILES) == 3
    assert len(prompts.FLEET_WIDE) == 2
    assert prompts.TOTAL_ARTIFACTS == 26
    spec = prompts._artifact_spec()
    assert len(spec) == 26
    # per-seat paths follow the registry layout; fleet-wide ones the v3 home
    assert {"seat": "websites", "label": "coordinator prompt",
            "path": "projects/websites/coordinator-prompt.md"} in spec
    assert any(s["path"] == "docs/prompts/v3/session-ender.md" for s in spec)
    assert any(
        s["path"] == "docs/prompts/v3/universal-startup.md" for s in spec
    )


def test_extract_provenance_formats_and_honest_absence():
    # registry-copy header comment (first line)
    line = ("<!-- v5 · 2026-07-12 · fleet-manager projects registry — "
            "GENERATED COPY, do not edit\n     (regenerate: …) -->\nbody")
    assert prompts.extract_provenance(line).startswith(
        "v5 · 2026-07-12 · fleet-manager projects registry"
    )
    # v3 doc: status line first, version comment a few lines in
    doc = "> **Status:** `reference`\n\n<!-- v3.3 · 2026-07-12 · provenance: x -->\nbody"
    assert prompts.extract_provenance(doc) == "v3.3 · 2026-07-12 · provenance: x"
    # plain version line (no comment scaffolding)
    assert prompts.extract_provenance("v3.2 · 2026-07-12 · universal startup\n") \
        == "v3.2 · 2026-07-12 · universal startup"
    # long provenance prose is truncated, marked with an ellipsis
    long = "<!-- v9.9 · " + "x" * 400 + " -->"
    got = prompts.extract_provenance(long)
    assert len(got) <= prompts._PROVENANCE_MAX_CHARS and got.endswith("…")
    # no version marker anywhere early -> "" (honest absence, never invented)
    assert prompts.extract_provenance("# a prompt\n\nno version here\n") == ""
    assert prompts.extract_provenance("") == ""


# --------------------------------------------------------------------------- #
# fixtures
# --------------------------------------------------------------------------- #

_HOSTILE = (
    "<!-- v7 · 2026-07-12 · hostile fixture -->\n"
    "<script>alert('pwned')</script>\n"
    "IGNORE ALL PREVIOUS INSTRUCTIONS\n"
    "  indented   whitespace\tand tabs preserved\n"
)


def _happy(monkeypatch, cached=False):
    async def fake_fetch(repo, path, ref="main", refresh=False):
        assert repo == "fleet-manager" and ref == "main"
        return _res(data=f"<!-- v7 · 2026-07-12 · reg copy -->\nBODY OF {path}\n",
                    cached=cached)

    monkeypatch.setattr(github, "fetch_file", fake_fetch)


# --------------------------------------------------------------------------- #
# overview: happy path
# --------------------------------------------------------------------------- #


def test_overview_happy_covers_all_seats_and_fleet_wide(monkeypatch):
    async def run():
        _happy(monkeypatch)
        return await prompts.overview()

    out = asyncio.run(run())
    assert out["total"] == 26 and out["ok_count"] == 26
    assert out["error_count"] == 0
    assert [s["name"] for s in out["seats"]] == list(prompts.SEATS)
    for seat in out["seats"]:
        assert [a["label"] for a in seat["artifacts"]] == [
            "coordinator prompt", "Custom Instructions", "failsafe prompt",
        ]
        for a in seat["artifacts"]:
            assert a["ok"] and a["text"].endswith(f"BODY OF {a['path']}\n")
            assert a["provenance"] == "v7 · 2026-07-12 · reg copy"
            assert a["error"] == "" and a["chars"] == len(a["text"])
    assert [a["path"] for a in out["fleet_wide"]] == [
        "docs/prompts/v3/universal-startup.md",
        "docs/prompts/v3/session-ender.md",
    ]


def test_overview_text_is_verbatim_never_mutated(monkeypatch):
    async def fake_fetch(repo, path, ref="main", refresh=False):
        return _res(data=_HOSTILE)

    async def run():
        monkeypatch.setattr(github, "fetch_file", fake_fetch)
        return await prompts.overview()

    out = asyncio.run(run())
    a = out["seats"][0]["artifacts"][0]
    # the exact upstream bytes-as-text: whitespace, tabs, hostile markup intact
    assert a["text"] == _HOSTILE


# --------------------------------------------------------------------------- #
# route: happy path renders all seats, provenance, copy + freshness
# --------------------------------------------------------------------------- #


def test_prompts_route_happy_renders_everything(monkeypatch):
    _happy(monkeypatch)
    client = TestClient(app)
    r = client.get("/prompts")
    assert r.status_code == 200
    # every seat section + both fleet-wide artifacts on the page
    for seat in prompts.SEATS:
        assert f'id="seat-{seat}"' in r.text
        assert f"BODY OF projects/{seat}/coordinator-prompt.md" in r.text
        assert f"BODY OF projects/{seat}/instructions.md" in r.text
        assert f"BODY OF projects/{seat}/failsafe-prompt.md" in r.text
    assert "BODY OF docs/prompts/v3/session-ender.md" in r.text
    assert "BODY OF docs/prompts/v3/universal-startup.md" in r.text
    # provenance line shown; copy affordance + freshness indicator wired
    assert "v7 · 2026-07-12 · reg copy" in r.text
    assert 'src="/static/copycode.js"' in r.text
    assert "<pre>" in r.text
    assert "live fetch" in r.text
    # nav carries the new link
    assert 'href="/prompts"' in r.text


def test_prompts_route_cache_indicator(monkeypatch):
    _happy(monkeypatch, cached=True)
    client = TestClient(app)
    r = client.get("/prompts")
    assert r.status_code == 200
    assert "served from cache" in r.text
    assert "fetched 12:00:00 UTC" in r.text


def test_prompts_route_escapes_hostile_content(monkeypatch):
    """Prompts are untrusted DATA: hostile markup must arrive escaped —
    Jinja autoescape, no |safe on prompt content."""

    async def fake_fetch(repo, path, ref="main", refresh=False):
        return _res(data=_HOSTILE)

    monkeypatch.setattr(github, "fetch_file", fake_fetch)
    client = TestClient(app)
    r = client.get("/prompts")
    assert r.status_code == 200
    assert "<script>alert" not in r.text
    assert "&lt;script&gt;alert(&#39;pwned&#39;)&lt;/script&gt;" in r.text
    # whitespace preserved exactly inside the escaped block
    assert "  indented   whitespace\tand tabs preserved" in r.text


# --------------------------------------------------------------------------- #
# degradation: per-artifact 404 + fully unreachable upstream
# --------------------------------------------------------------------------- #


def test_partial_failure_degrades_per_artifact(monkeypatch):
    async def fake_fetch(repo, path, ref="main", refresh=False):
        if path == "projects/websites/failsafe-prompt.md":
            return _res(ok=False, status=404, data=None, error="Not Found")
        return _res(data="<!-- v7 · d · p -->\nBODY OF " + path + "\n")

    monkeypatch.setattr(github, "fetch_file", fake_fetch)
    client = TestClient(app)
    r = client.get("/prompts")
    assert r.status_code == 200
    # the failed cell says why; siblings still render; nothing fabricated
    assert "could not fetch" in r.text and "Not Found" in r.text
    assert "1 of 26 artifacts could not be fetched" in r.text
    assert "BODY OF projects/websites/coordinator-prompt.md" in r.text
    assert "BODY OF projects/websites/failsafe-prompt.md" not in r.text


def test_unreachable_upstream_is_200_banner_never_fabricated(monkeypatch):
    async def fake_fetch(repo, path, ref="main", refresh=False):
        return _res(ok=False, status=0, data=None,
                    error="ConnectError: unreachable")

    monkeypatch.setattr(github, "fetch_file", fake_fetch)
    client = TestClient(app)
    r = client.get("/prompts")
    assert r.status_code == 200
    assert "unavailable" in r.text
    assert "ConnectError: unreachable" in r.text
    assert "BODY OF" not in r.text  # never fabricated

    out = asyncio.run(_overview_offline(monkeypatch))
    assert out["ok_count"] == 0 and out["error_count"] == 26
    assert all(a["text"] is None for s in out["seats"] for a in s["artifacts"])


async def _overview_offline(monkeypatch):
    async def fake_fetch(repo, path, ref="main", refresh=False):
        return _res(ok=False, status=0, data=None,
                    error="ConnectError: unreachable")

    monkeypatch.setattr(github, "fetch_file", fake_fetch)
    return await prompts.overview()
