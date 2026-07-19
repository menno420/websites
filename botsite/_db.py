"""Shared dual-backend (SQLite⇄Postgres) shim for the botsite stores.

The single home for the small database plumbing that ``submissions_store.py``
and ``testing_store.py`` both need. Both stores pick their backend by the
``DATABASE_URL`` scheme:

  * ``postgres://`` / ``postgresql://`` -> PostgreSQL via psycopg (production).
  * unset / anything else -> SQLite (tests, local runs, CI).

Layering: this stays WITHIN the botsite package — it imports nothing from
routes or templates, holds no secret, and never imports another service's
package (app/, dashboard/, review/). psycopg is imported lazily by the
callers on the Postgres path only, never here.

Contents:

  * :func:`database_url` / :func:`_is_postgres` — the backend-selection
    helpers both stores share.
  * :class:`_Row` / :func:`_pg_row_factory` / :class:`_Conn` — the generic
    connection plumbing that presents the sqlite-flavoured surface the stores
    already use while hiding the Postgres differences (placeholder
    translation, ``RETURNING id``, serial-sequence resync). Currently used by
    ``testing_store.py``; homed here so the shim is genuinely shared.
"""

from __future__ import annotations

import os


def database_url() -> str:
    """Resolved per call so tests can monkeypatch the environment."""
    return os.environ.get("DATABASE_URL") or ""


def _is_postgres(url: str) -> bool:
    return url.startswith(("postgres://", "postgresql://"))


class _Row:
    """A minimal stand-in for ``sqlite3.Row`` used on the Postgres path.

    The store's readers rely on ALL of: keyed access ``row["col"]``,
    positional access ``row[0]``, ``dict(row)``, tuple-unpacking
    ``(n,) = row`` (which must yield VALUES, as sqlite3.Row does), and
    ``.keys()``. psycopg's default tuple rows do not; this wrapper does.
    """

    __slots__ = ("_cols", "_vals", "_map")

    def __init__(self, cols, vals):
        self._cols = list(cols)
        self._vals = list(vals)
        self._map = {c: v for c, v in zip(self._cols, self._vals)}

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._vals[key]
        return self._map[key]

    def __iter__(self):
        return iter(self._vals)  # unpacking yields VALUES, like sqlite3.Row

    def keys(self):
        return list(self._cols)

    def __len__(self):
        return len(self._vals)


def _pg_row_factory(cursor):
    """psycopg row factory returning :class:`_Row` objects."""
    cols = [d.name for d in cursor.description] if cursor.description else []

    def make(values):
        return _Row(cols, values)

    return make


class _Conn:
    """Unified connection wrapper over both backends.

    Presents the sqlite-flavoured surface the store already uses (``execute``
    returning a cursor, native-transaction context manager, ``close``) while
    hiding the Postgres differences: ``?``→``%s`` placeholder translation,
    ``RETURNING id`` for autoincrement inserts, and serial-sequence resync.
    """

    def __init__(self, raw, backend):
        self._raw = raw
        self.backend = backend  # "sqlite" | "postgres"

    def execute(self, sql, params=()):
        if self.backend == "postgres":
            sql = sql.replace("?", "%s")
        return self._raw.execute(sql, params)

    def insert_id(self, sql, params=()):
        """INSERT and return the new row's autoincrement id (both backends)."""
        if self.backend == "postgres":
            cur = self._raw.execute(sql.replace("?", "%s") + " RETURNING id", params)
            return cur.fetchone()[0]
        return self._raw.execute(sql, params).lastrowid

    def resync_sequences(self, tables):
        """After an id-preserving import, advance PG serial sequences past the
        inserted max id. No-op for SQLite (AUTOINCREMENT self-advances)."""
        if self.backend != "postgres":
            return
        for table in tables:
            self._raw.execute(
                f"SELECT setval(pg_get_serial_sequence('{table}', 'id'),"
                f" COALESCE((SELECT MAX(id) FROM {table}), 1),"
                f" (SELECT COUNT(*) FROM {table}) > 0)"
            )

    def close(self):
        self._raw.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if self.backend == "postgres":
            if exc_type is None:
                self._raw.commit()
            else:
                self._raw.rollback()
            return False
        return self._raw.__exit__(exc_type, exc, tb)  # sqlite native txn CM

    def __getattr__(self, name):
        # Safety net: delegate any unused sqlite-specific attr to the raw conn.
        return getattr(self._raw, name)
