"""Owner-queue Drop-offs section: abandoned guided sessions surfaced.

Backlog promotion ("Abandoned guided sessions surfaced on the owner queue",
2026-07-13): a claim that chats with the AI guide but never submits leaves
persisted ``guide_exchanges`` rows (PR #292) that the submissions-only owner
queue could never show. Covers the ``abandoned_guided_claims()`` store
accessor (filters, fields, ordering) and the read-only "Drop-offs" section
on GET /testing/owner (rendered with count + transcript; submitted and
chat-free claims excluded). Network-free, same fixture as the guide suite.
The no-auth 401 pin for /testing/owner already lives in
``test_testing.py::test_owner_401_on_missing_or_wrong_password``.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from botsite import app as app_module
from botsite import data_source as ds
from botsite import testing, testing_ai, testing_store

PW = "owner-pass"
GUIDED_TASK = "walkthrough-botsite-first-visit"


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
        "TESTING_AI_GUIDE_CAP",
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


def make_claim(email, name="Wanda", task_id=GUIDED_TASK):
    """Store-level claim (status 'claimed'); token just has to be unique."""
    return testing_store.create_claim(
        task_id, name, email, "", f"token-{email}"
    )


def owner_page(client, monkeypatch):
    monkeypatch.setenv("SITE_PASSWORD", PW)
    r = client.get("/testing/owner", auth=("owner", PW))
    assert r.status_code == 200
    return r.text


# --- store accessor -----------------------------------------------------------

def test_accessor_returns_claim_fields_count_and_last_exchange(client):
    c = make_claim("walker@example.com")
    testing_store.add_guide_exchange(c["id"], 0, "Where do I start?", "Header.")
    testing_store.add_guide_exchange(c["id"], 2, "Toggle broken?", "Try it.")
    rows = testing_store.abandoned_guided_claims()
    assert len(rows) == 1
    row = rows[0]
    assert row["id"] == c["id"]
    assert row["task_id"] == GUIDED_TASK
    assert row["name"] == "Wanda"
    assert row["email"] == "walker@example.com"
    assert row["status"] == "claimed"
    assert row["exchange_count"] == 2
    transcript = testing_store.guide_transcript_for_claim(c["id"])
    assert row["last_exchange_at"] == transcript[-1]["created_at"]


def test_accessor_orders_by_last_exchange_desc(client, monkeypatch):
    early = make_claim("early@example.com", name="Early")
    late = make_claim("late@example.com", name="Late")
    # controlled clock: `late` claim's chat activity is the more recent
    monkeypatch.setattr(testing_store, "_now", lambda: "2026-07-13T10:00:00Z")
    testing_store.add_guide_exchange(early["id"], 0, "hello?", "hi")
    monkeypatch.setattr(testing_store, "_now", lambda: "2026-07-13T11:00:00Z")
    testing_store.add_guide_exchange(late["id"], 0, "anyone?", "yes")
    rows = testing_store.abandoned_guided_claims()
    assert [r["id"] for r in rows] == [late["id"], early["id"]]
    assert rows[0]["last_exchange_at"] == "2026-07-13T11:00:00Z"
    assert rows[1]["last_exchange_at"] == "2026-07-13T10:00:00Z"


def test_accessor_excludes_submitted_claims(client):
    c = make_claim("finisher@example.com")
    testing_store.add_guide_exchange(c["id"], 0, "How?", "Like this.")
    testing_store.create_submission(c["id"], {"q": "a"}, "found nothing")
    testing_store.set_claim_status(c["id"], "submitted")
    assert testing_store.abandoned_guided_claims() == []


def test_accessor_excludes_claims_without_exchanges(client):
    make_claim("silent@example.com")
    assert testing_store.abandoned_guided_claims() == []


def test_accessor_excludes_claimed_status_left_behind_by_a_submission_row(client):
    # belt + braces: even if a claim somehow kept status 'claimed' while a
    # submission row exists, the NOT EXISTS guard keeps it out of Drop-offs
    c = make_claim("racer@example.com")
    testing_store.add_guide_exchange(c["id"], 0, "hm", "ok")
    testing_store.create_submission(c["id"], {}, "")
    assert testing_store.abandoned_guided_claims() == []


# --- owner page rendering -------------------------------------------------------

def test_dropoff_renders_with_count_and_collapsed_transcript(client, monkeypatch):
    c = make_claim("walker@example.com")
    testing_store.add_guide_exchange(
        c["id"], 0, "Where is the search button?", "Check the header first."
    )
    testing_store.add_guide_exchange(
        c["id"], 2, "Is the toggle a bug?", "Try the theme toggle."
    )
    html = owner_page(client, monkeypatch)
    assert "Drop-offs — chatted with the guide, never submitted (1)" in html
    assert "claimed — never submitted" in html
    assert "Wanda · walker@example.com" in html
    assert GUIDED_TASK in html
    assert "2 exchange(s)" in html
    last = testing_store.abandoned_guided_claims()[0]["last_exchange_at"]
    assert f"last {last}" in html
    # transcript rides behind the same collapsed <details> pattern as #292
    assert "<details" in html
    assert "Where is the search button?" in html
    assert "Try the theme toggle." in html


def test_submitted_claim_never_shows_in_dropoffs(client, monkeypatch):
    c = make_claim("finisher@example.com", name="Fin")
    testing_store.add_guide_exchange(c["id"], 0, "How do I begin?", "Step one.")
    testing_store.create_submission(c["id"], {"step_1": "done"}, "all fine")
    testing_store.set_claim_status(c["id"], "submitted")
    html = owner_page(client, monkeypatch)
    assert "Drop-offs — chatted with the guide, never submitted (0)" in html
    assert "No drop-offs" in html
    # the transcript still shows — but on the submission card, not a drop-off
    assert "How do I begin?" in html


def test_chat_free_claim_never_shows_in_dropoffs(client, monkeypatch):
    make_claim("silent@example.com", name="Sil")
    html = owner_page(client, monkeypatch)
    assert "Drop-offs — chatted with the guide, never submitted (0)" in html
    assert "No drop-offs" in html
