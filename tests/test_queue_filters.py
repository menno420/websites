"""Offline tests for the ORDER 019 /queue filters: the centralized listfilter
widget wired to the owner queue — project / derived-kind / age dimensions,
search, sorts, reachable counts, chips, honest unknown values and the honest
filtered-empty state; the no-param page stays identical to before. Also the
derived-kind classifier's own unit tests (it is deterministic and tested, as
the dimension's "derived" label promises).

Fixture style mirrors tests/test_app.py's _queue_fakes (offline TestClient,
monkeypatched github layer, frozen clock).
"""

import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app import clock, config, github, owner_queue  # noqa: E402
from app.main import app  # noqa: E402

# Frozen clock so age buckets are deterministic against the fixture stamps.
NOW = datetime(2026, 7, 10, 12, 0, 0, tzinfo=timezone.utc)

_STATUS_FRESH = (  # websites — updated 10h before NOW -> <24h bucket
    "# websites · status\n"
    "updated: 2026-07-10T02:00Z\n"
    "health: green (ok)\n"
    "⚑ needs-owner:\n"
    "  ⚑ OWNER-ACTION\n"
    "  WHAT: Mint the control-plane PAT.\n"
    "  WHERE: github.com settings\n"
    "  HOW: set GITHUB_TOKEN\n"
    "  WHY-IT-MATTERS: cells degraded.\n"
    "  UNBLOCKS: /queue fleet-manager half.\n"
    "  VERIFIED-NEEDED: printenv checked by gen-1.\n"
    "notes: n\n"
)

_STATUS_OLDER = (  # substrate-kit — same WHAT (dedup), 35h old
    "# substrate-kit · status\n"
    "updated: 2026-07-09T01:00Z\n"
    "health: green (ok)\n"
    "⚑ needs-owner:\n"
    "  ⚑ OWNER-ACTION\n"
    "  WHAT: Mint the control-plane PAT.\n"
    "  WHERE: github.com settings\n"
    "  HOW: set GITHUB_TOKEN\n"
    "  WHY-IT-MATTERS: cells degraded.\n"
    "  UNBLOCKS: /queue fleet-manager half.\n"
    "  VERIFIED-NEEDED: printenv checked by gen-1.\n"
    "notes: n\n"
)

_STATUS_FREETEXT = (  # superbot-next — free-text note, exactly 24h -> 1-7d
    "# superbot-next · status\n"
    "updated: 2026-07-09T12:00Z\n"
    "health: green (ok)\n"
    "⚑ needs-owner: decide the plugin cutover window\n"
    "notes: n\n"
)

_OWNER_QUEUE_MD = (  # fleet-manager doc — undated, kind "other"
    "# Owner queue\n\n"
    "⚑ OWNER-ACTION\n"
    "WHAT: Arm the coordinator wake trigger.\n"
    "WHERE: claude.ai\n"
    "HOW: arm it\n"
    "WHY-IT-MATTERS: fleet is self-terminal without it.\n"
    "UNBLOCKS: unattended operation.\n"
    "VERIFIED-NEEDED: owner-only.\n"
)


def _res(ok=True, status=200, data=None, error=""):
    return {"ok": ok, "status": status, "data": data, "error": error,
            "fetched_at": "", "cached": False, "url": ""}


def _world(monkeypatch, with_fm=True):
    """3 lanes with asks (one WHAT duplicated across two lanes) + the
    fleet-manager doc; frozen clock; token set."""
    monkeypatch.setattr(clock, "NOW_OVERRIDE", NOW)
    monkeypatch.setattr(config, "GITHUB_TOKEN", "tok")

    async def fake_fetch(repo, path, ref="main", refresh=False):
        if repo == owner_queue.FLEET_MANAGER_REPO:
            if with_fm and path == owner_queue.OWNER_QUEUE_PATH:
                return _res(data=_OWNER_QUEUE_MD)
            return _res(ok=False, status=404, data=None, error="Not Found")
        bodies = {
            "websites": _STATUS_FRESH,
            "substrate-kit": _STATUS_OLDER,
            "superbot-next": _STATUS_FREETEXT,
        }
        if repo in bodies and path == "control/status.md":
            return _res(data=bodies[repo])
        return _res(ok=False, status=404, data=None, error="nf")

    async def fake_repo_api(repo, subpath="", refresh=False):
        return _res(ok=False, status=404, data=None, error="nf")

    monkeypatch.setattr(github, "fetch_file", fake_fetch)
    monkeypatch.setattr(github, "repo_api", fake_repo_api)


