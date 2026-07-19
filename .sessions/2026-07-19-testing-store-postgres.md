# 2026-07-19 — botsite /testing store: SQLite→Postgres dual backend

> **Status:** `complete` — branch `claude/testing-store-postgres`; porting
> `botsite/testing_store.py` to a DATABASE_URL-keyed dual backend (Postgres in
> prod, SQLite fallback in CI/dev), mirroring the already-landed
> `botsite/submissions_store.py` pattern. Born red; this card holds the PR red
> until the deliberate flip to `complete` as the LAST step.

- **📊 Model:** Claude Opus family · high · feature build

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

- `botsite/testing_store.py` (+232/−16) — dual backend keyed on
  `DATABASE_URL`. `database_url()`/`_is_postgres()` dispatch, read per call
  (`postgres://`/`postgresql://` → PostgreSQL via lazily-imported `psycopg`;
  anything else → SQLite at `TESTING_DB_PATH`). A `_Row` shim mirrors
  `sqlite3.Row` (keyed + positional access, `dict()`, tuple-unpacking,
  `.keys()`, `len`) for the psycopg path, built by `_pg_row_factory`. A unified
  `_Conn` wrapper serves both backends: `?`→`%s` translation, `insert_id()`
  (`RETURNING id` on PG / `lastrowid` on SQLite), `resync_sequences()` to
  advance BIGSERIAL past an id-preserving import, and a native-txn context
  manager per backend. `_SCHEMA_PG` translates the DDL
  (BIGSERIAL/BYTEA/DOUBLE PRECISION; FK `REFERENCES` omitted to preserve the
  module's FK-off DELETE/INSERT order), executed statement-by-statement by
  `_create_schema_pg` (psycopg has no `executescript`). The 5
  insert-then-lastrowid sites use `conn.insert_id()`; `import_all` resyncs PG
  sequences after the id-preserving inserts. Every SQLite `_SCHEMA` and code
  path is byte-unchanged.
- `botsite/tests/test_testing_store_backend.py` (+127, new) — backend-agnostic
  plumbing only (no live PG in CI, same bar as submissions_store #425): scheme
  detection, `_Row` semantics, SQLite selection + round-trip, `_SCHEMA_PG`
  wellformedness.
- `control/claims/testing-store-postgres.md` — work claim for this branch
  (deleted in this flip commit so it merges away with the PR).
- Verified (CI-equivalent, `DATABASE_URL` unset):
  `python3 -m pytest tests/ botsite/tests dashboard/tests review/tests -q` →
  **2043 passed** (exit 0); `python3 bootstrap.py check --strict` → green once
  this card flips `complete` (the born-red `[session-card-hold]` was the only
  gating finding, released at this flip).

**Verify plan:** four-suite
(`python3 -m pytest tests/ botsite/tests dashboard/tests review/tests -q`) +
`python3 bootstrap.py check --strict` before flip. The Postgres SQL path itself
is NOT exercised in CI (no live database — same honest bar as submissions_store
#425); it is verified live post-deploy once `DATABASE_URL` is set on the
botsite service.

## 💡 Session idea

**Extract the duplicated dual-backend primitives into one shared module.**
`botsite/submissions_store.py` and now `botsite/testing_store.py` each carry
their own near-identical ~60-line shim — `database_url()`/`_is_postgres()`, the
`_Row`/`_pg_row_factory` sqlite3.Row mirror, and the `_Conn` wrapper
(`?`→`%s`, `insert_id`, `resync_sequences`). Worth doing because two copies of
the same delicate translation logic will drift silently: a fix to one (say a
`LIKE`/`%`-hardening of the `?`→`%s` translator) won't reach the other. Extract
into a small shared `botsite/_db.py` (or a vendored copy behind a drift guard
like `listfilter.py`) so both stores consume one implementation. Deduped
against `docs/ideas/backlog.md` + the NEXT list: not present. Captured in
`docs/ideas/backlog.md`.

## ⟲ Previous-session review

`.sessions/2026-07-18-wire-bake-pat.md` (ASK-0008, PR #434) did the minimal
thing well: it flipped exactly one `GH_TOKEN` line to
`${{ secrets.BAKE_PAT || secrets.GITHUB_TOKEN }}`, deliberately left the bake
step's own `GITHUB_TOKEN` untouched, and made the `|| secrets.GITHUB_TOKEN`
fallback load-bearing so a missing/expired secret degrades to today's behavior
rather than breaking the workflow — a genuinely careful blast-radius call. One
workflow improvement it surfaces: its own 💡 correctly diagnosed that the silent
fallback is *invisible* (a reverted secret would quietly resume the blocked-PR
behavior with no signal), yet the one-line `$GITHUB_STEP_SUMMARY` visibility
fix was only filed to `docs/ideas/backlog.md`, not landed in the same PR — so
the change shipped with its own observability gap still open. The lesson this
card carries forward: when a change's only safety net is a *silent* fallback,
land the one-line "which path did we take" signal in the same PR rather than
deferring the visibility to backlog.
