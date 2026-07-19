# 2026-07-19 — botsite dual-backend shim extraction + heartbeat true + CAPABILITIES wall fix

> **Status:** `in-progress` — branch `claude/botsite-db-shim`; a three-part
> landing. **(Task 3)** extract the botsite dual-backend shim into a single
> shared home `botsite/_db.py`: the truly-shared helpers `database_url()` /
> `_is_postgres()` plus the generic connection plumbing (`_Conn`, `_Row`,
> `_pg_row_factory`) relocated out of `botsite/testing_store.py`, with both
> stores (`submissions_store.py`, `testing_store.py`) importing their shim
> symbols back so every public name stays resolvable at its original module
> path — behavior-identical, within the botsite package only (no cross-service
> import). **(Task 2)** correct the stale `docs/CAPABILITIES.md` wall that
> claimed "botsite carries no DATABASE_URL" (true only at 2026-07-18): botsite
> now carries a live Railway Postgres `DATABASE_URL` (owner-set 2026-07-19,
> proven by /submit persistence; PR #425, #446) — annotated inline as
> superseded, history preserved. **(Task 1)** true the `control/status.md`
> heartbeat to current neutral facts. Born red; flips to `complete` on green.

- **📊 Model:** [[fill:model-effort-role]]

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

[[fill:evidence — files touched, verify (test counts + bootstrap check), git commits]]

**Judgment:**

[[fill:judgment — decisions made, next session should pick up]]

## 💡 Session idea

[[fill:idea]]

## ⟲ Previous-session review

[[fill:prev-session-review]]
