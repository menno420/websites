"""Offline tests for the ORDER 041 REMAINDER: the same prompt data surfaced
on (a) each seat's dispatch screen (``/projects/{package}`` — a compact
prompt-versions strip) and (b) the gated owner console (``/owner`` — a
per-seat fleet prompt-state card) — as VIEWS over the ONE source PR #236
shipped: ``prompt_history.history()`` for the version ladder and the
``prompts`` drift-row model (``seat_drift`` / ``console_rollup``, both pure
reductions of ``_build_deployed``) for deployed-vs-canonical. No second
fetch path, no prompt copy stored.

Pinned here, both surfaces: rendering (current version + ladder labels,
"deployed vX · canonical vY" version line, stale count, history deep link)
and honest degradation (history unavailable → SAID in the strip, never
hidden or invented; fetch failures → unreachable/not recorded rows, never a
fabricated "in sync"; non-seat packages get NO strip). Fixture shapes are
copied from tests/test_prompts.py + tests/test_prompt_history.py (the real
committed shapes). Fully offline: ``github.repo_api`` / ``github.fetch_file``
/ ``github._get`` monkeypatched.
"""

import asyncio
import base64
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app import (  # noqa: E402
    briefing,
    clock,
    config,
    envhub,
    github,
    prompt_history,
    prompts,
    readiness,
)
from app.main import app  # noqa: E402
from app.roster import seat_for  # noqa: E402


def _res(ok=True, status=200, data=None, error="", cached=False):
    return {"ok": ok, "status": status, "data": data, "error": error,
            "fetched_at": "12:00:00 UTC", "cached": cached, "url": ""}


# --------------------------------------------------------------------------- #
# fixtures — the real committed shapes (registry copies, meta.md table,
# triggers snapshot, commits-API ladder)
# --------------------------------------------------------------------------- #

_FAILSAFE_PROMPT = (
    "FAILSAFE WAKE (Websites, Q-0265): send_later chain alive -> verify in "
    "one line, end. Stalled -> resume the work loop."
)

_CANON_CI = (
    "<!-- v6 · 2026-07-13 · fleet-manager projects registry — GENERATED "
    "COPY, do not edit -->\n"
    "<!-- registry-header-end -->\n"
    "v3.5 {seat} CI — dictionary+router. DRIFT CHECK: quote this line on "
    "ask.\n\n"
    "You are a session in the seat.\n\n"
    "Provenance: v3.5 2026-07-13 · core@95b5c8f.\n"
)

_CANON_STARTUP = (
    "<!-- v7 · 2026-07-13 · fleet-manager projects registry — GENERATED "
    "COPY -->\n"
    "v3.5 · 2026-07-13 · EXPANDED startup (coordinator brief) · {seat}\n"
    "You are the coordinator.\n"
)

_CANON_FAILSAFE = (
    "<!-- v6 · 2026-07-13 · fleet-manager projects registry — GENERATED "
    "COPY -->\n"
    "<!-- registry-header-end -->\n"
    "# Seat — failsafe cron (dead-man wake, Q-0265)\n\n"
    "## Prompt text (create_trigger `prompt`, EXACTLY)\n\n"
    "```\n" + _FAILSAFE_PROMPT + "\n```\n\n"
    "## Cutover\n\nMore doc text.\n"
)

# 4-column restructure-seat meta.md: version-stamped claims dated BEFORE the
# canonical copies' 2026-07-13 → provably stale (never "in sync" from prose).
_META_WEBSITES = """# websites — package meta

## Deployed-state per part (2026-07-10)

| Part | This package file | Deployed today | Citation |
|---|---|---|---|
| 1 instructions | `instructions.md` | **DEPLOYED v3.4** — pasted 2026-07-10 (~02:05Z) | fm docs |
| 2 wake prompt (= coordinator prompt) | `coordinator-prompt.md` | **DEPLOYED v3.4** — pasted 2026-07-10 | owner actions row E |
| 4 wake cron text | `failsafe-prompt.md` | **DEPLOYED trigger verified** | CAPABILITIES log |
"""

_SEAT_HUMAN = {
    "fleet-manager": "Fleet Manager", "venture-lab": "Venture Lab",
    "superbot-world": "SuperBot World", "superbot-2.0": "SuperBot 2.0",
    "ideas-lab": "Ideas Lab", "game-lab": "Game Lab",
    "self-improvement": "Self Improvement", "websites": "Websites",
    "curious-research": "Curious Research",
}


