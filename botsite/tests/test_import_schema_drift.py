"""Schema-drift pin: the import valve's hand-kept constants
(``_IMPORT_SPEC`` / ``_IMPORT_REFS`` / ``_IMPORT_ENUMS`` in
``botsite/testing_store.py``) mirror ``_SCHEMA`` by convention only — the
next table or FK column added to ``_SCHEMA`` would import as
silently-absent (spec) or silently-unchecked (refs) with nothing going
red. These tests derive the ACTUAL structure from a live in-memory DB
(``executescript(_SCHEMA)`` + ``PRAGMA table_info`` /
``PRAGMA foreign_key_list``) and assert exact two-way coverage against the
constants the import path itself uses, failing with the drifted
table/column/edge named. Deliberate spec↔schema differences are pinned
explicitly below, never silently skipped. Network-free, stdlib sqlite3
only."""

from __future__ import annotations

import sqlite3

import pytest

from botsite import testing_store

# Spec fields that DELIBERATELY differ from their schema column, pinned as
# {(table, spec_field): schema_column}. The one case: the export writes the
# screenshots blob as base64 text, so the import spec validates
# ``data_base64`` and ``_validated_import_rows`` decodes it into the
# ``data`` BLOB column at insert time. A new mismatch anywhere else is
# drift and must fail below, not grow this map casually.
RENAMED_SPEC_FIELDS: dict[tuple[str, str], str] = {
    ("screenshots", "data_base64"): "data",
}

# Reference edges the import checks that ``_SCHEMA`` does NOT declare as
# foreign keys, pinned as (referencing table, FK column, target table).
# The one case: ``payout_ledger.claim_id`` carries no REFERENCES clause in
# the schema, but the PR #323 referential pass validates it anyway — the
# stricter net is deliberate. If the schema later gains the REFERENCES
# clause, this pin must shrink in the same PR.
EXTRA_IMPORT_REFS: frozenset[tuple[str, str, str]] = frozenset(
    {("payout_ledger", "claim_id", "claims")}
)


@pytest.fixture()
def conn():
    """A live in-memory DB built from the real ``_SCHEMA`` — the actual
    structure is always derived, never hand-copied into this test."""
    conn = sqlite3.connect(":memory:")
    conn.executescript(testing_store._SCHEMA)
    yield conn
    conn.close()


def schema_tables(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master"
        " WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()
    return {r[0] for r in rows}


def schema_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}


def schema_fk_edges(conn: sqlite3.Connection) -> set[tuple[str, str, str, str]]:
    """Every declared FK edge as (child table, from-col, parent table, to-col).
    A ``None`` to-col (an implicit-PK reference) resolves to the parent's
    actual primary-key column rather than an assumed name."""
    edges: set[tuple[str, str, str, str]] = set()
    for table in schema_tables(conn):
        for row in conn.execute(f"PRAGMA foreign_key_list({table})"):
            parent, from_col, to_col = row[2], row[3], row[4]
            if to_col is None:
                pks = [r[1] for r in conn.execute(f"PRAGMA table_info({parent})") if r[5]]
                to_col = pks[0]
            edges.add((table, from_col, parent, to_col))
    return edges


def spec_columns(table: str) -> set[str]:
    """The import spec's field names for a table, mapped through the pinned
    renames so they are comparable to schema column names."""
    return {
        RENAMED_SPEC_FIELDS.get((table, field), field)
        for field, _default in testing_store._IMPORT_SPEC[table]
    }


# --- tables -------------------------------------------------------------------


def test_import_spec_tables_match_schema_tables(conn):
    """Every schema table is importable and the spec imports nothing
    phantom — a new table in ``_SCHEMA`` must land in ``_IMPORT_SPEC`` (or
    be pinned here as deliberately excluded; today nothing is)."""
    actual = schema_tables(conn)
    spec = set(testing_store._IMPORT_SPEC)
    missing = actual - spec
    phantom = spec - actual
    assert not missing and not phantom, (
        "_IMPORT_SPEC tables drifted from _SCHEMA —"
        f" in schema but NOT importable: {sorted(missing)};"
        f" in spec but NOT in schema: {sorted(phantom)}"
    )


# --- columns ------------------------------------------------------------------


def test_import_spec_columns_match_schema_columns(conn):
    """Per table, the spec's field set (through the pinned renames) equals
    the schema's column set exactly — a new column imports as
    silently-absent otherwise, and a removed one 500s at INSERT time."""
    drift: dict[str, str] = {}
    for table in sorted(schema_tables(conn) & set(testing_store._IMPORT_SPEC)):
        actual = schema_columns(conn, table)
        spec = spec_columns(table)
        missing = actual - spec
        phantom = spec - actual
        if missing or phantom:
            drift[table] = (
                f"in schema but NOT in _IMPORT_SPEC: {sorted(missing)};"
                f" in spec but NOT in schema: {sorted(phantom)}"
            )
    assert not drift, f"_IMPORT_SPEC columns drifted from _SCHEMA — {drift}"


