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

import sqlite3
import time
from contextlib import closing
from typing import Any

# Shared botsite dual-backend shim — the single home for these helpers
# (re-imported here so ``submissions_store.database_url`` /
# ``submissions_store._is_postgres`` still resolve at this module path).
from ._db import database_url, _is_postgres

# Allowed submission kinds -- mirror the <select> in templates/submit.html.
KINDS = ("feature", "bug")

_COLUMNS = ("id", "kind", "title", "body", "status", "created_at")

_SCHEMA_SQLITE = """
CREATE TABLE IF NOT EXISTS submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kind TEXT NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
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


def create_submission(kind: str, title: str, body: str) -> dict[str, Any] | None:
    """Persist one pending submission and return the stored row.

    Returns ``None`` when the intake is not live (DATABASE_URL unset).
    """
    if not is_live():
        return None
    url = database_url()
    created = _now()
    if _is_postgres(url):
        import psycopg  # lazy: only imported when a Postgres URL is configured

        with closing(psycopg.connect(url)) as conn:
            with conn.cursor() as cur:
                cur.execute(_SCHEMA_PG)
                cur.execute(
                    "INSERT INTO submissions (kind, title, body, created_at)"
                    " VALUES (%s, %s, %s, %s)"
                    " RETURNING id, kind, title, body, status, created_at",
                    (kind, title, body, created),
                )
                row = cur.fetchone()
            conn.commit()
        return dict(zip(_COLUMNS, row))
    with closing(sqlite3.connect(_sqlite_path(url))) as conn:
        conn.row_factory = sqlite3.Row
        conn.executescript(_SCHEMA_SQLITE)
        with conn:
            cur = conn.execute(
                "INSERT INTO submissions (kind, title, body, created_at)"
                " VALUES (?, ?, ?, ?)",
                (kind, title, body, created),
            )
            row = conn.execute(
                "SELECT id, kind, title, body, status, created_at"
                " FROM submissions WHERE id = ?",
                (cur.lastrowid,),
            ).fetchone()
    return dict(row)


def list_submissions(limit: int = 100) -> list[dict[str, Any]]:
    """Newest-first submissions for the owner moderation queue.

    Returns ``[]`` when the intake is not live.
    """
    if not is_live():
        return []
    url = database_url()
    if _is_postgres(url):
        import psycopg

        with closing(psycopg.connect(url)) as conn:
            with conn.cursor() as cur:
                cur.execute(_SCHEMA_PG)
                cur.execute(
                    "SELECT id, kind, title, body, status, created_at"
                    " FROM submissions ORDER BY id DESC LIMIT %s",
                    (limit,),
                )
                rows = cur.fetchall()
            conn.commit()
        return [dict(zip(_COLUMNS, r)) for r in rows]
    with closing(sqlite3.connect(_sqlite_path(url))) as conn:
        conn.row_factory = sqlite3.Row
        conn.executescript(_SCHEMA_SQLITE)
        rows = conn.execute(
            "SELECT id, kind, title, body, status, created_at"
            " FROM submissions ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]
