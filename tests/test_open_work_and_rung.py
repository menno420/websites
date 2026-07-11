"""Offline unit tests for the wake-tooling batch: the open-work classifier
(scripts/open_work.py) and the `rung:` heartbeat line (KNOWN_KEYS
leak-guard + /fleet display).
"""

import importlib.util
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import fleet  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "open_work", Path(__file__).resolve().parents[1] / "scripts" / "open_work.py"
)
open_work = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(open_work)


# --------------------------------------------------------------------------- #
# open_work.classify
# --------------------------------------------------------------------------- #

_BRANCHES = {
    "claude/in-flight": "a" * 40,
    "claude/stranded": "b" * 40,
    "claude/landed": "c" * 40,
    "claude/mystery": "d" * 40,
}


def test_classify_with_live_pr_list():
    rows = open_work.classify(
        _BRANCHES,
        prs={"claude/in-flight": 63},
        unmerged={"claude/stranded": True, "claude/landed": False,
                  "claude/mystery": None},
    )
    by = {r["branch"]: r for r in rows}
    assert by["claude/in-flight"]["state"] == "PR-OPEN"
    assert "#63" in by["claude/in-flight"]["note"]
    assert by["claude/stranded"]["state"] == "PR-LESS"  # the rescue class
    assert by["claude/landed"]["state"] == "MERGED-STALE"
    assert by["claude/mystery"]["state"] == "UNKNOWN"  # never guessed


def test_classify_degrades_honestly_without_pr_list():
    """api.github.com unreachable (the documented session wall): unmerged
    branches say PR-UNKNOWN — partial truth labeled, never a guess."""
    rows = open_work.classify(
        {"claude/stranded": "b" * 40},
        prs=None,
        unmerged={"claude/stranded": True},
    )
    assert rows[0]["state"] == "PR-UNKNOWN"
    assert "api unreachable" in rows[0]["note"]


def test_classify_empty_is_empty():
    assert open_work.classify({}, prs={}, unmerged={}) == []


def test_classify_no_content_diff_is_ignorable_not_a_rescue_alarm():
    """A branch with commits but ZERO tree diff vs main (empty probe commit,
    or content that landed via another PR's squash) classifies NO-DIFF —
    never PR-LESS/PR-UNKNOWN. The 2026-07-11 false-positive class: the
    probe branch + two squash-landed branches each cost an MCP PR-state
    check to clear from the ⚠ stranded list."""
    rows = open_work.classify(
        {"claude/probe": "e" * 40, "claude/really-stranded": "f" * 40},
        prs=None,
        unmerged={"claude/probe": True, "claude/really-stranded": True},
        content_diff={"claude/probe": False, "claude/really-stranded": True},
    )
    by = {r["branch"]: r for r in rows}
    assert by["claude/probe"]["state"] == "NO-DIFF"
    assert "ignorable" in by["claude/probe"]["note"]
    # a real content diff still raises the alarm
    assert by["claude/really-stranded"]["state"] == "PR-UNKNOWN"


def test_classify_without_content_map_keeps_old_behavior():
    """content_diff is optional — callers/tests without it see the exact
    pre-change classification (no silent behavior change)."""
    rows = open_work.classify(
        {"claude/stranded": "b" * 40}, prs=None,
        unmerged={"claude/stranded": True},
    )
    assert rows[0]["state"] == "PR-UNKNOWN"


def test_classify_unknown_content_diff_stays_alarmed():
    """A failed content comparison (None) must NOT silence the alarm —
    unknown is treated as potentially-real work, never guessed ignorable."""
    rows = open_work.classify(
        {"claude/x": "9" * 40}, prs=None,
        unmerged={"claude/x": True},
        content_diff={"claude/x": None},
    )
    assert rows[0]["state"] == "PR-UNKNOWN"


# --------------------------------------------------------------------------- #
# rung: heartbeat line
# --------------------------------------------------------------------------- #


def test_rung_is_a_known_key_and_never_leaks_into_previous_field():
    """The routine:-into-blockers incident class, closed for rung:."""
    text = (
        "# lane · status\nupdated: 2026-07-11T02:00Z\nhealth: green (ok)\n"
        "blockers: none\n"
        "rung: backlog, self\n"
        "orders: acked=001 done=001\n"
    )
    fields = fleet.parse_status(text, "lane")["fields"]
    assert fields["rung"] == "backlog, self"
    assert "rung" not in fields["blockers"]


def test_fleet_page_shows_rung_row_when_present(monkeypatch):
    from fastapi.testclient import TestClient
    from app import github
    from app.main import app

    body = (
        "# lane · status\nupdated: 2026-07-11T02:00Z\nhealth: green (ok)\n"
        "rung: order\n"
    )

    async def fake_fetch(repo, path, ref="main", refresh=False):
        if path.startswith("control/status"):
            return {"ok": True, "status": 200, "data": body, "error": "",
                    "fetched_at": "", "cached": False, "url": ""}
        return {"ok": False, "status": 404, "data": None, "error": "nf",
                "fetched_at": "", "cached": False, "url": ""}

    async def fake_api(repo, subpath="", refresh=False):
        return {"ok": False, "status": 404, "data": None, "error": "nf",
                "fetched_at": "", "cached": False, "url": ""}

    monkeypatch.setattr(github, "fetch_file", fake_fetch)
    monkeypatch.setattr(github, "repo_api", fake_api)
    r = TestClient(app).get("/fleet")
    assert r.status_code == 200
    assert "<th>rung</th>" in r.text and "order" in r.text