def _snapshot_json(prompt=_FAILSAFE_PROMPT, captured="2026-07-13T00:39:53Z"):
    data = []
    for i, seat in enumerate(prompts.SEATS):
        data.append({
            "cron_expression": "45 */2 * * *",
            "enabled": True,
            "id": f"trig_test{i:02d}",
            "job_config": {"ccr": {"events": [{"data": {"message": {
                "content": prompt, "role": "user"}}}]}},
            "name": f"{_SEAT_HUMAN[seat]} failsafe wake",
        })
    return json.dumps({"captured_at": captured, "data": data})


# History ladder (commits-API order: newest first) + file-at-sha bodies.
_SHA_A = "a1" * 20  # oldest — v3.4
_SHA_B = "b2" * 20  # middle — v3.5
_SHA_C = "c3" * 20  # newest — v3.6

_LADDER = [
    {"sha": _SHA_C, "commit": {"committer": {"date": "2026-07-13T02:05:50Z"},
                               "message": "v3.6 prompt fold (#153)"}},
    {"sha": _SHA_B, "commit": {"committer": {"date": "2026-07-13T01:05:43Z"},
                               "message": "v3.5 per-seat fold (#151)"}},
    {"sha": _SHA_A, "commit": {"committer": {"date": "2026-07-12T19:49:25Z"},
                               "message": "v3.4 seat prompts (#122)"}},
]

_SHA_BODIES = {
    _SHA_C: "<!-- v3.6 · 2026-07-13 -->\nv3.6 websites CI.\nbody\n",
    _SHA_B: "<!-- v3.5 · 2026-07-13 -->\nv3.5 websites CI.\nbody\n",
    _SHA_A: "<!-- v3.4 · 2026-07-12 -->\nv3.4 websites CI.\nbody\n",
}

# Dispatch-screen package listing (the /projects/{package} side).
_DETAIL_LISTING = [
    {"type": "file", "path": "projects/websites/meta.md"},
    {"type": "file", "path": "projects/websites/project-instructions.md"},
    {"type": "file", "path": "projects/websites/coordinator-prompt.md"},
    {"type": "file", "path": "projects/websites/failsafe.md"},
]

_DETAIL_TEXTS = {
    "projects/websites/project-instructions.md": "FULL CUSTOM INSTRUCTIONS TEXT",
    "projects/websites/failsafe.md": "failsafe cron: armed hourly",
}


def _patch_all(monkeypatch, commits_ok=True, snapshot=None, meta=None,
               registry_dirs=("websites", "old-lab")):
    """One offline world: registry listing + package listing + commits
    ladder (repo_api) and registry copies + meta.md + snapshot + file-at-sha
    bodies (fetch_file)."""
    snapshot_text = _snapshot_json() if snapshot is None else snapshot
    meta_text = _META_WEBSITES if meta is None else meta

    async def fake_api(repo, subpath="", refresh=False):
        assert repo == "fleet-manager"
        if subpath.startswith("/commits?path="):
            if not commits_ok:
                return _res(ok=False, status=0, data=None,
                            error="proxy blocked the commits API")
            return _res(data=_LADDER)
        if subpath.endswith("/contents/projects"):
            return _res(data=[
                {"type": "dir", "name": n, "path": f"projects/{n}"}
                for n in registry_dirs
            ])
        if subpath.endswith("/contents/projects/websites"):
            return _res(data=_DETAIL_LISTING)
        if subpath.endswith("/contents/projects/old-lab"):
            return _res(data=[
                {"type": "file", "path": "projects/old-lab/meta.md"}])
        return _res(ok=False, status=404, data=None, error="nf")

    async def fake_fetch(repo, path, ref="main", refresh=False):
        assert repo == "fleet-manager"
        if ref != "main":  # file-at-sha: the history ladder bodies
            if ref in _SHA_BODIES:
                return _res(data=_SHA_BODIES[ref])
            return _res(ok=False, status=404, data=None, error="Not Found")
        if path == prompts.SNAPSHOT_PATH:
            if snapshot_text is False:
                return _res(ok=False, status=404, data=None, error="Not Found")
            return _res(data=snapshot_text)
        if path.endswith("/meta.md"):
            seat = path.split("/")[1]
            if seat == "websites":
                return _res(data=meta_text)
            if seat == "old-lab":
                return _res(data="# old-lab\n\nRetired — merged into web.\n")
            return _res(ok=False, status=404, data=None, error="Not Found")
        if path in _DETAIL_TEXTS:
            return _res(data=_DETAIL_TEXTS[path])
        if path.startswith("projects/"):
            fname = path.rsplit("/", 1)[-1]
            seat = path.split("/")[1]
            if fname == "instructions.md":
                return _res(data=_CANON_CI.format(seat=seat))
            if fname == "coordinator-prompt.md":
                return _res(data=_CANON_STARTUP.format(seat=seat))
            if fname == "failsafe-prompt.md":
                return _res(data=_CANON_FAILSAFE)
        return _res(ok=False, status=404, data=None, error="nf")

    monkeypatch.setattr(github, "repo_api", fake_api)
    monkeypatch.setattr(github, "fetch_file", fake_fetch)


