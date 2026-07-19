# 2026-07-19 — botsite /testing store: SQLite→Postgres dual backend

> **Status:** `in-progress` — branch `claude/testing-store-postgres`; porting
> `botsite/testing_store.py` to a DATABASE_URL-keyed dual backend (Postgres in
> prod, SQLite fallback in CI/dev), mirroring the already-landed
> `botsite/submissions_store.py` pattern. Born red; this card holds the PR red
> until the deliberate flip to `complete` as the LAST step.

- **📊 Model:** [[fill: model line resolved at flip]]

**What this session is about:** The tester program's state (claims,
submissions, AI exit-reviews, screenshots, guide-chat transcripts, payout
ledger) lives in `botsite/testing_store.py`, today a stdlib `sqlite3` file on
the botsite service's local disk. Railway's disk is ephemeral: every redeploy
wipes it, so the module ships with a loud warning banner and a JSON
export/import backup valve as the only mitigation. The durable fix — long an
open owner ask — is a real database keyed off `DATABASE_URL`. Its sibling
`botsite/submissions_store.py` already landed exactly this pattern for the
public /submit intake: read `DATABASE_URL` per call, dispatch on the URL
scheme (`postgres://`/`postgresql://` → PostgreSQL via a lazily-imported
`psycopg`; anything else → SQLite), so production persists to Postgres while CI
and local dev stay on SQLite with no live database present.

This session brings `testing_store.py` onto the same rails without changing any
SQLite behavior. The Postgres path is selected only when `DATABASE_URL` is a
`postgres://`/`postgresql://` URL; otherwise the module falls back to SQLite at
`TESTING_DB_PATH` exactly as before (fail-soft, matching submissions_store).
The port is mechanical but has real surface: the store's row objects rely on
`sqlite3.Row`'s dual positional+keyed access, `dict(row)`, tuple-unpacking and
`.keys()`, so a `_Row` shim mirrors all of that for the Postgres path; a
unified `_Conn` wrapper serves both backends (translating `?`→`%s`, appending
`RETURNING id` for inserts, resyncing PG sequences after an id-preserving
import); and a `_SCHEMA_PG` translates the SQLite DDL (BIGSERIAL/BYTEA/DOUBLE
PRECISION, FK-clauses omitted to preserve the module's FK-off behavior). CI has
no live Postgres, so the new tests exercise the backend-agnostic plumbing only,
exactly as submissions_store's tests do.

Work-ladder rung: coordinator-assigned build — durable tester-queue data
(DATABASE_URL Postgres, SQLite fallback in CI/dev).

⚑ Self-initiated: no — coordinator-assigned slice.

## What was done

[[fill: resolved at flip — file-by-file summary + verification counts]]

**Verify plan:** four-suite
(`python3 -m pytest tests/ botsite/tests dashboard/tests review/tests -q`) +
`python3 bootstrap.py check --strict` before flip. The Postgres SQL path itself
is NOT exercised in CI (no live database — same honest bar as submissions_store
#425); it is verified live post-deploy once `DATABASE_URL` is set on the
botsite service.

## 💡 Session idea

[[fill: session idea resolved at flip]]

## ⟲ Previous-session review

[[fill: previous-session review resolved at flip]]
