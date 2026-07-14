"""Import-valve tests: POST /testing/owner/import.json restores a previously
downloaded export.json backup after a redeploy wiped the ephemeral SQLite
disk. Covers the auth gate (503 fail-closed / 401), the state-change guard
(same-origin), untrusted-input handling (shape 400s, size 413), the
replace-into-empty refusal semantics, and legacy backups missing columns
added after they were taken (``guide_exchanges.step_title`` et al.).
Network-free, same fixture pattern as test_testing.py."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from botsite import app as app_module
from botsite import data_source as ds
from botsite import testing, testing_ai, testing_store

ORIGIN = {"Origin": "http://testserver"}
EVIL_ORIGIN = {"Origin": "http://evil.example"}
PW = "owner-pass"
OPEN_TASK = "site-review-botsite"
IMPORT_PATH = "/testing/owner/import.json"


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("TESTING_DB_PATH", str(tmp_path / "testing.sqlite3"))
    for var in (
        "SITE_PASSWORD",
        "TESTING_AUTOPAY_ENABLED",
        "PAYPAL_CLIENT_ID",
        "PAYPAL_CLIENT_SECRET",
        "TESTING_BOUNTY_CAP_USD",
        "ANTHROPIC_API_KEY",  # no key in tests → degraded mode, zero network
        "TESTING_AI_MODEL",
        "TESTING_AI_DAILY_CAP",
        "TESTING_AUTOPAY_MIN_SCORE",
    ):
        monkeypatch.delenv(var, raising=False)
    testing.reset_rate_limits()
    testing_ai.reset_ai_state()
    ds.clear_cache()
    ds.prime_cache({})
    ds.set_client(ds.make_client())  # never actually hit (cache is warm)
    with TestClient(app_module.app) as c:
        yield c
    ds.clear_cache()


def minimal_backup() -> dict:
    """The smallest current-schema export: one claim, nothing else."""
    return {
        "claims": [
            {
                "id": 1,
                "task_id": OPEN_TASK,
                "name": "Tess Tester",
                "email": "restore@example.com",
                "paypal_email": "",
                "token": "restored-token",
                "status": "claimed",
                "created_at": "2026-07-01T00:00:00Z",
            }
        ],
        "submissions": [],
        "ai_reviews": [],
        "screenshots": [],
        "guide_exchanges": [],
        "payout_ledger": [],
    }


def post_import(client, payload, *, auth=("owner", PW), headers=ORIGIN, query=""):
    body = payload if isinstance(payload, (str, bytes)) else json.dumps(payload)
    return client.post(IMPORT_PATH + query, content=body, auth=auth, headers=headers)


# --- auth + guard gates -------------------------------------------------------


def test_import_fails_closed_503_without_password(client):
    r = client.post(IMPORT_PATH, content="{}", headers=ORIGIN)
    assert r.status_code == 503


def test_import_401_on_missing_or_wrong_password(client, monkeypatch):
    monkeypatch.setenv("SITE_PASSWORD", PW)
    assert client.post(IMPORT_PATH, content="{}", headers=ORIGIN).status_code == 401
    assert (
        post_import(client, minimal_backup(), auth=("owner", "wrong")).status_code
        == 401
    )


def test_import_rejects_cross_origin_and_headerless_posts(client, monkeypatch):
    monkeypatch.setenv("SITE_PASSWORD", PW)
    # wrong Origin → 403 even with valid credentials (basic auth is no CSRF defense)
    assert post_import(client, minimal_backup(), headers=EVIL_ORIGIN).status_code == 403
    # no Origin and no Referer → 403
    assert post_import(client, minimal_backup(), headers={}).status_code == 403
    # nothing was imported by the rejected attempts
    assert testing_store.list_claims() == []


# --- the restore round trip ----------------------------------------------------


def test_round_trip_export_then_import_after_wipe(client, tmp_path, monkeypatch):
    """Populate every table, export, point at a FRESH db file (the redeploy
    wipe), import the export — the queue's data is back, blobs included."""
    monkeypatch.setenv("SITE_PASSWORD", PW)
    r = client.post(
        f"/testing/tasks/{OPEN_TASK}/claim",
        data={"name": "Tess", "email": "rt@example.com", "paypal_email": ""},
        headers=ORIGIN,
    )
    assert r.status_code == 200
    import re

    token = re.search(r"/testing/s/([A-Za-z0-9_-]+)", r.text).group(1)
    r = client.post(
        f"/testing/s/{token}",
        data={
            "what_worked": "Nav.",
            "what_broke": "One 404.",
            "confusing": "",
            "device_browser": "Mac / Firefox",
            "severity": "minor",
            "findings": "Found a broken link.",
        },
        headers=ORIGIN,
    )
    assert r.status_code == 200  # also stores a degraded ai_review (no key)
    submission = testing_store.list_submissions()[0]
    testing_store.add_screenshot(submission["id"], "shot.png", "image/png", b"\x89PNGfake")
    claim_row = testing_store.claim_by_token(token)
    testing_store.add_guide_exchange(
        claim_row["id"], 2, "how do I open the palette?", "Press slash.",
        step_title="Open the search palette",
    )
    testing_store.add_ledger_entry(
        claim_row["id"], OPEN_TASK, "rt@example.com", 10.0, "owed", note="test"
    )
    backup = client.get("/testing/owner/export.json", auth=("owner", PW)).json()

    # the redeploy wipe: a brand-new empty DB file
    monkeypatch.setenv("TESTING_DB_PATH", str(tmp_path / "after-wipe.sqlite3"))
    assert testing_store.list_claims() == []

    r = post_import(client, backup)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] is True and body["replaced"] is False
    assert body["imported"] == {
        "claims": 1,
        "submissions": 1,
        "ai_reviews": 1,
        "screenshots": 1,
        "guide_exchanges": 1,
        "payout_ledger": 1,
    }
    restored = testing_store.claim_by_token(token)
    assert restored["email"] == "rt@example.com"
    assert restored["status"] == "submitted"
    sub = testing_store.submission_for_claim(restored["id"])
    assert sub["findings"] == "Found a broken link."
    assert testing_store.ai_review_for_submission(sub["id"])["status"] == "degraded"
    shot = testing_store.screenshot_by_id(1)
    assert shot["data"] == b"\x89PNGfake"  # base64 round trip, byte-exact
    exchange = testing_store.guide_transcript_for_claim(restored["id"])[0]
    assert exchange["step_title"] == "Open the search palette"
    assert testing_store.ledger_totals()["owed"] == 10.0


