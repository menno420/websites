"""Durable store for the public /submit intake (ORDER 034 / ASK-0004).

The public submissions intake persists to a real database when DATABASE_URL is
configured on the botsite service. The backend is chosen by the URL scheme:

  * ``postgres://`` / ``postgresql://`` -> PostgreSQL via psycopg (the production
    target once Railway provisions the superbot-websites Postgres, ASK-0004).
  * ``sqlite:///path`` or a bare path -> SQLite (tests and local runs).

When DATABASE_URL is unset the intake is NOT live: :func:`is_live` returns False
and the /submit handler honestly reports the intake is not yet wired, exactly as
before. CI stays green with no database present, and going live is a pure
provisioning step (set DATABASE_URL) rather than a code change.
"""
from __future__ import annotations

import secrets
import sqlite3
import time
from contextlib import closing
from typing import Any

# Shared botsite dual-backend shim — the single home for these helpers AND the
# generic connection plumbing (_Row / _pg_row_factory / _Conn), the same shim
# ``testing_store`` consumes. Re-imported here so ``submissions_store.database_url``
# / ``._is_postgres`` / ``._Row`` / ``._pg_row_factory`` / ``._Conn`` still
# resolve at this module path.
from ._db import database_url, _is_postgres, _Row, _pg_row_factory, _Conn

# Allowed submission kinds -- mirror the <select> in templates/submit.html.
KINDS = ("feature", "bug")

# ``ref`` is the opaque, unguessable lookup token issued at create time
# (``secrets.token_urlsafe``) — the ONLY handle the public status route accepts.
# It is deliberately NULLABLE: rows written before this column existed carry no
# ref, so a nullable add needs no data migration and the store stays fail-soft.
_SCHEMA_SQLITE = """
CREATE TABLE IF NOT EXISTS submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kind TEXT NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    ref TEXT,
    created_at TEXT NOT NULL
);
"""

_SCHEMA_PG = """
CREATE TABLE IF NOT EXISTS submissions (
    id BIGSERIAL PRIMARY KEY,
    kind TEXT NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    ref TEXT,
    created_at TEXT NOT NULL
);
"""


def is_live() -> bool:
    """True when a durable write target is configured."""
    return bool(database_url())


def _sqlite_path(url: str) -> str:
    for prefix in ("sqlite:///", "sqlite://"):
        if url.startswith(prefix):
            return url[len(prefix):]
    return url


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _connect() -> "_Conn":
    """Open the configured backend as a unified :class:`_Conn`.

    Mirrors ``testing_store._connect`` — the shared dual-backend shim — but
    resolves the SQLite path from ``DATABASE_URL`` (``sqlite:///…`` or a bare
    path) rather than a dedicated env knob, and creates the intake's own
    single-table schema. psycopg is imported lazily on the Postgres path only.
    """
    url = database_url()
    if _is_postgres(url):
        import psycopg  # lazy: only imported when a Postgres URL is configured

        raw = psycopg.connect(url, row_factory=_pg_row_factory)
        with raw.cursor() as cur:
            cur.execute(_SCHEMA_PG)  # psycopg has no executescript
            # Idempotent guard for tables created before ``ref`` existed;
            # Postgres supports ADD COLUMN IF NOT EXISTS natively.
            cur.execute("ALTER TABLE submissions ADD COLUMN IF NOT EXISTS ref TEXT")
        raw.commit()
        return _Conn(raw, "postgres")
    raw = sqlite3.connect(_sqlite_path(url))
    raw.row_factory = sqlite3.Row
    raw.executescript(_SCHEMA_SQLITE)  # existing idempotent path, unchanged
    # Idempotent guard for tables created before ``ref`` existed. SQLite has no
    # ADD COLUMN IF NOT EXISTS, so add-and-swallow: on a fresh DB the column is
    # already in CREATE TABLE and this raises "duplicate column name", caught.
    try:
        raw.execute("ALTER TABLE submissions ADD COLUMN ref TEXT")
        raw.commit()
    except sqlite3.OperationalError:
        pass
    return _Conn(raw, "sqlite")


def create_submission(kind: str, title: str, body: str) -> dict[str, Any] | None:
    """Persist one pending submission and return the stored row.

    Issues an opaque ``ref`` token (``secrets.token_urlsafe``) on the row — the
    unguessable handle the submitter uses to check status at
    ``/submit/status/{ref}``. Returns ``None`` when the intake is not live
    (DATABASE_URL unset).
    """
    if not is_live():
        return None
    ref = secrets.token_urlsafe(12)
    with closing(_connect()) as conn, conn:
        new_id = conn.insert_id(
            "INSERT INTO submissions (kind, title, body, ref, created_at)"
            " VALUES (?, ?, ?, ?, ?)",
            (kind, title, body, ref, _now()),
        )
        row = conn.execute(
            "SELECT id, kind, title, body, status, ref, created_at"
            " FROM submissions WHERE id = ?",
            (new_id,),
        ).fetchone()
    return dict(row)


def submission_status_by_ref(ref: str) -> str | None:
    """Public status lookup by opaque ref — returns the status string only.

    Privacy: this is the ONLY public read path into a submission and it exposes
    the status string and nothing else (never title/body). Returns ``None`` when
    the ref is unknown OR the intake is not live — the caller must treat both as
    an honest not-found and never leak which case it was.
    """
    if not is_live() or not ref:
        return None
    with closing(_connect()) as conn:
        row = conn.execute(
            "SELECT status FROM submissions WHERE ref = ?",
            (ref,),
        ).fetchone()
    return row["status"] if row is not None else None


def list_submissions(limit: int = 100) -> list[dict[str, Any]]:
    """Newest-first submissions for the owner moderation queue.

    Returns ``[]`` when the intake is not live.
    """
    if not is_live():
        return []
    with closing(_connect()) as conn:
        rows = conn.execute(
            "SELECT id, kind, title, body, status, ref, created_at"
            " FROM submissions ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]
