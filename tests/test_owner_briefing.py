"""Tests for /owner/briefing — THE MORNING BRIEFING (ORDER 025).

Coverage, mirroring the suite's owner-route conventions
(tests/test_owner_security.py auth pattern, offline canned github fetches):

* gate intact — unauthenticated GET answers 401; wrong password 401;
  unset SITE_PASSWORD 503 (fail closed);
* authed render — 200 with ALL FIVE section headings present, offline;
* window logic — unit tests on ``briefing.parse_window`` (default 16h,
  override, clamp both ways, invalid → default with an honest note) plus
  the notes surfacing on the rendered page;
* honest unknown — a failing source renders ``unknown`` + its reason and
  the page still answers 200 (never fabricated data, never a 500);
* REPORTS — unit tests on ``briefing.latest_report`` (newest-entry
  selection, empty/report-less/malformed outbox → honest empty, body
  bound) plus the section rendering the newest ``control/outbox.md``
  REPORT and its explicit honest-empty state;
* the /owner console page links to the briefing prominently.
"""

import base64
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app import briefing, config, github  # noqa: E402
from app.main import app  # noqa: E402

OWNER_PW = "test-owner-pw"

NOW = datetime(2026, 7, 13, 10, 0, tzinfo=timezone.utc)


def _basic(pw: str = OWNER_PW, user: str = "owner") -> dict:
    token = base64.b64encode(f"{user}:{pw}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


def _envelope(url, *, ok=False, status=0, data=None, error="offline test"):
    return {
        "ok": ok, "status": status, "data": data,
        "error": error, "fetched_at": "", "cached": False, "url": url,
    }


@pytest.fixture()
def offline_client(monkeypatch):
    """Owner gate armed, every github fetch failing (offline) — the page
    must still answer 200 with honest unknowns."""
    monkeypatch.setattr(config, "SITE_PASSWORD", OWNER_PW)
    monkeypatch.setattr(config, "RAILWAY_TOKEN", "")

    async def fake_get(url, refresh=False, raw=False):
        return _envelope(url)

    monkeypatch.setattr(github, "_get", fake_get)
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def stubbed_client(monkeypatch):
    """Owner gate armed, github fetches answering canned happy-path data
    keyed by URL — merged PRs in and out of the window, a review-bake run,
    an open non-draft PR with green checks, the owner-actions ledger."""
    monkeypatch.setattr(config, "SITE_PASSWORD", OWNER_PW)
    monkeypatch.setattr(config, "RAILWAY_TOKEN", "")
    from app import clock
    monkeypatch.setattr(clock, "NOW_OVERRIDE", NOW)

    ledger = (
        "# Owner actions\n\n"
        "## 🟡 Open — waiting on the owner\n\n"
        "⚑ OWNER-ACTION\n"
        "WHAT: Answer the briefing fixture question.\n"
        "WHERE: docs/question-router.md\n"
        "UNBLOCKS: the fixture.\n\n"
        "⚑ OWNER-ACTION\n"
        "WHAT: Newest fixture ask (appended last).\n"
        "WHERE: here.\n"
        "UNBLOCKS: ordering assertion.\n\n"
        "## 🟢 Decided / resolved\n\n"
        "⚑ OWNER-ACTION\n"
        "WHAT: A decided ask that must NOT count as open.\n"
    )

    outbox = (
        "# websites → manager · outbox\n\n"
        "> Lane→manager channel, append-only, one writer.\n\n"
        "## REPORT · 2026-07-13T05:48Z · websites → manager · OLDER TALLY\n"
        "older report body — must not render.\n\n"
        "## REPORT · 2026-07-13T09:30Z · websites → manager · "
        "NEWEST NIGHT REPORT\n"
        "newest report body line one.\n\n"
        "### SHIPPED\n"
        "- fixture shipped row inside the newest report.\n\n"
        "## PROPOSAL · 2026-07-13T11:29Z · websites → manager · "
        "A PROPOSAL ENTRY\n"
        "proposal-only body marker — not a report.\n"
    )

    async def fake_get(url, refresh=False, raw=False):
        if "/pulls?state=closed" in url:
            return _envelope(url, ok=True, status=200, error="", data=[
                {
                    "number": 301, "title": "in-window merge",
                    "merged_at": "2026-07-13T02:00:00Z",
                    "html_url": "https://github.com/menno420/x/pull/301",
                },
                {
                    "number": 300, "title": "out-of-window merge",
                    "merged_at": "2026-07-11T02:00:00Z",
                    "html_url": "https://github.com/menno420/x/pull/300",
                },
                {"number": 299, "title": "closed unmerged", "merged_at": None},
            ])
        if "/actions/workflows/review-bake.yml/runs" in url:
            return _envelope(url, ok=True, status=200, error="", data={
                "workflow_runs": [{
                    "status": "completed", "conclusion": "success",
                    "event": "schedule",
                    "run_started_at": "2026-07-13T07:38:00Z",
                    "html_url": "https://github.com/menno420/websites/actions/runs/1",
                }],
            })
        if "/pulls?state=open" in url:
            return _envelope(url, ok=True, status=200, error="", data=[
                {
                    "number": 42, "title": "an open ready PR", "draft": False,
                    "created_at": "2026-07-13T01:00:00Z",
                    "head": {"sha": "abc123"},
                    "html_url": "https://github.com/menno420/x/pull/42",
                },
                {
                    "number": 43, "title": "a draft PR (excluded)",
                    "draft": True, "created_at": "2026-07-13T02:00:00Z",
                    "head": {"sha": "def456"},
                },
            ])
        if "/check-runs" in url:
            return _envelope(url, ok=True, status=200, error="", data={
                "check_runs": [
                    {"status": "completed", "conclusion": "success",
                     "name": "quality"},
                ],
            })
        if "OWNER-ACTIONS.md" in url:
            return _envelope(url, ok=True, status=200, error="", data=ledger)
        if "control/outbox.md" in url:
            return _envelope(url, ok=True, status=200, error="", data=outbox)
        # everything else (inboxes, statuses, registry, …) offline-degrades
        return _envelope(url)

    monkeypatch.setattr(github, "_get", fake_get)
    with TestClient(app) as c:
        yield c


# --------------------------------------------------------------------------- #
# Gate
# --------------------------------------------------------------------------- #
def test_unauthenticated_briefing_401(offline_client):
    r = offline_client.get("/owner/briefing")
    assert r.status_code == 401


def test_wrong_password_briefing_401(offline_client):
    r = offline_client.get("/owner/briefing", headers=_basic(pw="wrong"))
    assert r.status_code == 401


def test_unset_password_briefing_503(monkeypatch):
    monkeypatch.setattr(config, "SITE_PASSWORD", "")

    async def fake_get(url, refresh=False, raw=False):
        return _envelope(url)

    monkeypatch.setattr(github, "_get", fake_get)
    with TestClient(app) as c:
        assert c.get("/owner/briefing", headers=_basic()).status_code == 503


# --------------------------------------------------------------------------- #
# Authed render — five sections
# --------------------------------------------------------------------------- #
def test_authed_render_has_all_five_sections(stubbed_client):
    r = stubbed_client.get("/owner/briefing", headers=_basic())
    assert r.status_code == 200
    for heading in ("SHIPPED", "ORDERS", "ASKS", "FLEET", "WATCHES"):
        assert heading in r.text, f"missing section heading {heading}"
    assert "window: last 16h" in r.text


def test_stubbed_sections_carry_the_canned_data(stubbed_client):
    r = stubbed_client.get("/owner/briefing", headers=_basic())
    assert r.status_code == 200
    # SHIPPED: in-window merge shown, out-of-window + unmerged excluded.
    assert "in-window merge" in r.text
    assert "out-of-window merge" not in r.text
    assert "closed unmerged" not in r.text
    # ASKS: both open blocks counted, newest (appended last) listed first,
    # the Decided-section block NOT counted as open.
    assert "2 open asks" in r.text
    assert "Newest fixture ask" in r.text
    assert r.text.index("Newest fixture ask") < r.text.index(
        "Answer the briefing fixture question"
    )
    assert "must NOT count as open" not in r.text
    # WATCHES: review-bake success + the non-draft PR green, draft excluded.
    assert "review-bake" in r.text
    assert "an open ready PR" in r.text
    assert "a draft PR (excluded)" not in r.text


# --------------------------------------------------------------------------- #
# Window logic (unit)
# --------------------------------------------------------------------------- #
def test_window_default_16h():
    w = briefing.parse_window(None)
    assert w == {"hours": 16, "default_used": True, "note": ""}
    assert briefing.parse_window("")["hours"] == 16
    assert briefing.parse_window("")["note"] == ""


def test_window_override():
    w = briefing.parse_window("48")
    assert w["hours"] == 48
    assert w["default_used"] is False
    assert w["note"] == ""


def test_window_clamps_with_note():
    low = briefing.parse_window("0")
    assert low["hours"] == 1 and "clamped" in low["note"]
    neg = briefing.parse_window("-5")
    assert neg["hours"] == 1 and "clamped" in neg["note"]
    high = briefing.parse_window("9999")
    assert high["hours"] == 168 and "clamped" in high["note"]


def test_window_invalid_falls_back_to_default_with_note():
    w = briefing.parse_window("soon")
    assert w["hours"] == 16
    assert w["default_used"] is True
    assert "not a whole number" in w["note"]


def test_window_notes_surface_on_the_page(stubbed_client):
    r = stubbed_client.get("/owner/briefing?hours=soon", headers=_basic())
    assert r.status_code == 200
    assert "window: last 16h" in r.text
    assert "not a whole number" in r.text
    r2 = stubbed_client.get("/owner/briefing?hours=9999", headers=_basic())
    assert "window: last 168h" in r2.text
    assert "clamped" in r2.text
    r3 = stubbed_client.get("/owner/briefing?hours=48", headers=_basic())
    assert "window: last 48h" in r3.text
    assert "clamped" not in r3.text


# --------------------------------------------------------------------------- #
# Honest unknowns — offline everything, page still 200
# --------------------------------------------------------------------------- #
def test_offline_page_renders_honest_unknowns(offline_client):
    r = offline_client.get("/owner/briefing", headers=_basic())
    assert r.status_code == 200
    for heading in ("SHIPPED", "ORDERS", "ASKS", "FLEET", "WATCHES"):
        assert heading in r.text
    # every fetch failed → the sections say unknown WITH the reason.
    assert "unknown" in r.text
    assert "offline test" in r.text
    # nothing fabricated: no PR rows, no fake counts of merged work.
    assert "merged in the last" in r.text  # section header still explains itself


def test_offline_sections_state_unknown():
    """Domain-level: with every fetch failing, shipped/asks/watches report
    state=unknown with a reason (never an empty-but-ok fake)."""
    import asyncio

    async def run():
        async def fake_get(url, refresh=False, raw=False):
            return _envelope(url)

        real_get = github._get
        github._get = fake_get
        try:
            data = await briefing.overview(hours_raw=None, now=NOW)
        finally:
            github._get = real_get
        return data

    data = asyncio.run(run())
    assert data["shipped"]["state"] == "unknown"
    assert data["shipped"]["reason"]
    assert data["asks"]["state"] == "unknown"
    assert data["asks"]["reason"]
    assert data["watches"]["bake"]["state"] == "unknown"
    assert data["watches"]["bake"]["reason"]
    assert data["watches"]["prs"]["state"] == "unknown"
    assert data["outbox"]["state"] == "unknown"
    assert data["outbox"]["reason"]
    assert data["outbox"]["found"] is False
    assert data["window"]["hours"] == 16


# --------------------------------------------------------------------------- #
# REPORTS — latest_report (unit) + the rendered section
# --------------------------------------------------------------------------- #
def test_latest_report_picks_the_last_report_entry():
    text = (
        "# outbox\n\n"
        "## REPORT · 2026-07-13T05:48Z · websites → manager · OLDER\n"
        "older body.\n\n"
        "## REPORT · 2026-07-13T09:30Z · websites → manager · NEWEST\n"
        "newest body.\n\n"
        "### SHIPPED\n"
        "- a subsection line stays inside the entry.\n\n"
        "## PROPOSAL · 2026-07-13T11:29Z · websites → manager · IGNORED\n"
        "proposals are not reports.\n"
    )
    r = briefing.latest_report(text)
    assert r["found"] is True
    assert r["issued"] == "2026-07-13T09:30Z"
    assert r["route"] == "websites → manager"
    assert r["title"] == "NEWEST"
    assert r["total_reports"] == 2
    assert "newest body." in r["lines"]
    assert "### SHIPPED" in r["lines"]  # ### subsections belong to the entry
    assert "older body." not in r["lines"]
    assert "proposals are not reports." not in r["lines"]
    assert r["truncated"] is False
    assert r["note"] == ""


def test_latest_report_empty_and_reportless_are_honest_empty():
    assert briefing.latest_report("")["found"] is False
    assert briefing.latest_report("")["total_reports"] == 0
    reportless = (
        "# outbox\n\n"
        "## PROPOSAL · 2026-07-13T11:29Z · websites → manager · NO REPORTS\n"
        "body.\n"
    )
    r = briefing.latest_report(reportless)
    assert r["found"] is False
    assert r["title"] == ""
    assert r["lines"] == []


def test_latest_report_malformed_headings_skipped_with_note():
    text = (
        "## REPORT\n"
        "no grammar at all.\n\n"
        "## REPORT ·  · websites manager · timestamp and arrow missing\n"
        "also out of grammar.\n"
    )
    r = briefing.latest_report(text)
    assert r["found"] is False  # nothing parseable → honest empty, not a guess
    assert "2 REPORT-like heading(s) skipped" in r["note"]


def test_latest_report_bounds_the_body_with_a_truncation_flag():
    body = "\n".join(f"line {i}" for i in range(60))
    text = f"## REPORT · 2026-07-13T09:30Z · websites → manager · LONG\n{body}\n"
    r = briefing.latest_report(text)
    assert r["found"] is True
    assert len(r["lines"]) == briefing.OUTBOX_REPORT_MAX_LINES
    assert r["truncated"] is True
    assert r["limit"] == briefing.OUTBOX_REPORT_MAX_LINES


def test_reports_section_renders_the_newest_outbox_report(stubbed_client):
    r = stubbed_client.get("/owner/briefing", headers=_basic())
    assert r.status_code == 200
    assert "REPORTS" in r.text
    # newest report rendered: heading fields + body, subsection included.
    assert "NEWEST NIGHT REPORT" in r.text
    assert "2026-07-13T09:30Z" in r.text
    assert "newest report body line one." in r.text
    assert "fixture shipped row inside the newest report." in r.text
    assert "newest of 2 reports" in r.text
    # older report and the PROPOSAL entry stay in the outbox, not the page.
    assert "OLDER TALLY" not in r.text
    assert "older report body" not in r.text
    assert "proposal-only body marker" not in r.text


def test_reports_section_honest_empty_when_no_report_entries(monkeypatch):
    monkeypatch.setattr(config, "SITE_PASSWORD", OWNER_PW)
    monkeypatch.setattr(config, "RAILWAY_TOKEN", "")

    reportless = (
        "# websites → manager · outbox\n\n"
        "## PROPOSAL · 2026-07-13T11:29Z · websites → manager · NOT A REPORT\n"
        "proposal-only body marker.\n"
    )

    async def fake_get(url, refresh=False, raw=False):
        if "control/outbox.md" in url:
            return _envelope(
                url, ok=True, status=200, error="", data=reportless
            )
        return _envelope(url)

    monkeypatch.setattr(github, "_get", fake_get)
    with TestClient(app) as c:
        r = c.get("/owner/briefing", headers=_basic())
    assert r.status_code == 200
    assert "no REPORT entries" in r.text  # explicit honest-empty, page 200
    assert "NOT A REPORT" not in r.text
    assert "proposal-only body marker" not in r.text


def test_reports_section_unknown_when_outbox_unreadable(offline_client):
    r = offline_client.get("/owner/briefing", headers=_basic())
    assert r.status_code == 200
    assert "REPORTS" in r.text
    # the offline fixture fails every fetch → the section says unknown with
    # the reason instead of an invented report or a silent omission.
    assert 'id="reports"' in r.text
    assert "no REPORT entries" not in r.text


# --------------------------------------------------------------------------- #
# Console link
# --------------------------------------------------------------------------- #
def test_owner_console_links_to_the_briefing(offline_client):
    r = offline_client.get("/owner", headers=_basic())
    assert r.status_code == 200
    assert '/owner/briefing' in r.text
    assert "morning briefing" in r.text