# --------------------------------------------------------------------------- #
# derived-kind classifier + age buckets (the "derived, tested" promise)
# --------------------------------------------------------------------------- #


def test_classify_action_categories_and_precedence():
    assert owner_queue.classify_action("Mint the control-plane PAT.") == "token/secret"
    assert owner_queue.classify_action("set the GITHUB_TOKEN") == "token/secret"
    assert owner_queue.classify_action("pay the tester via PayPal") == "money"
    assert owner_queue.classify_action("flip it in the Railway console") == "console/settings"
    assert owner_queue.classify_action("decide the cutover window") == "decision/review"
    assert owner_queue.classify_action("something else entirely") == "other"
    assert owner_queue.classify_action("") == "other"
    # precedence: token/secret outranks decision/review
    assert owner_queue.classify_action("decide about the token") == "token/secret"
    # \b guards: 'pattern'/'environment' never classify as pat/env
    assert owner_queue.classify_action("study the pattern") == "other"


def test_item_kinds_form_source_and_action():
    structured = {"what": "Mint the PAT", "text": "",
                  "sources": [{"kind": "lane"}]}
    assert owner_queue.item_kinds(structured) == ["ask", "lane", "token/secret"]
    free = {"what": "", "text": "decide the window",
            "sources": [{"kind": "lane"}, {"kind": "fleet-manager"}]}
    assert owner_queue.item_kinds(free) == [
        "note", "fleet-manager", "lane", "decision/review"]


def test_age_bucket_boundaries_and_undated():
    def item(*ages):
        return {"sources": [{"age_hours": a} for a in ages]}

    assert owner_queue.age_bucket(item(5.0)) == "<24h"
    assert owner_queue.age_bucket(item(24.0)) == "1-7d"
    assert owner_queue.age_bucket(item(168.0)) == "1-7d"
    assert owner_queue.age_bucket(item(169.0)) == ">7d"
    assert owner_queue.age_bucket(item(200.0, 5.0)) == "<24h"  # newest wins
    assert owner_queue.age_bucket({"sources": [{"age_hours": None}]}) == "undated"


# --------------------------------------------------------------------------- #
# /queue end-to-end
# --------------------------------------------------------------------------- #


def test_queue_default_page_unchanged_plus_widget(monkeypatch):
    _world(monkeypatch)
    with TestClient(app) as c:
        r = c.get("/queue")
    assert r.status_code == 200
    # all three items, pre-filter order (newest first, undated last)
    assert "3 of 3" in r.text
    i_mint = r.text.index("Mint the control-plane PAT.")
    i_note = r.text.index("decide the plugin cutover window")
    i_arm = r.text.index("Arm the coordinator wake trigger.")
    assert i_mint < i_note < i_arm
    # the widget: dimension rows, derived label, pills as toggle links
    assert "project" in r.text and "(derived)" in r.text
    assert 'href="/queue?project=websites"' in r.text
    assert "no items match" not in r.text


def test_queue_filter_by_project_single_and_multi(monkeypatch):
    _world(monkeypatch)
    with TestClient(app) as c:
        r = c.get("/queue?project=superbot-next")
        assert "1 of 3" in r.text
        assert "decide the plugin cutover window" in r.text
        assert "Mint the control-plane PAT." not in r.text
        # multi-select is OR within the dimension
        r = c.get("/queue?project=superbot-next&project=websites")
        assert "2 of 3" in r.text
        assert "Mint the control-plane PAT." in r.text


