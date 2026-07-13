"""Tester-program tests (ORDER 018 PR1): catalog pages, claim + submission
flow, anti-abuse guards, owner queue auth/transitions, export, and the
payout module's dry-run safety. Network-free: the site feed is primed and
the SQLite store points at a per-test temp file."""

from __future__ import annotations

import inspect
import re

import pytest
from fastapi.testclient import TestClient

from botsite import app as app_module
from botsite import data_source as ds
from botsite import testing, testing_ai, testing_payouts, testing_store

# Browsers send Origin on form POSTs; the same-origin guard requires it (or
# Referer). TestClient's host is "testserver".
ORIGIN = {"Origin": "http://testserver"}
PW = "owner-pass"
OPEN_TASK = "site-review-botsite"  # payout 10, slots 3 (committed catalog)
TWO_SLOT_TASK = "site-review-control-plane-projects"  # payout 12, slots 2


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


def claim(client, task_id=OPEN_TASK, email="tester@example.com", name="Tess Tester"):
    r = client.post(
        f"/testing/tasks/{task_id}/claim",
        data={"name": name, "email": email, "paypal_email": ""},
        headers=ORIGIN,
    )
    assert r.status_code == 200, r.text
    m = re.search(r"/testing/s/([A-Za-z0-9_-]+)", r.text)
    assert m, "claim response must show the private submission link"
    return m.group(1)


def submit(client, token, findings="Found a broken link on /commands."):
    r = client.post(
        f"/testing/s/{token}",
        data={
            "what_worked": "Navigation was clear.",
            "what_broke": "One 404 link.",
            "confusing": "",
            "device_browser": "MacBook / Firefox",
            "severity": "minor",
            "findings": findings,
        },
        headers=ORIGIN,
    )
    return r


def owner_approve(client, submission_id=1):
    return client.post(
        f"/testing/owner/submissions/{submission_id}/approve",
        headers=ORIGIN,
        auth=("owner", PW),
    )


# --- public pages -----------------------------------------------------------

def test_landing_renders_catalog_and_bounty_cap(client):
    r = client.get("/testing")
    assert r.status_code == 200
    assert "Get paid to test" in r.text
    assert "Review the SuperBot public site" in r.text  # open, real task
    assert "Playtest Lumen Drift" in r.text  # coming-soon game
    assert "coming soon" in r.text
    assert "$200 program cap" in r.text  # visible total-open-bounty cap
    assert "claims are reviewed manually" in r.text.lower()


def test_landing_in_nav(client):
    r = client.get("/")
    assert 'href="/testing"' in r.text


def test_task_detail_renders_brief_payout_slots(client):
    r = client.get(f"/testing/tasks/{OPEN_TASK}")
    assert r.status_code == 200
    assert "$10 payout" in r.text
    assert "3 of 3 slots left" in r.text
    assert "search palette" in r.text  # the real brief text
    assert "no confirmation email is sent" in r.text.lower()


def test_task_detail_unknown_404(client):
    assert client.get("/testing/tasks/nope").status_code == 404


def test_coming_soon_task_has_no_claim_form_and_honest_note(client):
    r = client.get("/testing/tasks/game-test-lumen-drift")
    assert r.status_code == 200
    assert "Activates when the game deploys" in r.text
    assert 'action="/testing/tasks/game-test-lumen-drift/claim"' not in r.text


# --- claim flow --------------------------------------------------------------

def test_claim_creates_token_and_private_page(client):
    token = claim(client)
    r = client.get(f"/testing/s/{token}")
    assert r.status_code == 200
    assert "status: claimed" in r.text
    assert "File your report" in r.text


def test_claim_requires_same_origin(client):
    r = client.post(
        f"/testing/tasks/{OPEN_TASK}/claim",
        data={"name": "X", "email": "x@example.com"},
    )  # no Origin, no Referer
    assert r.status_code == 403
    r = client.post(
        f"/testing/tasks/{OPEN_TASK}/claim",
        data={"name": "X", "email": "x@example.com"},
        headers={"Origin": "https://evil.example"},
    )
    assert r.status_code == 403


