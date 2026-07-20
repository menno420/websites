"""Backend-agnostic plumbing pins for submissions_store's dual backend.

``botsite/submissions_store.py`` selects PostgreSQL when ``DATABASE_URL`` is a
``postgres://`` URL and falls back to SQLite (``sqlite:///…`` or a bare path)
otherwise — now routed onto the SAME shared shim (``botsite/_db.py``:
``_Conn`` / ``_Row`` / ``_pg_row_factory``) that ``testing_store`` consumes,
rather than a second hand-rolled copy of the psycopg plumbing. CI has no live
Postgres, so — exactly like ``test_testing_store_backend.py`` — these exercise
ONLY the backend-agnostic plumbing: scheme detection, the ``_Row`` shim, SQLite
backend selection, the ``insert_id`` (``RETURNING id``) round-trip, the
sequence-resync no-op, and ``_SCHEMA_PG`` wellformedness. No psycopg connection
is ever opened; the suite stays network-free.
"""
from __future__ import annotations

import pytest

from botsite import submissions_store


@pytest.fixture()
def sqlite_db(tmp_path, monkeypatch):
    """Point the store at a fresh sqlite file via a ``sqlite:///`` DATABASE_URL."""
    monkeypatch.setenv(
        "DATABASE_URL", "sqlite:///" + str(tmp_path / "backend.sqlite3")
    )
    return tmp_path


# --- scheme detection --------------------------------------------------------

def test_is_postgres_true_for_pg_schemes():
    assert submissions_store._is_postgres("postgres://host/db")
    assert submissions_store._is_postgres("postgresql://host/db")


def test_is_postgres_false_otherwise():
    assert not submissions_store._is_postgres("")
    assert not submissions_store._is_postgres("sqlite:///x.db")
    assert not submissions_store._is_postgres("/path/to/file.db")


def test_database_url_reads_env(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert submissions_store.database_url() == ""
    monkeypatch.setenv("DATABASE_URL", "postgresql://unused/db")
    assert submissions_store.database_url() == "postgresql://unused/db"
    assert submissions_store._is_postgres(submissions_store.database_url())


# --- _Row: the sqlite3.Row stand-in (shared shim, resolvable at this path) ----

def test_row_keyed_and_positional_access():
    row = submissions_store._Row(["a", "b"], [1, 2])
    assert row["a"] == 1
    assert row["b"] == 2
    assert row[0] == 1
    assert row[1] == 2


def test_row_dict_and_keys():
    row = submissions_store._Row(["a", "b"], [1, 2])
    assert dict(row) == {"a": 1, "b": 2}
    assert row.keys() == ["a", "b"]


# --- backend selection -------------------------------------------------------

def test_connect_selects_sqlite_for_sqlite_url(sqlite_db):
    conn = submissions_store._connect()
    try:
        assert conn.backend == "sqlite"
    finally:
        conn.close()


def test_postgres_url_detected_without_connecting(monkeypatch):
    # A PG URL is DETECTED as postgres, but we never open a psycopg
    # connection (no live DB in CI) — assert on detection only.
    monkeypatch.setenv("DATABASE_URL", "postgresql://unused/db")
    assert submissions_store._is_postgres(submissions_store.database_url())


# --- insert_id (RETURNING id) round-trip + read-back via the shim -------------

def test_insert_id_returns_new_row_id_on_sqlite(sqlite_db):
    with submissions_store._connect() as conn:
        new_id = conn.insert_id(
            "INSERT INTO submissions (kind, title, body, created_at)"
            " VALUES (?, ?, ?, ?)",
            ("bug", "Direct insert", "via the shim", submissions_store._now()),
        )
        assert isinstance(new_id, int) and new_id >= 1
        row = conn.execute(
            "SELECT id, kind, title, body, status, created_at"
            " FROM submissions WHERE id = ?",
            (new_id,),
        ).fetchone()
    assert row["id"] == new_id
    assert row["title"] == "Direct insert"
    assert row["status"] == "pending"  # schema default preserved


def test_sqlite_backend_round_trips_through_public_api(sqlite_db):
    created = submissions_store.create_submission("feature", "Hello", "World")
    assert created is not None
    assert created["id"] >= 1
    assert created["kind"] == "feature"
    assert created["status"] == "pending"
    fetched = submissions_store.list_submissions()
    assert [r["title"] for r in fetched] == ["Hello"]
    assert fetched[0]["id"] == created["id"]


# --- sequence-resync path (shared shim; no-op on SQLite) ----------------------

def test_resync_sequences_is_noop_on_sqlite(sqlite_db):
    """SQLite AUTOINCREMENT self-advances, so the shared resync helper must be
    a harmless no-op — exercised here so submissions_store's SQLite path never
    trips it (parity with the Postgres import-resync it shares)."""
    with submissions_store._connect() as conn:
        conn.insert_id(
            "INSERT INTO submissions (kind, title, body, created_at)"
            " VALUES (?, ?, ?, ?)",
            ("bug", "t", "b", submissions_store._now()),
        )
        conn.resync_sequences(["submissions"])  # must not raise on SQLite
        (n,) = conn.execute("SELECT COUNT(*) FROM submissions").fetchone()
    assert int(n) == 1


# --- _SCHEMA_PG wellformedness -----------------------------------------------

def test_schema_pg_uses_postgres_types():
    assert "BIGSERIAL" in submissions_store._SCHEMA_PG


def test_schema_pg_drops_sqlite_only_types():
    assert "AUTOINCREMENT" not in submissions_store._SCHEMA_PG


def test_schema_pg_has_one_create_statement():
    stmts = [s for s in submissions_store._SCHEMA_PG.split(";") if s.strip()]
    assert len(stmts) == 1
    assert "CREATE TABLE IF NOT EXISTS submissions" in stmts[0]
