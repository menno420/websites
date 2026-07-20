# 2026-07-19 — botsite: route submissions_store onto the shared _db._Conn shim

> **Status:** `complete` — branch `claude/submissions-store-shim`; routed
> `botsite/submissions_store.py` off its own inline per-function
> `psycopg.connect` onto the shared `botsite/_db.py` shim (`_Conn` / `_Row` /
> `_pg_row_factory`) that `testing_store.py` already consumes, behaviour-
> preserving. Born red; this flip to `complete` is the LAST step, releasing the
> `[session-card-hold]`.

- **📊 Model:** claude-opus-4-8 · medium · feature build

**What this session is about:** `botsite/_db.py` landed in #447 as the single
home for the botsite stores' dual-backend (SQLite⇄Postgres) plumbing —
`database_url()`/`_is_postgres()`, the `_Row`/`_pg_row_factory` `sqlite3.Row`
mirror, and the unified `_Conn` wrapper (`?`→`%s` translation, `insert_id()`
with `RETURNING id`, `resync_sequences()`, per-backend native-txn context
manager). `botsite/testing_store.py` already consumes the full shim. But
`botsite/submissions_store.py` — the durable store behind the public `/submit`
intake — still imported only `database_url, _is_postgres` and carried a SECOND
copy of the connection logic inline in each function: raw `psycopg.connect`,
hand-written `%s` placeholders, an inline `RETURNING …` clause, and its own
`sqlite3.connect` + `sqlite3.Row` setup, duplicated across
`create_submission` and `list_submissions`. Two copies of the same delicate
translation drift silently.

This session makes the shim genuinely shared: `submissions_store` now opens its
backend through a local `_connect()` that mirrors `testing_store._connect`
(psycopg with `row_factory=_pg_row_factory` on the Postgres path, `sqlite3`
with `sqlite3.Row` otherwise) and returns a `_Conn`; its two functions use
`conn.insert_id()` + `conn.execute()` + `dict(row)` exactly as testing_store
does. The one genuine difference from testing_store is preserved: submissions'
SQLite path resolves its file from `DATABASE_URL` (`sqlite:///…` or a bare
path via `_sqlite_path`), not a dedicated env knob, and it owns its own
single-table `_SCHEMA_SQLITE`/`_SCHEMA_PG`. Every public signature, the
`None`/`[]` not-live gates, and the returned row shape are byte-identical.
No `_db.py` change was needed — the existing shim already exported everything
submissions_store needs. Routes, CSRF, and the public behaviour of `/submit`
are untouched.

Work-ladder rung: coordinator-assigned build — plan slice 1 of
`docs/plans/next-cycle-2026-07-19.md` (make the shim real for both stores).

⚑ Self-initiated: no — coordinator-assigned slice.

## What was done

- `botsite/submissions_store.py` — imports `_Conn`/`_Row`/`_pg_row_factory`
  from `._db` (was: only `database_url`/`_is_postgres`). New `_connect()`
  returns a `_Conn` over either backend, mirroring `testing_store._connect`
  but resolving the SQLite file from `DATABASE_URL` via `_sqlite_path` and
  creating the intake's own `_SCHEMA_SQLITE`/`_SCHEMA_PG`. `create_submission`
  uses `conn.insert_id()` (`RETURNING id` on PG / `lastrowid` on SQLite) then
  reads the row back via the shim; `list_submissions` reads through the shim.
  The now-unused `_COLUMNS` zip helper and both inline `psycopg.connect`
  blocks are gone — the shim is the single owner of the translation. Public
  signatures, the not-live `None`/`[]` gates, and every returned row shape are
  preserved.
- `botsite/tests/test_submissions_store_backend.py` (new) — backend-agnostic
  plumbing pins mirroring `test_testing_store_backend.py` (no live PG in CI,
  same honest bar): scheme detection, `_Row` semantics via the module path,
  SQLite backend selection, the `insert_id`/`RETURNING id` round-trip and
  read-back through `_Conn`, the `resync_sequences` no-op on SQLite, and
  `_SCHEMA_PG` wellformedness.
- `control/claims/submissions-store-shim-2026-07-19.md` — work claim for this
  branch (deleted in the flip commit so it merges away with the PR).
- Verified (CI-equivalent, `DATABASE_URL` unset):
  `env -u DATABASE_URL python3 -m pytest tests/ botsite/tests dashboard/tests review/tests -q`
  → **2083 passed** (exit 0; 2070 baseline + 13 new backend pins);
  `python3 bootstrap.py check --strict` → the only gating finding was this
  card's born-red `[session-card-hold]`, released at this flip.

**Verify plan:** four-suite
(`env -u DATABASE_URL python3 -m pytest tests/ botsite/tests dashboard/tests review/tests -q`)
+ `python3 bootstrap.py check --strict` before the flip. The Postgres SQL path
itself is NOT exercised in CI (no live database — the same honest bar as
testing_store #447 and the original submissions_store #425); it is verified
live post-deploy, and the `/submit` intake is already confirmed writing to
Postgres in production (ASK-0004 satisfied), so this behaviour-preserving
re-route lands on an already-live path.

## 💡 Session idea

**A drift guard that fails CI when a botsite store reintroduces a raw
`psycopg.connect` or `sqlite3.connect` outside `_db.py`.** The whole point of
`_db.py` is one owner for the connection translation; nothing structural stops
a future store (or a careless edit to these two) from inlining a third copy
again — exactly the drift #447 + this slice just paid down. A ~15-line
`botsite/tests/test_store_shim_single_owner.py` that greps the store modules
for `psycopg.connect(`/`sqlite3.connect(` and asserts they appear ONLY in
`botsite/_db.py` (allowing each store's thin `_connect()` that resolves its
own path/schema, or asserting the raw connect calls live in `_db`) would make
the single-owner invariant executable instead of aspirational. Cheap,
test-only, and it turns "please keep using the shim" into a gate. Deduped
against `docs/ideas/backlog.md` + the NEXT list: not present. To capture in
`docs/ideas/backlog.md`.

## ⟲ Previous-session review

`.sessions/2026-07-19-testing-store-postgres.md` (#446, testing_store dual
backend) did the harder half of this two-step well: it ported the six-table
testing store onto the dual backend AND, in its 💡, correctly diagnosed that
its own `_Row`/`_Conn`/`_pg_row_factory` shim was a second near-identical copy
of submissions_store's — then that idea was actually landed as `_db.py` in
#447 rather than left in backlog, so the extraction happened instead of
rotting. The lesson this card carries forward: #447 extracted the shim but
only `testing_store` was migrated onto it in that PR, leaving submissions_store
still on its inline copy — a shared module with only one real consumer is only
half-shared, and the second consumer is where the "did the extraction actually
dedupe anything?" proof lives. This slice closes that gap so `_db.py` has two
real consumers and the dedupe is genuine; the follow-on lesson (captured in
this card's 💡) is to add the executable single-owner guard so the invariant
survives the next store.