def test_claim_referer_fallback_accepted(client):
    r = client.post(
        f"/testing/tasks/{OPEN_TASK}/claim",
        data={"name": "X", "email": "ref@example.com"},
        headers={"Referer": f"http://testserver/testing/tasks/{OPEN_TASK}"},
    )
    assert r.status_code == 200


def test_claim_validates_input(client):
    r = client.post(
        f"/testing/tasks/{OPEN_TASK}/claim",
        data={"name": "", "email": "not-an-email"},
        headers=ORIGIN,
    )
    assert r.status_code == 400


def test_claim_dup_email_rejected(client):
    claim(client, email="dup@example.com")
    r = client.post(
        f"/testing/tasks/{OPEN_TASK}/claim",
        data={"name": "Again", "email": "dup@example.com"},
        headers=ORIGIN,
    )
    assert r.status_code == 409
    assert "one claim per task per email" in r.text


def test_claim_on_coming_soon_task_rejected(client):
    r = client.post(
        "/testing/tasks/game-test-lumen-drift/claim",
        data={"name": "X", "email": "x@example.com"},
        headers=ORIGIN,
    )
    assert r.status_code == 409


def test_slot_exhaustion_auto_closes_task(client):
    claim(client, task_id=TWO_SLOT_TASK, email="a@example.com")
    claim(client, task_id=TWO_SLOT_TASK, email="b@example.com")
    r = client.post(
        f"/testing/tasks/{TWO_SLOT_TASK}/claim",
        data={"name": "C", "email": "c@example.com"},
        headers=ORIGIN,
    )
    assert r.status_code == 409
    detail = client.get(f"/testing/tasks/{TWO_SLOT_TASK}")
    assert "closed" in detail.text
    assert "0 of 2" not in detail.text  # slots line replaced by closed badge


def test_bounty_cap_enforced_at_claim_time(client, monkeypatch):
    monkeypatch.setenv("TESTING_BOUNTY_CAP_USD", "15")
    claim(client, email="first@example.com")  # $10 committed, $5 headroom
    r = client.post(
        f"/testing/tasks/{TWO_SLOT_TASK}/claim",  # $12 > $5 remaining
        data={"name": "X", "email": "second@example.com"},
        headers=ORIGIN,
    )
    assert r.status_code == 409
    assert "open-bounty cap" in r.text


# --- submission flow ----------------------------------------------------------

def test_submission_unknown_token_404(client):
    assert client.get("/testing/s/no-such-token").status_code == 404


def test_submission_flow_stores_and_locks(client):
    token = claim(client)
    r = submit(client, token)
    assert r.status_code == 200
    assert "Report received" in r.text
    assert "status: submitted" in r.text
    # stored, honestly echoed back
    assert "Found a broken link" in r.text
    # second submission on the same claim is refused
    r2 = submit(client, token, findings="again")
    assert r2.status_code == 409


def test_submission_requires_same_origin(client):
    token = claim(client)
    r = client.post(f"/testing/s/{token}", data={"findings": "x"})
    assert r.status_code == 403


def test_empty_submission_rejected(client):
    token = claim(client)
    r = client.post(
        f"/testing/s/{token}",
        data={"findings": "", "what_worked": "", "severity": "none"},
        headers=ORIGIN,
    )
    assert r.status_code == 400


def test_submission_page_says_review_is_manual_ai_later(client):
    token = claim(client)
    submit(client, token)
    r = client.get(f"/testing/s/{token}")
    assert "manual" in r.text
    assert "AI exit-review" in r.text  # PR2, stated honestly


# --- rate limiting -------------------------------------------------------------

def test_rate_limit_429_with_retry_after(client):
    path = f"/testing/tasks/{OPEN_TASK}/claim"
    for _ in range(testing.RATE_LIMIT_MAX):
        r = client.post(path, data={"name": "", "email": ""}, headers=ORIGIN)
        assert r.status_code == 400  # invalid input, but each attempt counts
    r = client.post(path, data={"name": "", "email": ""}, headers=ORIGIN)
    assert r.status_code == 429
    assert int(r.headers["Retry-After"]) >= 1