# --------------------------------------------------------------------------- #
# seat mapping — packages resolve to roster seats, never guessed
# --------------------------------------------------------------------------- #


def test_seat_for_maps_aliases_and_rejects_non_seats():
    assert seat_for("websites") == "websites"
    assert seat_for("superbot-2.0") == "superbot-2.0"
    # aliases normalize (lowercase, _ -> -) to the canonical seat
    assert seat_for("superbot-next") == "superbot-2.0"
    assert seat_for("Superbot_Next") == "superbot-2.0"
    assert seat_for("project-manager") == "fleet-manager"
    # non-seat packages map to nothing — the strip is never invented
    assert seat_for("old-lab") == ""
    assert seat_for("") == ""


def test_strip_is_none_for_non_seat_packages():
    # no fetch happens: the roster gate short-circuits before any network
    assert asyncio.run(prompt_history.strip("old-lab")) is None
    assert asyncio.run(prompt_history.strip("not-a-package")) is None


# --------------------------------------------------------------------------- #
# (a) /projects/{package} — the prompt-versions strip
# --------------------------------------------------------------------------- #


def test_dispatch_strip_shows_ladder_and_drift(monkeypatch):
    _patch_all(monkeypatch)
    r = TestClient(app).get("/projects/websites")
    assert r.status_code == 200
    assert 'id="prompt-versions"' in r.text
    # current version + ladder labels, parsed from the fetched files
    assert "current v3.6" in r.text
    for label in ("v3.6", "v3.5", "v3.4"):
        assert label in r.text
    # deployed-vs-canonical: version-aware line + honest per-artifact states
    assert "deployed v3.4 · canonical v3.5" in r.text
    assert "Custom Instructions: stale" in r.text
    assert "failsafe prompt: in sync" in r.text
    assert "2 of 3 stale/drifted" in r.text
    # two clicks to the full history — the strip links the seat's page
    assert 'href="/prompts/history/websites"' in r.text
    # the dispatch screen itself still renders (strip is additive)
    assert "FULL CUSTOM INSTRUCTIONS TEXT" in r.text


def test_dispatch_strip_history_unavailable_is_said_not_hidden(monkeypatch):
    _patch_all(monkeypatch, commits_ok=False)
    r = TestClient(app).get("/projects/websites")
    assert r.status_code == 200
    assert 'id="prompt-versions"' in r.text  # strip still there
    assert "history not available" in r.text
    assert "proxy blocked the commits API" in r.text  # the exact reason
    assert "current v3.6" not in r.text  # never a fabricated ladder
    # the drift half still renders from its own records
    assert "deployed v3.4 · canonical v3.5" in r.text
    assert 'href="/prompts/history/websites"' in r.text


def test_dispatch_strip_absent_for_non_seat_package(monkeypatch):
    _patch_all(monkeypatch)
    r = TestClient(app).get("/projects/old-lab")
    assert r.status_code == 200
    assert 'id="prompt-versions"' not in r.text
    assert "/prompts/history/" not in r.text


