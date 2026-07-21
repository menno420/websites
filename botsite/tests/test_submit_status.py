"""Tests for the submitter status lookup (S5).

/submit issues an opaque ``ref`` token on the stored row and surfaces it on the
thank-you screen; ``GET /submit/status/{ref}`` is a read-only public lookup that
returns the stored status string and nothing else, with an honest not-found for
unknown refs. Exercised through the SQLite backend (DATABASE_URL=sqlite:///...),
so these stay network-free — matching test_submit.py's fixture pattern exactly.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from botsite import app as app_module
from botsite import data_source as ds
from botsite import submissions_store
from botsite import testing

ORIGIN = {"Origin": "http://testserver"}
_SECRET_VARS = (
    "SITE_PASSWORD",
    "ANTHROPIC_API_KEY",
    "PAYPAL_CLIENT_ID",
    "PAYPAL_SECRET",
)


def _prime():
    testing.reset_rate_limits()
    ds.clear_cache()
    ds.prime_cache({})
    ds.set_client(ds.make_client())


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///" + str(tmp_path / "submissions.sqlite3"))
    for var in _SECRET_VARS:
        monkeypatch.delenv(var, raising=False)
    _prime()
    with TestClient(app_module.app) as c:
        yield c
    ds.clear_cache()


# --- store: create issues an opaque ref, reader looks status up by it --------

def test_create_submission_returns_opaque_ref(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///" + str(tmp_path / "s.sqlite3"))
    row = submissions_store.create_submission("feature", "Hello", "World")
    assert row is not None
    assert isinstance(row["ref"], str) and len(row["ref"]) >= 12  # token_urlsafe(12)
    # two submissions get distinct refs
    other = submissions_store.create_submission("bug", "Two", "Body")
    assert other["ref"] != row["ref"]


def test_status_by_ref_returns_stored_status(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///" + str(tmp_path / "s.sqlite3"))
    row = submissions_store.create_submission("feature", "Hello", "World")
    assert submissions_store.submission_status_by_ref(row["ref"]) == "pending"


def test_status_by_ref_unknown_returns_none(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///" + str(tmp_path / "s.sqlite3"))
    assert submissions_store.submission_status_by_ref("nope-not-a-real-ref") is None


def test_status_by_ref_none_when_not_live(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert submissions_store.is_live() is False
    assert submissions_store.submission_status_by_ref("anything") is None


# --- route: submit surfaces the ref; status route returns it ------------------

def test_submit_surfaces_ref_on_thank_you(client):
    r = client.post(
        "/submit",
        data={"kind": "feature", "title": "Dark mode", "body": "Please add a dark theme."},
        headers=ORIGIN,
    )
    assert r.status_code == 200
    ref = submissions_store.list_submissions()[0]["ref"]
    assert ref  # persisted
    assert ref in r.text  # shown on the thank-you screen
    assert "/submit/status/" + ref in r.text  # with the check-status link


def test_status_route_returns_stored_status(client):
    client.post(
        "/submit",
        data={"kind": "bug", "title": "Broken link", "body": "404 on /x"},
        headers=ORIGIN,
    )
    ref = submissions_store.list_submissions()[0]["ref"]
    r = client.get("/submit/status/" + ref)
    assert r.status_code == 200
    assert ref in r.text
    assert "pending" in r.text.lower()


def test_status_route_leaks_no_title_or_body(client):
    client.post(
        "/submit",
        data={"kind": "bug", "title": "SecretTitleXYZ", "body": "SecretBodyABC"},
        headers=ORIGIN,
    )
    ref = submissions_store.list_submissions()[0]["ref"]
    r = client.get("/submit/status/" + ref)
    assert r.status_code == 200
    assert "SecretTitleXYZ" not in r.text
    assert "SecretBodyABC" not in r.text


def test_status_route_unknown_ref_is_404(client):
    r = client.get("/submit/status/definitely-not-a-real-ref")
    assert r.status_code == 404
    assert "no submission found" in r.text.lower()


def test_status_route_not_found_when_not_live(monkeypatch):
    """Fail-soft: with no DATABASE_URL the store is not live, so every ref reads
    as not-found (404) — the page never leaks that the store is down vs unknown."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    for var in _SECRET_VARS:
        monkeypatch.delenv(var, raising=False)
    _prime()
    with TestClient(app_module.app) as c:
        r = c.get("/submit/status/anything")
    ds.clear_cache()
    assert r.status_code == 404
    assert "no submission found" in r.text.lower()
