"""Backend-agnostic plumbing pins for testing_store's dual backend.

``botsite/testing_store.py`` selects PostgreSQL when ``DATABASE_URL`` is a
``postgres://`` URL and falls back to SQLite otherwise (mirroring
``botsite/submissions_store.py``). CI has no live Postgres, so — exactly like
submissions_store's tests — these exercise ONLY the backend-agnostic plumbing:
scheme detection, the ``_Row`` shim that stands in for ``sqlite3.Row`` on the
PG path, SQLite backend selection + round-trip, and ``_SCHEMA_PG``
wellformedness. No psycopg connection is ever opened; the suite stays
network-free.
"""
from __future__ import annotations

import pytest

from botsite import testing_store


@pytest.fixture()
def sqlite_db(tmp_path, monkeypatch):
    """Point the store at a fresh sqlite file and ensure no PG URL leaks in."""
    monkeypatch.setenv("TESTING_DB_PATH", str(tmp_path / "backend.sqlite3"))
    monkeypatch.delenv("DATABASE_URL", raising=False)
    return tmp_path


# --- scheme detection --------------------------------------------------------

def test_is_postgres_true_for_pg_schemes():
    assert testing_store._is_postgres("postgres://host/db")
    assert testing_store._is_postgres("postgresql://host/db")


def test_is_postgres_false_otherwise():
    assert not testing_store._is_postgres("")
    assert not testing_store._is_postgres("sqlite:///x.db")
    assert not testing_store._is_postgres("/path/to/file.db")


def test_database_url_reads_env(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert testing_store.database_url() == ""
    monkeypatch.setenv("DATABASE_URL", "postgresql://unused/db")
    assert testing_store.database_url() == "postgresql://unused/db"
    assert testing_store._is_postgres(testing_store.database_url())


# --- _Row: the sqlite3.Row stand-in ------------------------------------------

def test_row_keyed_and_positional_access():
    row = testing_store._Row(["a", "b"], [1, 2])
    assert row["a"] == 1
    assert row["b"] == 2
    assert row[0] == 1
    assert row[1] == 2


def test_row_dict_and_keys():
    row = testing_store._Row(["a", "b"], [1, 2])
    assert dict(row) == {"a": 1, "b": 2}
    assert row.keys() == ["a", "b"]


def test_row_unpacking_yields_values():
    (x,) = testing_store._Row(["n"], [5])
    assert x == 5
    a, b = testing_store._Row(["a", "b"], [10, 20])
    assert (a, b) == (10, 20)


def test_row_len():
    assert len(testing_store._Row(["a", "b", "c"], [1, 2, 3])) == 3


# --- backend selection + SQLite round-trip -----------------------------------

def test_connect_selects_sqlite_when_database_url_unset(sqlite_db):
    conn = testing_store._connect()
    try:
        assert conn.backend == "sqlite"
    finally:
        conn.close()


def test_connect_selects_sqlite_for_empty_database_url(sqlite_db, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "")
    conn = testing_store._connect()
    try:
        assert conn.backend == "sqlite"
    finally:
        conn.close()


def test_sqlite_backend_round_trips(sqlite_db):
    created = testing_store.create_claim(
        "site-review-botsite", "Ada", "ada@example.com", "", "tok-ada"
    )
    fetched = testing_store.claim_by_token("tok-ada")
    assert fetched is not None
    assert fetched["id"] == created["id"]
    assert fetched["email"] == "ada@example.com"
    assert fetched["status"] == "claimed"


def test_postgres_url_detected_without_connecting(sqlite_db, monkeypatch):
    # A PG URL is DETECTED as postgres, but we never open a psycopg
    # connection (no live DB in CI) — assert on detection only.
    monkeypatch.setenv("DATABASE_URL", "postgresql://unused/db")
    assert testing_store._is_postgres(testing_store.database_url())


# --- _SCHEMA_PG wellformedness -----------------------------------------------

def test_schema_pg_uses_postgres_types():
    assert "BIGSERIAL" in testing_store._SCHEMA_PG
    assert "BYTEA" in testing_store._SCHEMA_PG


def test_schema_pg_drops_sqlite_only_types():
    assert "AUTOINCREMENT" not in testing_store._SCHEMA_PG
    assert "BLOB" not in testing_store._SCHEMA_PG


def test_schema_pg_has_six_create_statements():
    stmts = [s for s in testing_store._SCHEMA_PG.split(";") if s.strip()]
    assert len(stmts) == 6
    assert all("CREATE TABLE IF NOT EXISTS" in s for s in stmts)