# --- owner queue ------------------------------------------------------------------

def test_owner_fails_closed_503_without_password(client):
    assert client.get("/testing/owner").status_code == 503


def test_owner_401_on_missing_or_wrong_password(client, monkeypatch):
    monkeypatch.setenv("SITE_PASSWORD", PW)
    assert client.get("/testing/owner").status_code == 401
    assert client.get("/testing/owner", auth=("owner", "wrong")).status_code == 401


def test_owner_queue_states_what_it_is(client, monkeypatch):
    """Clarity: the owner queue names itself (h1) and says what it does up front."""
    monkeypatch.setenv("SITE_PASSWORD", PW)
    r = client.get("/testing/owner", auth=("owner", PW))
    assert r.status_code == 200
    assert "<h1>Tester program — review queue</h1>" in r.text
    assert "review queue for paid tester submissions" in r.text
    assert "approve" in r.text.lower() and "mark paid" in r.text.lower()


def test_owner_queue_renders_with_ephemerality_warning(client, monkeypatch):
    monkeypatch.setenv("SITE_PASSWORD", PW)
    r = client.get("/testing/owner", auth=("owner", PW))
    assert r.status_code == 200
    assert "Ephemeral storage" in r.text
    assert "redeploy wipes it" in r.text
    assert "DRY-RUN" in r.text
    assert "kill switch: auto-pay OFF" in r.text
    assert "PAYPAL_CLIENT_ID" in r.text  # names only
    assert "paypal-payouts" in r.text


def test_owner_posts_require_origin_and_auth(client, monkeypatch):
    monkeypatch.setenv("SITE_PASSWORD", PW)
    token = claim(client)
    submit(client, token)
    # guard runs first: no Origin → 403 even unauthenticated
    assert client.post("/testing/owner/submissions/1/approve").status_code == 403
    # with origin but no auth → 401
    assert (
        client.post("/testing/owner/submissions/1/approve", headers=ORIGIN).status_code
        == 401
    )


def test_approve_writes_owed_ledger(client, monkeypatch):
    monkeypatch.setenv("SITE_PASSWORD", PW)
    token = claim(client)
    submit(client, token)
    r = owner_approve(client)
    assert r.status_code == 200
    assert "recorded as" in r.text and "OWED" in r.text
    totals = testing_store.ledger_totals()
    assert totals["owed"] == 10.0  # the task's payout
    assert totals["paid"] == 0.0
    entry = testing_store.ledger_entries()[0]
    assert "queued for owner" in entry["note"]
    assert "kill switch is OFF" in entry["note"]


def test_mark_paid_transitions_and_ledger(client, monkeypatch):
    monkeypatch.setenv("SITE_PASSWORD", PW)
    token = claim(client)
    submit(client, token)
    owner_approve(client)
    r = client.post(
        "/testing/owner/submissions/1/mark-paid", headers=ORIGIN, auth=("owner", PW)
    )
    assert r.status_code == 200
    assert testing_store.claim_by_token(token)["status"] == "paid"
    assert testing_store.ledger_totals()["paid"] == 10.0


def test_mark_paid_requires_approved_first(client, monkeypatch):
    monkeypatch.setenv("SITE_PASSWORD", PW)
    token = claim(client)
    submit(client, token)
    r = client.post(
        "/testing/owner/submissions/1/mark-paid", headers=ORIGIN, auth=("owner", PW)
    )
    assert r.status_code == 409
    assert testing_store.claim_by_token(token)["status"] == "submitted"


def test_reject_frees_the_slot(client, monkeypatch):
    monkeypatch.setenv("SITE_PASSWORD", PW)
    token = claim(client, task_id=TWO_SLOT_TASK, email="a@example.com")
    submit(client, token)
    assert testing_store.active_claim_count(TWO_SLOT_TASK) == 1
    r = client.post(
        "/testing/owner/submissions/1/reject", headers=ORIGIN, auth=("owner", PW)
    )
    assert r.status_code == 200
    assert testing_store.active_claim_count(TWO_SLOT_TASK) == 0
    assert "2 of 2 slots left" in client.get(f"/testing/tasks/{TWO_SLOT_TASK}").text