def test_queue_filter_by_derived_kind(monkeypatch):
    _world(monkeypatch)
    with TestClient(app) as c:
        r = c.get("/queue?kind=note")
        assert "1 of 3" in r.text
        assert "decide the plugin cutover window" in r.text
        r = c.get("/queue?kind=token/secret")
        assert "1 of 3" in r.text and "Mint the control-plane PAT." in r.text
        r = c.get("/queue?kind=fleet-manager")
        assert "1 of 3" in r.text and "Arm the coordinator" in r.text


def test_queue_filter_by_age_bucket(monkeypatch):
    _world(monkeypatch)
    with TestClient(app) as c:
        r = c.get("/queue?age=%3C24h")  # <24h
        assert "1 of 3" in r.text and "Mint the control-plane PAT." in r.text
        r = c.get("/queue?age=undated")
        assert "1 of 3" in r.text and "Arm the coordinator" in r.text


def test_queue_combined_filters_and_search(monkeypatch):
    _world(monkeypatch)
    with TestClient(app) as c:
        # AND across dimensions
        r = c.get("/queue?project=websites&kind=note")
        assert "0 of 3" in r.text and "no items match" in r.text
        r = c.get("/queue?project=websites&kind=ask")
        assert "1 of 3" in r.text
        # search hits WHAT/text/fields
        r = c.get("/queue?q=cutover")
        assert "1 of 3" in r.text
        assert "decide the plugin cutover window" in r.text


def test_queue_sorts(monkeypatch):
    _world(monkeypatch)
    with TestClient(app) as c:
        r = c.get("/queue?sort=oldest")
        # oldest dated first, undated still last
        i_note = r.text.index("decide the plugin cutover window")
        i_mint = r.text.index("Mint the control-plane PAT.")
        i_arm = r.text.index("Arm the coordinator wake trigger.")
        assert i_note < i_mint < i_arm
        r = c.get("/queue?sort=az")
        i_mint = r.text.index("Mint the control-plane PAT.")
        i_note = r.text.index("decide the plugin cutover window")
        i_arm = r.text.index("Arm the coordinator wake trigger.")
        assert i_arm < i_note < i_mint


def test_queue_unknown_value_flagged_and_chips(monkeypatch):
    _world(monkeypatch)
    with TestClient(app) as c:
        r = c.get("/queue?project=bogus-project")
        assert r.status_code == 200
        assert "0 of 3" in r.text
        assert "bogus-project · unknown" in r.text  # flagged, kept visible
        assert "no items match" in r.text and "clear filters" in r.text
        # chips + clear-all on a normal filter
        r = c.get("/queue?project=websites&refresh=1")
        assert "project: websites ✕" in r.text
        assert "clear all" in r.text
        # ?refresh=1 is preserved across widget URLs
        assert "refresh=1&amp;" in r.text


def test_queue_counts_reflect_other_filters(monkeypatch):
    _world(monkeypatch)
    with TestClient(app) as c:
        r = c.get("/queue?project=superbot-next")
    # within project=superbot-next the kind pills count reachable results
    assert "note · 1" in r.text
    assert "ask · 0" in r.text


def test_queue_json_accepts_filters_and_default_is_unfiltered(monkeypatch):
    _world(monkeypatch)
    with TestClient(app) as c:
        d = c.get("/queue.json").json()
        assert len(d["items"]) == 3
        assert d["filter"]["active"] is False
        assert d["filter"]["shown"] == 3 and d["filter"]["total"] == 3
        d = c.get("/queue.json?kind=note").json()
        assert len(d["items"]) == 1
        assert d["items"][0]["text"] == "decide the plugin cutover window"
        assert d["filter"]["selected"] == {"kind": ["note"]}
        assert d["filter"]["active"] is True


def test_queue_overview_untouched_by_filter_layer(monkeypatch):
    """The domain overview() itself stays filter-free — filtering is applied
    at the route over the centralized module, so /queue.json consumers and
    the dedup/sort behavior keep their existing contract."""
    _world(monkeypatch)
    out = asyncio.run(owner_queue.overview())
    assert len(out["items"]) == 3
    assert out["summary"]["deduped"] == 1
    assert "filter" not in out
