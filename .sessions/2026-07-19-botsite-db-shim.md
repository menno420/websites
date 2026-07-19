# 2026-07-19 — botsite dual-backend shim extraction + heartbeat true + CAPABILITIES wall fix

> **Status:** `complete`

- **📊 Model:** Opus 4.8 (family) · high effort · refactor + docs + heartbeat

**What this session is about:** the botsite dual-backend (SQLite⇄Postgres)
shim grew up twice — `submissions_store.py` inlines raw psycopg per function
while `testing_store.py` carries the generic `_Conn`/`_Row`/`_pg_row_factory`
plumbing — and the two files carry verbatim-duplicated `database_url()` /
`_is_postgres()`. This session pulls the shared surface into one module,
`botsite/_db.py`, so there is a single home for the shim; both stores re-import
their symbols so no public name moves. Alongside it, two truth-maintenance
fixes: the CAPABILITIES ledger still asserted a "no DATABASE_URL" wall that
ORDER 034 / #446 superseded, and the status heartbeat needed re-truing.

⚑ Self-initiated: no — coordinator-dispatched (shared-shim follow-up + truth maintenance).

## Close-out

**Evidence:**

- files touched this branch:
  - `botsite/_db.py` — new module (WITHIN the botsite package; imports nothing
    from routes/templates, holds no secret, imports no other service). The
    single home for the shared shim: the backend-selection helpers
    `database_url()` / `_is_postgres()`, plus the generic connection plumbing
    `_Row` / `_pg_row_factory` / `_Conn` relocated out of `testing_store.py`.
    Behavior-identical — the plumbing is moved verbatim, not rewritten.
  - `botsite/testing_store.py` — the relocated `_Conn`/`_Row`/`_pg_row_factory`
    and the duplicated `database_url()` / `_is_postgres()` are deleted and
    re-imported from `botsite/_db.py`, so every public name stays resolvable at
    its original module path (`testing_store.database_url`,
    `testing_store._Conn`, etc.).
  - `botsite/submissions_store.py` — drops its verbatim-duplicated
    `database_url()` / `_is_postgres()` and re-imports them from `_db`; its
    per-function raw-psycopg bodies are left as-is (see Session idea).
  - `docs/CAPABILITIES.md` — the stale "botsite carries no DATABASE_URL" wall
    (true only as of 2026-07-18) is annotated inline as superseded: botsite now
    carries a live Railway Postgres `DATABASE_URL` (owner-set 2026-07-19, proven
    by /submit persistence; PR #425, #446). History preserved, not deleted.
  - `control/status.md` — heartbeat re-trued to current neutral facts (botsite
    _db shim landing).
- verify: `DATABASE_URL="" python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — **2070 passed**, 0 failed (== baseline; the extraction is
  behavior-identical and every relocated symbol path resolves).
  `test_own_heartbeat` 5/5 after the status re-truing.
  `python3 bootstrap.py check --strict` green — the only red was the DESIGNED
  born-red HOLD on this card, released at this flip.
- git: branch `claude/botsite-db-shim`; commits `2b7dca7` (born-red card +
  claim), `0410958` (extract `_db.py` shim + CAPABILITIES wall fix),
  `052ed5e` (heartbeat true), + this flip. PR #447 (squash auto-merge).

**Judgment:**

- Decisions made: (1) `_db.py` is the single shared home, but the two stores
  re-import their symbols rather than being rewritten to call through the module
  path, so no public name moves and the diff stays behavior-identical and
  low-risk. (2) `submissions_store.py`'s per-function raw psycopg is left
  untouched this slice — the shared surface is `database_url()`/`_is_postgres()`
  plus the `_Conn` plumbing; routing submissions through `_Conn` is a separate,
  larger refactor (flagged below). (3) CAPABILITIES correction is annotate-as-
  superseded, not delete — the ledger keeps its history so the 2026-07-18 wall
  is still legible as a dated finding.
- Next session should pick up: route `submissions_store.py` through the new
  `_db._Conn` wrapper so both stores share the connection plumbing, not just the
  two selection helpers — retiring the inlined per-function psycopg for full DRY
  (see Session idea).

## 💡 Session idea

**Route `submissions_store.py` through `_db._Conn` for full DRY.** This slice
homed the shared shim in `botsite/_db.py`, but only `testing_store.py` actually
uses the `_Conn`/`_Row`/`_pg_row_factory` plumbing — `submissions_store.py`
still inlines raw psycopg per function (placeholder translation, `RETURNING id`,
sequence resync repeated by hand). A natural next slice is to migrate
`submissions_store`'s functions onto the same `_Conn` wrapper testing_store
uses, so the whole botsite dual-backend surface flows through one code path
instead of two — deleting the last copy of the hand-rolled Postgres handling
and making `_db.py` the shim in fact, not just in name.

## ⟲ Previous-session review

`.sessions/2026-07-18-release-drift-banner.md` (ORDER 033) landed a genuinely
outbound-free banner by baking cross-repo release tags into `review/data` at
build time and honestly decide-and-flagged the botsite-vs-review venue call for
owner veto; the one loose thread it names on itself — `pick_latest_tag`'s
all-tags fallback surfacing an unrelated tag as a shared repo's `live_tag` — is
covered by a test but still deserves the stricter repo-scoped filter it defers.
