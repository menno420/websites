"""Tests for the public /submit durable intake (ORDER 034 / ASK-0004).

The store is exercised through its SQLite backend (DATABASE_URL=sqlite:///...),
so these tests never require a live PostgreSQL and stay network-free.
"""
from __future__ import annotations

import base64

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


def test_submit_form_renders(client):
    r = client.get("/submit")
    assert r.status_code == 200
    assert 'action="/submit"' in r.text


def test_submit_persists_when_live(client):
    r = client.post(
        "/submit",
        data={"kind": "feature", "title": "Dark mode", "body": "Please add a dark theme."},
        headers=ORIGIN,
    )
    assert r.status_code == 200
    rows = submissions_store.list_submissions()
    assert len(rows) == 1
    assert rows[0]["title"] == "Dark mode"
    assert rows[0]["kind"] == "feature"
    assert rows[0]["status"] == "pending"


def test_submit_rejects_cross_origin(client):
    r = client.post("/submit", data={"kind": "bug", "title": "x", "body": "y"})
    assert r.status_code == 403
    assert submissions_store.list_submissions() == []


def test_submit_requires_title_and_body(client):
    r = client.post("/submit", data={"kind": "feature", "title": "", "body": ""}, headers=ORIGIN)
    assert r.status_code == 200
    assert submissions_store.list_submissions() == []


def test_submit_not_live_without_database_url(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    for var in _SECRET_VARS:
        monkeypatch.delenv(var, raising=False)
    _prime()
    with TestClient(app_module.app) as c:
        r = c.post("/submit", data={"kind": "bug", "title": "t", "body": "b"}, headers=ORIGIN)
    ds.clear_cache()
    assert r.status_code == 200
    assert submissions_store.is_live() is False


def test_queue_requires_owner(client):
    r = client.get("/submit/queue.json")
    assert r.status_code == 503  # SITE_PASSWORD unset -> owner queue fails closed


def test_queue_lists_submissions_for_owner(client, monkeypatch):
    monkeypatch.setenv("SITE_PASSWORD", "hunter2")
    client.post(
        "/submit",
        data={"kind": "bug", "title": "Broken link", "body": "404 on /x"},
        headers=ORIGIN,
    )
    token = base64.b64encode(b"owner:hunter2").decode()
    r = client.get("/submit/queue.json", headers={"Authorization": "Basic " + token})
    assert r.status_code == 200
    payload = r.json()
    assert payload["live"] is True
    assert any(s["title"] == "Broken link" for s in payload["submissions"])


def test_store_sqlite_roundtrip(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///" + str(tmp_path / "s.sqlite3"))
    assert submissions_store.is_live() is True
    row = submissions_store.create_submission("feature", "Hello", "World")
    assert row is not None
    assert row["id"] >= 1
    assert [r["title"] for r in submissions_store.list_submissions()] == ["Hello"]


def test_store_returns_none_when_not_live(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert submissions_store.is_live() is False
    assert submissions_store.create_submission("bug", "t", "b") is None
    assert submissions_store.list_submissions() == []


def test_submit_form_hides_stub_when_live(client):
    r = client.get("/submit")
    assert r.status_code == 200
    body = r.text.lower()
    assert "not wired" not in body
    assert "still being provisioned" not in body


def test_submit_form_shows_stub_when_not_live(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    for var in _SECRET_VARS:
        monkeypatch.delenv(var, raising=False)
    _prime()
    with TestClient(app_module.app) as c:
        r = c.get("/submit")
    ds.clear_cache()
    assert r.status_code == 200
    assert "not wired" in r.text.lower()