def test_renamed_field_pin_is_honest(conn):
    """Each pinned rename names a real spec field and a real schema column,
    and the spec never ALSO carries the raw schema column (double coverage
    would mean the rename pin outlived its reason)."""
    for (table, spec_field), schema_col in RENAMED_SPEC_FIELDS.items():
        fields = {f for f, _d in testing_store._IMPORT_SPEC[table]}
        assert spec_field in fields, (
            f"pinned rename {table}.{spec_field!r} is not in _IMPORT_SPEC"
            " — stale rename pin"
        )
        assert schema_col in schema_columns(conn, table), (
            f"pinned rename target {table}.{schema_col!r} is not in _SCHEMA"
            " — stale rename pin"
        )
        assert schema_col not in fields, (
            f"{table} spec carries BOTH {spec_field!r} and {schema_col!r}"
            " — the rename pin no longer applies"
        )


# --- FK edges -----------------------------------------------------------------


def test_import_refs_match_schema_fk_edges(conn):
    """Every declared FK edge in ``_SCHEMA`` is checked by ``_IMPORT_REFS``,
    and every checked edge is either a declared FK or on the explicit
    ``EXTRA_IMPORT_REFS`` pin — SQLite FKs are off at runtime, so an
    unchecked edge admits orphans silently (the exact #323 failure class)."""
    actual4 = schema_fk_edges(conn)
    # The referential pass resolves references against the target rows'
    # ``id`` (testing_store._validated_import_rows) — a declared FK aimed
    # at any other column would be silently mischecked, so pin that too.
    non_id = {e for e in actual4 if e[3] != "id"}
    assert not non_id, (
        "FK edges targeting a non-id column — the import's referential pass"
        f" only resolves against target 'id': {sorted(non_id)}"
    )
    actual = {(child, from_col, parent) for child, from_col, parent, _to in actual4}
    refs = set(testing_store._IMPORT_REFS)
    unchecked = actual - refs
    assert not unchecked, (
        "FK edges declared in _SCHEMA but NOT checked by _IMPORT_REFS —"
        f" orphans on these edges would import silently: {sorted(unchecked)}"
    )
    extra = refs - actual
    assert extra == set(EXTRA_IMPORT_REFS), (
        "_IMPORT_REFS edges beyond the schema's declared FKs drifted from"
        " the EXTRA_IMPORT_REFS pin —"
        f" checked but neither declared nor pinned: {sorted(extra - EXTRA_IMPORT_REFS)};"
        f" pinned but no longer extra (schema gained the FK?):"
        f" {sorted(EXTRA_IMPORT_REFS - extra)}"
    )


def test_extra_ref_pin_names_real_columns(conn):
    """The pinned extra edges must still be REAL structure: referencing
    table + FK column and target table + ``id`` all exist in the schema."""
    tables = schema_tables(conn)
    for child, fk, target in sorted(EXTRA_IMPORT_REFS):
        assert child in tables and target in tables, (
            f"pinned extra edge ({child}, {fk!r}, {target}) names a table"
            " missing from _SCHEMA"
        )
        assert fk in schema_columns(conn, child), (
            f"pinned extra edge column {child}.{fk!r} is not in _SCHEMA"
        )
        assert "id" in schema_columns(conn, target), (
            f"pinned extra edge target {target} has no 'id' column"
        )


# --- enum columns -------------------------------------------------------------


def test_import_enums_name_real_spec_columns(conn):
    """``_IMPORT_ENUMS`` re-checks enum columns on import via ``row[field]``
    — a renamed column there would KeyError (a 500, not a 400), so each
    enum's table and column must exist in both the schema and the spec."""
    for table, (field, _allowed) in testing_store._IMPORT_ENUMS.items():
        assert table in schema_tables(conn), (
            f"_IMPORT_ENUMS table {table!r} is not in _SCHEMA"
        )
        assert field in schema_columns(conn, table), (
            f"_IMPORT_ENUMS column {table}.{field!r} is not in _SCHEMA"
        )
        assert field in {f for f, _d in testing_store._IMPORT_SPEC[table]}, (
            f"_IMPORT_ENUMS column {table}.{field!r} is not in _IMPORT_SPEC"
            " — the enum check would KeyError on import"
        )
