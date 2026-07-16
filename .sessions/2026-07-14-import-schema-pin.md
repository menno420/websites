# 2026-07-14 — botsite: schema-drift pin for the import valve's hand-kept spec

> **Status:** `complete` — PR #326, branch `claude/import-schema-pin-0714`;
> `_IMPORT_SPEC`/`_IMPORT_REFS`/`_IMPORT_ENUMS` can no longer silently trail
> `_SCHEMA` — a forgotten spec update now fails CI naming the drifted
> table/column/FK edge.

- **📊 Model:** Claude Fable 5 · medium · test writing (schema-drift pin, backlog-promotion slice)

**What this session was about:** backlog promotion — the captured bullet
"Pin `_IMPORT_SPEC`/`_IMPORT_REFS` against the live schema with a drift
test" (`docs/ideas/backlog.md`, captured 2026-07-14 by the
import-referential session, source card
`.sessions/2026-07-14-import-referential.md`). The import valve's field
spec and reference-edge list in `botsite/testing_store.py` are hand-kept
constants that mirror `_SCHEMA` by convention only; this session adds the
test that derives the actual tables/columns/FK edges from a live in-memory
DB (`PRAGMA table_info` + `PRAGMA foreign_key_list`) and asserts exact
two-way coverage against the constants, naming any drift.

## What was done

- `botsite/tests/test_import_schema_drift.py` — 6 network-free tests. An
  in-memory DB runs the real `_SCHEMA`; tables derive from `sqlite_master`
  (excluding `sqlite_%` internals), columns from `PRAGMA table_info`, FK
  edges from `PRAGMA foreign_key_list` (implicit-PK references resolved to
  the parent's real PK). The spec side imports the constants the import
  path itself uses — never re-keyed copies. Exact two-way coverage: every
  actual table/column/declared-FK edge must be in the spec AND the spec
  may reference nothing absent from the schema; failures print the named
  set differences. Deliberate gaps pinned explicitly, never skipped:
  `screenshots.data_base64`→`data` (rename pin with staleness checks) and
  the undeclared `payout_ledger.claim_id`→claims edge #323 checks anyway
  (extra-refs pin that must shrink if the schema gains the REFERENCES
  clause). Plus: every declared FK must target `id` (the referential pass
  resolves against target `id` only), and `_IMPORT_ENUMS` columns must
  exist in schema AND spec (a rename there is a 500, not a 400).
- Drift-catch proven live: a seeded throwaway
  `guide_exchanges.drift_probe_id … REFERENCES submissions(id)` column
  (local only, never committed) failed 2 tests naming exactly
  `['drift_probe_id']` and the edge
  `('guide_exchanges', 'drift_probe_id', 'submissions')`.
- `docs/ideas/backlog.md`: source bullet flipped to `built`; this
  session's 💡 captured as a new bullet.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — 1395 passed, 1 warning (+6 over main's 1389);
  `python3 bootstrap.py check --strict` — exit 0 (the only red being this
  card's own designed born-red HOLD, flipped by this commit).

⚑ Self-initiated: no — backlog promotion of the import-spec/schema drift
bullet captured by the #323 session.

## 💡 Session idea

**Export→import→export deep-equality round-trip pin** — populate every
table, run `export_all()`, import it into a fresh DB via `import_all()`,
re-export, and assert the two exports are deeply equal (ids, values,
base64 blobs — everything). Worth having because the existing round-trip
test only spot-checks fields someone remembered to assert, while this pin
plus the schema-drift pin makes every current AND future column
value-fidelity-checked for free — the drift pin proves the spec covers the
schema, deep equality proves the covered values survive the trip. Deduped
against `docs/ideas/backlog.md` + the queue-state NEXT list: the import
bullets there are the valve (#320), the referential pass (#323), and this
session's spec pin; nothing asserts export/import round-trip equality.
Captured in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

The venture-vetting-catalog session (PR #248) did well — 22 entries
curated with every status derived from the packet's own blockquote and
pinned to venture-lab @ `2c039e3`, plus a registry-honesty pin test; what
it missed: its own capture (the catalog sha-drift nag) is still unbuilt,
so the hand-curated registry's decay clock runs with no alarm attached.