def test_strip_data_reuses_the_history_module(monkeypatch):
    """strip() is a view over prompt_history.history() — same ladder, same
    labels, nothing re-derived."""
    _patch_all(monkeypatch)

    async def run():
        return (
            await prompt_history.strip("websites"),
            await prompt_history.history("websites", "ci"),
        )

    strip, hist = asyncio.run(run())
    assert strip["available"] is hist["available"] is True
    assert strip["current"] == hist["newest_label"] == "v3.6"
    assert strip["labels"] == [v["label"] for v in hist["versions"]]
    assert strip["total"] == len(hist["versions"])
    assert strip["history_link"] == "/prompts/history/websites"
    # drift rows are the /prompts row model (state + version_line fields)
    assert {r["label"] for r in strip["rows"]} == {
        "Custom Instructions", "coordinator prompt", "failsafe prompt"}
    assert strip["stale"] == 2


# --------------------------------------------------------------------------- #
# (b) /owner — the fleet prompt-state card
# --------------------------------------------------------------------------- #

OWNER_PW = "test-owner-pw"


def _basic(pw=OWNER_PW, user="owner"):
    token = base64.b64encode(f"{user}:{pw}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


_ENVCOV_UNKNOWN = {
    "state": "unknown", "reason": "offline test", "complete": 0,
    "incomplete": 0, "unknown": 0, "incomplete_names": [],
    "unknown_names": [],
}


def _patch_owner_siblings(monkeypatch):
    """Can the board's OTHER data sources so the prompt-state card is
    exercised in isolation (same style as tests/test_owner_*)."""
    async def fake_board(refresh=False, reveal_secrets=False):
        return []

    async def fake_rollup(refresh=False):
        return dict(_ENVCOV_UNKNOWN)

    async def fake_asks(refresh=False):
        # The preflight-verdicts sibling (askverify): honest-unknown canned
        # state, so the prompt-state card stays exercised in isolation.
        return {"state": "unknown", "reason": "canned offline", "count": 0,
                "top": [], "note": "", "url": "", "verify": None}

    monkeypatch.setattr(readiness, "board", fake_board)
    monkeypatch.setattr(envhub, "board_rollup", fake_rollup)
    monkeypatch.setattr(briefing, "asks", fake_asks)
    monkeypatch.setattr(config, "SITE_PASSWORD", OWNER_PW)


def test_console_rollup_reduces_the_drift_rows(monkeypatch):
    _patch_all(monkeypatch)
    out = asyncio.run(prompts.console_rollup())
    assert [r["seat"] for r in out["rows"]] == list(prompts.SEATS)
    row = next(r for r in out["rows"] if r["seat"] == "websites")
    assert row["version_line"] == "deployed v3.4 · canonical v3.5"
    assert row["stale"] == 2 and row["total"] == 3
    assert row["state"] == "stale" and row["cls"] == "warn"
    assert row["history_url"] == "/prompts/history/websites"
    # a seat with no meta ledger: honest not-recorded, never invented
    other = next(r for r in out["rows"] if r["seat"] == "game-lab")
    assert other["version_line"] == ""
    assert other["stale"] == 0
    # snapshot byte-match still gives its failsafe an honest "in sync"
    assert any(s["state"] == "in sync" for s in other["states"])
    assert out["stale_total"] == 2
    assert out["snapshot"]["ok"] and out["snapshot"]["captured_at"]


def test_console_rollup_flags_stale_snapshot_age(monkeypatch):
    """A failsafe snapshot older than SNAPSHOT_STALE_HOURS exposes an age and
    is_stale — computed against an injectable ``now`` (deterministic, no wall
    clock). The snapshot is a manager-wake artifact that freezes when the
    manager seat parks; the panel reads live but says how stale it is."""
    _patch_all(monkeypatch)  # snapshot captured 2026-07-13T00:39:53Z
    now = datetime(2026, 7, 14, 6, 39, 53, tzinfo=timezone.utc)  # +30h
    out = asyncio.run(prompts.console_rollup(now=now))
    snap = out["snapshot"]
    assert snap["ok"] and snap["captured_ok"] is True
    assert snap["is_stale"] is True
    assert round(snap["age_hours"]) == 30
    assert snap["age_human"] == "30h ago"
    assert snap["stale_hours"] == prompts.SNAPSHOT_STALE_HOURS == 24


def test_console_rollup_fresh_snapshot_not_stale(monkeypatch):
    """A recent snapshot exposes its age but is NOT flagged stale — no
    fabricated warning when the data is fresh."""
    _patch_all(monkeypatch)
    now = datetime(2026, 7, 13, 6, 39, 53, tzinfo=timezone.utc)  # +6h
    out = asyncio.run(prompts.console_rollup(now=now))
    snap = out["snapshot"]
    assert snap["captured_ok"] is True
    assert snap["is_stale"] is False
    assert snap["age_human"] == "6h ago"


def test_owner_console_warns_when_snapshot_stale(monkeypatch):
    """The owner console renders the age + a >24h-stale banner attributing the
    freeze upstream (this panel reads live). Clock pinned via app.clock."""
    _patch_all(monkeypatch)
    _patch_owner_siblings(monkeypatch)
    monkeypatch.setattr(
        clock, "NOW_OVERRIDE",
        datetime(2026, 7, 14, 6, 39, 53, tzinfo=timezone.utc),  # 30h later
    )
    r = TestClient(app).get("/owner", headers=_basic())
    assert r.status_code == 200
    assert "captured 2026-07-13T00:39:53Z" in r.text  # raw stamp kept
    assert "(30h ago)" in r.text
    assert "&gt;24h stale" in r.text
    assert "awaiting an upstream" in r.text
    assert "reads live" in r.text


def test_owner_console_no_warning_when_snapshot_fresh(monkeypatch):
    """A fresh snapshot shows the age but renders NO stale banner."""
    _patch_all(monkeypatch)
    _patch_owner_siblings(monkeypatch)
    monkeypatch.setattr(
        clock, "NOW_OVERRIDE",
        datetime(2026, 7, 13, 6, 39, 53, tzinfo=timezone.utc),  # 6h later
    )
    r = TestClient(app).get("/owner", headers=_basic())
    assert r.status_code == 200
    assert "(6h ago)" in r.text
    assert "awaiting an upstream" not in r.text  # no stale-snapshot banner
    assert "&gt;24h stale" not in r.text


def test_owner_console_renders_per_seat_prompt_state(monkeypatch):
    _patch_all(monkeypatch)
    _patch_owner_siblings(monkeypatch)
    r = TestClient(app).get("/owner", headers=_basic())
    assert r.status_code == 200
    assert 'id="prompt-state"' in r.text
    assert "fleet prompt state" in r.text
    # every roster seat gets a row with its history deep link
    for seat in prompts.SEATS:
        assert f'href="/prompts/history/{seat}"' in r.text
    # the websites row: version line, stale count, worst-state badge
    assert "deployed v3.4 · canonical v3.5" in r.text
    assert "2 of 3" in r.text
    assert "2 artifacts stale/drifted fleet-wide" in r.text
    assert "captured 2026-07-13T00:39:53Z" in r.text


def test_owner_console_degrades_honestly_when_upstream_is_down(monkeypatch):
    _patch_owner_siblings(monkeypatch)

    async def fake_get(url, refresh=False, raw=False):
        return {"ok": False, "status": 0, "data": None, "error": "offline",
                "fetched_at": "", "cached": False, "url": url}

    async def fake_api(repo, subpath="", refresh=False):
        return _res(ok=False, status=0, data=None, error="offline")

    async def fake_fetch(repo, path, ref="main", refresh=False):
        return _res(ok=False, status=0, data=None, error="offline")

    monkeypatch.setattr(github, "_get", fake_get)
    monkeypatch.setattr(github, "repo_api", fake_api)
    monkeypatch.setattr(github, "fetch_file", fake_fetch)
    r = TestClient(app).get("/owner", headers=_basic())
    assert r.status_code == 200
    assert 'id="prompt-state"' in r.text
    # every verdict degrades to unreachable — equality is never invented
    assert "unreachable" in r.text
    assert ">in sync</span>" not in r.text
    assert "unavailable — offline" in r.text  # the snapshot line says why
    # never a fabricated green while nothing was comparable
    assert "no stale or drifted record" not in r.text
    assert "no verdict assumed" in r.text
    assert "stale/drifted fleet-wide" not in r.text


def test_owner_console_requires_auth_and_stays_get_only(monkeypatch):
    """The new surface adds NO state-changing route: /owner stays gated GET;
    unauthenticated access is still refused."""
    _patch_all(monkeypatch)
    _patch_owner_siblings(monkeypatch)
    client = TestClient(app)
    assert client.get("/owner").status_code == 401
    # GET-rendering only — the new surfaces accept no state change
    assert client.post("/projects/websites").status_code == 405
    assert client.post("/owner", headers=_basic()).status_code == 405