def test_legacy_backup_missing_newer_columns_imports_with_defaults(client, monkeypatch):
    """A backup taken before newer columns existed (no ``step_title`` on
    guide_exchanges, no ``paypal_email``/``status`` on claims, no
    ``answers_json`` on submissions) restores with the schema defaults —
    never invented values."""
    monkeypatch.setenv("SITE_PASSWORD", PW)
    legacy = {
        "claims": [
            {
                "id": 1,
                "task_id": OPEN_TASK,
                "name": "Old Tester",
                "email": "old@example.com",
                "token": "legacy-token",
                "created_at": "2026-06-01T00:00:00Z",
            }
        ],
        "submissions": [
            {"id": 1, "claim_id": 1, "created_at": "2026-06-01T01:00:00Z"}
        ],
        "guide_exchanges": [
            {
                "id": 1,
                "claim_id": 1,
                "step_index": 3,
                "message": "stuck here",
                "reply": "Try the menu.",
                "created_at": "2026-06-01T00:30:00Z",
            }
        ],
        # ai_reviews / screenshots / payout_ledger keys absent entirely —
        # tables that postdate the oldest exports import as empty.
    }
    r = post_import(client, legacy)
    assert r.status_code == 200, r.text
    claim_row = testing_store.claim_by_token("legacy-token")
    assert claim_row["paypal_email"] == ""
    assert claim_row["status"] == "claimed"
    sub = testing_store.submission_for_claim(1)
    assert sub["answers_json"] == "{}" and sub["findings"] == ""
    exchange = testing_store.guide_transcript_for_claim(1)[0]
    assert exchange["step_title"] == ""  # honest "no snapshot was taken"


# --- untrusted-input rejection ---------------------------------------------------


def test_malformed_bodies_are_400(client, monkeypatch):
    monkeypatch.setenv("SITE_PASSWORD", PW)
    # not JSON at all
    assert post_import(client, "this is not json").status_code == 400
    # JSON but not an object
    assert post_import(client, "[1, 2, 3]").status_code == 400
    # object without a claims list
    assert post_import(client, {"nope": True}).status_code == 400
    # a table that is not a list
    bad = minimal_backup()
    bad["submissions"] = {"id": 1}
    assert post_import(client, bad).status_code == 400
    # a record missing a required field
    bad = minimal_backup()
    del bad["claims"][0]["token"]
    r = post_import(client, bad)
    assert r.status_code == 400
    assert "token" in r.json()["detail"]
    # an unknown enum value
    bad = minimal_backup()
    bad["claims"][0]["status"] = "hacked"
    assert post_import(client, bad).status_code == 400
    # undecodable screenshot base64
    bad = minimal_backup()
    bad["screenshots"] = [
        {
            "id": 1,
            "submission_id": 1,
            "filename": "x.png",
            "content_type": "image/png",
            "data_base64": "!!! not base64 !!!",
            "created_at": "2026-07-01T00:00:00Z",
        }
    ]
    assert post_import(client, bad).status_code == 400
    # nothing was imported by any rejected attempt
    assert testing_store.list_claims() == []


def test_oversize_body_is_413(client, monkeypatch):
    monkeypatch.setenv("SITE_PASSWORD", PW)
    monkeypatch.setattr(testing, "IMPORT_MAX_BYTES", 1024)
    r = post_import(client, "x" * 2048)
    assert r.status_code == 413


# --- replace-into-empty semantics ------------------------------------------------


def test_non_empty_db_refused_without_flag_replaced_with_it(client, monkeypatch):
    monkeypatch.setenv("SITE_PASSWORD", PW)
    r = client.post(
        f"/testing/tasks/{OPEN_TASK}/claim",
        data={"name": "Live", "email": "live@example.com", "paypal_email": ""},
        headers=ORIGIN,
    )
    assert r.status_code == 200
    # without the flag: refused, live data untouched
    r = post_import(client, minimal_backup())
    assert r.status_code == 409
    assert "replace" in r.json()["detail"]
    assert testing_store.list_claims()[0]["email"] == "live@example.com"
    # with replace=1: wiped then restored
    r = post_import(client, minimal_backup(), query="?replace=1")
    assert r.status_code == 200, r.text
    assert r.json()["replaced"] is True
    claims = testing_store.list_claims()
    assert len(claims) == 1
    assert claims[0]["email"] == "restore@example.com"
