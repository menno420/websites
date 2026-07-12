"""ORDER 019 PR2 filter tests for botsite's list surfaces — the centralized
listfilter core vendored from app/listfilter.py and applied to /arcade, the
/testing task catalog, and the Basic-auth /testing/owner submissions queue.

Covers, per surface: the no-param page renders identically-ordered full lists
(default unchanged), single + combined dimension filters, search, sorts,
honest unknown-value flagging, the honest filtered-empty state, and — for the
owner queue — that auth stays exactly as strict as before. Plus the vendored-
copy byte-identity tests (the module needed zero edits, so identity is
asserted, not skipped).

Network-free: the site feed is primed, the arcade registry is a tmp file,
and the SQLite store points at a per-test temp file (the test_testing.py
fixture style)."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from botsite import app as app_module
from botsite import arcade, testing
from botsite import data_source as ds
from botsite import testing_ai

REPO_ROOT = Path(__file__).resolve().parents[2]
ORIGIN = {"Origin": "http://testserver"}
PW = "owner-pass"


# --------------------------------------------------------------------------
# vendored-copy byte identity — the sharing pattern's contract
# --------------------------------------------------------------------------
def test_vendored_listfilter_module_is_byte_identical_to_app():
    ours = (REPO_ROOT / "botsite" / "listfilter.py").read_bytes()
    theirs = (REPO_ROOT / "app" / "listfilter.py").read_bytes()
    assert ours == theirs, (
        "botsite/listfilter.py must stay a byte-identical vendored copy of "
        "app/listfilter.py (like static/ds/ and app.js — update both together)"
    )


def test_vendored_listfilter_partial_is_byte_identical_to_app():
    ours = (REPO_ROOT / "botsite" / "templates" / "_listfilter.html").read_bytes()
    theirs = (REPO_ROOT / "app" / "templates" / "_listfilter.html").read_bytes()
    assert ours == theirs


# --------------------------------------------------------------------------
# /arcade — maturity / availability dims, search, sorts
# --------------------------------------------------------------------------
ARCADE_FIXTURE = [
    {
        "slug": "alpha-quest", "name": "Alpha Quest", "tagline": "grid crawler",
        "description": "Crawl the alpha grid.", "maturity": "playable",
        "availability": "live", "source_repo": "menno420/alpha",
        "url": "https://alpha.example",
    },
    {
        "slug": "beta-blast", "name": "Beta Blast", "tagline": "shooter",
        "description": "Blast the beta blobs.", "maturity": "beta",
        "availability": "download", "source_repo": "menno420/beta",
        "url": "https://beta.example/zip",
    },
    {
        "slug": "proto-pit", "name": "Proto Pit", "tagline": "sandbox",
        "description": "A prototype pit.", "maturity": "prototype",
        "availability": "unavailable", "source_repo": "menno420/proto",
        "url": None, "status_note": "not deployed yet",
    },
]

SITE_FIXTURE = {
    "meta": {"build": {"commit": "abcdef1234", "subject": "test", "committed_at": "2026-07-09T00:00:00Z"}},
    "counts": {"commands": 0, "features": 0, "games": 0},
    "catalogue": [],
    "commands": [],
    "bot_changelog": [],
}


@pytest.fixture()
def client(tmp_path, monkeypatch):
    registry = tmp_path / "arcade.json"
    registry.write_text(json.dumps(ARCADE_FIXTURE), encoding="utf-8")
    monkeypatch.setattr(arcade, "ARCADE_JSON_PATH", registry)
    monkeypatch.setenv("TESTING_DB_PATH", str(tmp_path / "testing.sqlite3"))
    for var in ("SITE_PASSWORD", "ANTHROPIC_API_KEY", "TESTING_BOUNTY_CAP_USD"):
        monkeypatch.delenv(var, raising=False)
    testing.reset_rate_limits()
    testing_ai.reset_ai_state()
    ds.clear_cache()
    ds.prime_cache(SITE_FIXTURE)
    ds.set_client(ds.make_client())  # never actually hit (cache is warm)
    with TestClient(app_module.app) as c:
        yield c
    ds.clear_cache()


def _card_order(html: str, names: list[str]) -> list[str]:
    found = [(html.index(n), n) for n in names if n in html]
    return [n for _, n in sorted(found)]


def test_arcade_no_params_renders_all_games_in_registry_order(client):
    r = client.get("/arcade")
    assert r.status_code == 200
    order = _card_order(r.text, ["Alpha Quest", "Beta Blast", "Proto Pit"])
    assert order == ["Alpha Quest", "Beta Blast", "Proto Pit"]
    assert "3 of 3" in r.text


def test_arcade_maturity_filter(client):
    r = client.get("/arcade?maturity=playable")
    assert "Alpha Quest" in r.text
    assert "Beta Blast" not in r.text and "Proto Pit" not in r.text
    assert "1 of 3" in r.text


def test_arcade_combined_dims_are_anded(client):
    # maturity=beta AND availability=live -> nothing (Beta Blast is download)
    r = client.get("/arcade?maturity=beta&availability=live")
    assert "0 of 3" in r.text
    assert "no items match the active filters" in r.text
    # multi-select within a dim is OR
    r = client.get("/arcade?maturity=beta&maturity=playable")
    assert "2 of 3" in r.text


def test_arcade_search_hits_name_tagline_description(client):
    r = client.get("/arcade?q=blobs")  # description text of Beta Blast
    assert "Beta Blast" in r.text and "1 of 3" in r.text
    assert "Alpha Quest" not in r.text


def test_arcade_sorts(client):
    r = client.get("/arcade?sort=az")
    assert _card_order(r.text, ["Alpha Quest", "Beta Blast", "Proto Pit"]) == [
        "Alpha Quest", "Beta Blast", "Proto Pit"]
    # maturity sort: playable < beta < prototype
    r = client.get("/arcade?sort=maturity")
    assert _card_order(r.text, ["Alpha Quest", "Beta Blast", "Proto Pit"]) == [
        "Alpha Quest", "Beta Blast", "Proto Pit"]


def test_arcade_unknown_value_is_flagged_not_dropped(client):
    r = client.get("/arcade?maturity=bogus")
    assert r.status_code == 200
    assert "0 of 3" in r.text
    assert "unknown" in r.text  # the honest unknown-value pill
    assert "bogus" in r.text


# --------------------------------------------------------------------------
# /testing task catalog — type / status / payout / time dims
# --------------------------------------------------------------------------
def test_testing_no_params_shows_the_full_catalog(client):
    tasks = testing.load_tasks()
    r = client.get("/testing")
    assert r.status_code == 200
    assert f"{len(tasks)} of {len(tasks)}" in r.text
    for t in tasks:
        assert t["title"] in r.text


def test_testing_type_and_status_filters_combine(client):
    r = client.get("/testing?type=game-test")
    n = sum(1 for t in testing.load_tasks() if t["type"] == "game-test")
    assert f"{n} of" in r.text
    # every committed game-test task is coming-soon -> AND with status=open is empty
    r = client.get("/testing?type=game-test&status=open")
    assert "0 of" in r.text
    assert "no items match the active filters" in r.text


def test_testing_payout_and_time_buckets(client):
    tasks = testing.shaped_tasks()
    low = [t for t in tasks if testing.payout_bucket(t) == "<=10"]
    r = client.get("/testing?payout=%3C%3D10")
    assert f"{len(low)} of {len(tasks)}" in r.text
    for t in low:
        assert t["title"] in r.text
    quick = [t for t in tasks if testing.est_minutes_bucket(t) == "<=30"]
    r = client.get("/testing?time=%3C%3D30")
    assert f"{len(quick)} of {len(tasks)}" in r.text


def test_testing_sorts_payout_high_first_and_minutes_short_first(client):
    r = client.get("/testing?sort=payout")
    titles = [t["title"] for t in testing.load_tasks()]
    order = _card_order(r.text, titles)
    payouts = {t["title"]: float(t["payout_usd"]) for t in testing.load_tasks()}
    assert [payouts[t] for t in order] == sorted(
        (payouts[t] for t in order), reverse=True)
    r = client.get("/testing?sort=minutes")
    order = _card_order(r.text, titles)
    minutes = {t["title"]: int(t["est_minutes"]) for t in testing.load_tasks()}
    assert [minutes[t] for t in order] == sorted(minutes[t] for t in order)


def test_testing_search(client):
    tasks = testing.load_tasks()
    hits = [t for t in tasks
            if "walkthrough" in f"{t['title']} {t['brief']} {t['id']}".lower()]
    assert hits  # the committed catalog has a guided walkthrough
    r = client.get("/testing?q=walkthrough")
    assert f"{len(hits)} of {len(tasks)}" in r.text
    others = [t["title"] for t in tasks
              if t["type"] == "site-review"]
    assert all(t not in r.text for t in others)


# --------------------------------------------------------------------------
# /testing/owner submissions queue — status / task / date dims, auth intact
# --------------------------------------------------------------------------
def _claim(client, task_id, email, name="Tess Tester"):
    r = client.post(
        f"/testing/tasks/{task_id}/claim",
        data={"name": name, "email": email, "paypal_email": ""},
        headers=ORIGIN,
    )
    assert r.status_code == 200, r.text
    m = re.search(r"/testing/s/([A-Za-z0-9_-]+)", r.text)
    assert m
    return m.group(1)


def _submit(client, token, findings):
    r = client.post(
        f"/testing/s/{token}",
        data={
            "what_worked": "nav", "what_broke": "a 404", "confusing": "",
            "device_browser": "MacBook / Firefox", "severity": "minor",
            "findings": findings,
        },
        headers=ORIGIN,
    )
    assert r.status_code == 200, r.text


@pytest.fixture()
def owner_client(client, monkeypatch):
    monkeypatch.setenv("SITE_PASSWORD", PW)
    t1 = _claim(client, "site-review-botsite", "one@example.com")
    _submit(client, t1, "findings about the botsite")
    t2 = _claim(client, "site-review-dashboard", "two@example.com")
    _submit(client, t2, "findings about the dashboard")
    # approve submission #2 (the newest, id 2) so statuses differ
    r = client.post(
        "/testing/owner/submissions/2/approve", headers=ORIGIN, auth=("owner", PW)
    )
    assert r.status_code == 200
    return client


def test_owner_queue_filters_require_auth_exactly_as_before(owner_client):
    assert owner_client.get("/testing/owner?status=approved").status_code == 401
    assert owner_client.get(
        "/testing/owner?status=approved", auth=("owner", "wrong")
    ).status_code == 401


def test_owner_queue_no_params_shows_all_submissions_newest_first(owner_client):
    r = owner_client.get("/testing/owner", auth=("owner", PW))
    assert r.status_code == 200
    assert "2 of 2" in r.text
    # id-DESC store order preserved: submission #2 renders before #1
    assert r.text.index("submission #2") < r.text.index("submission #1")


def test_owner_queue_status_and_task_filters(owner_client):
    # NOTE: the claims/ledger tables below the queue keep listing everything
    # (they are separate surfaces) — assertions target the submission cards.
    r = owner_client.get("/testing/owner?status=approved", auth=("owner", PW))
    assert "1 of 2" in r.text
    assert "submission #2" in r.text and "submission #1" not in r.text
    r = owner_client.get(
        "/testing/owner?task=site-review-botsite", auth=("owner", PW)
    )
    assert "1 of 2" in r.text
    assert "submission #1" in r.text and "submission #2" not in r.text


def test_owner_queue_search_and_sort(owner_client):
    r = owner_client.get("/testing/owner?q=dashboard", auth=("owner", PW))
    assert "1 of 2" in r.text and "two@example.com" in r.text
    r = owner_client.get("/testing/owner?sort=oldest", auth=("owner", PW))
    assert r.text.index("submission #1") < r.text.index("submission #2")


def test_owner_queue_unknown_status_flagged_and_empty_state_honest(owner_client):
    r = owner_client.get("/testing/owner?status=nonsense", auth=("owner", PW))
    assert r.status_code == 200
    assert "0 of 2" in r.text
    assert "unknown" in r.text and "nonsense" in r.text
    assert "no items match the active filters" in r.text