def test_export_json_dumps_everything(client, monkeypatch):
    monkeypatch.setenv("SITE_PASSWORD", PW)
    token = claim(client, email="export@example.com")
    submit(client, token)
    r = client.get("/testing/owner/export.json", auth=("owner", PW))
    assert r.status_code == 200
    body = r.json()
    assert set(body) >= {"claims", "submissions", "payout_ledger", "warning"}
    assert body["claims"][0]["email"] == "export@example.com"
    assert body["submissions"][0]["findings"].startswith("Found a broken link")
    assert "ephemeral" in body["warning"]


def test_export_requires_auth(client, monkeypatch):
    monkeypatch.setenv("SITE_PASSWORD", PW)
    assert client.get("/testing/owner/export.json").status_code == 401


# --- payout dry-run safety -------------------------------------------------------

def test_no_autopay_even_with_creds_and_kill_switch_on(client, monkeypatch):
    """The hard v1 guarantee: credentials + kill switch ON still cannot pay —
    the AI-review gate (degraded here: no API key) and the DRY_RUN constant
    both queue everything."""
    monkeypatch.setenv("SITE_PASSWORD", PW)
    monkeypatch.setenv("PAYPAL_CLIENT_ID", "test-id")
    monkeypatch.setenv("PAYPAL_CLIENT_SECRET", "test-secret")
    monkeypatch.setenv("TESTING_AUTOPAY_ENABLED", "true")
    token = claim(client)
    submit(client, token)
    owner_approve(client)
    totals = testing_store.ledger_totals()
    assert totals["paid"] == 0.0 and totals["owed"] == 10.0
    entry = testing_store.ledger_entries()[0]
    assert "no automated exit-review verdict" in entry["note"]
    assert "test-secret" not in entry["note"]  # values never logged


def test_decide_payout_always_queues_in_v1(client, monkeypatch):
    monkeypatch.setenv("PAYPAL_CLIENT_ID", "x")
    monkeypatch.setenv("PAYPAL_CLIENT_SECRET", "y")
    monkeypatch.setenv("TESTING_AUTOPAY_ENABLED", "true")
    claim_row = {"id": 1, "task_id": OPEN_TASK, "email": "t@example.com"}
    task = {"payout_usd": 10}
    decision = testing_payouts.decide_payout(claim_row, task)
    assert decision["action"] == "queue-owner"
    assert any("DRY-RUN" in r for r in decision["reasons"])


def test_adapter_execute_is_dry_run_only(client, monkeypatch):
    monkeypatch.setenv("PAYPAL_CLIENT_ID", "x")
    monkeypatch.setenv("PAYPAL_CLIENT_SECRET", "y")
    adapter = testing_payouts.get_adapter()
    assert adapter.configured()
    result = adapter.execute(
        claim={"id": 99, "task_id": OPEN_TASK, "email": "t@example.com"},
        amount_usd=10.0,
    )
    assert result["dry_run"] is True and result["ok"] is False
    entries = testing_store.ledger_entries()
    assert entries[0]["state"] == "dry-run"
    assert "no provider call executed" in entries[0]["note"]


def test_adapter_unconfigured_without_creds(client):
    assert testing_payouts.get_adapter().configured() is False
    assert testing_payouts.autopay_enabled() is False


def test_payout_module_has_no_http_client():
    """Structural pin: v1's payout module cannot talk to any provider —
    no HTTP library is even imported."""
    src = inspect.getsource(testing_payouts)
    for lib in ("httpx", "requests", "urllib", "aiohttp", "http.client"):
        assert lib not in src, f"payout module must not import {lib} in v1"
    assert testing_payouts.DRY_RUN is True


def test_per_payout_cap_reason(client):
    decision = testing_payouts.decide_payout(
        {"id": 1, "task_id": "t", "email": "e@example.com"},
        {"payout_usd": 25},  # above the $20 hard max
    )
    assert decision["action"] == "queue-owner"
    assert any("per-payout limit" in r for r in decision["reasons"])
