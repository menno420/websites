# 2026-07-14 — botsite: schema-drift pin for the import valve's hand-kept spec

> **Status:** `in-progress` — branch `claude/import-schema-pin-0714`; flips to
> `complete` + PR number as the deliberate LAST code step.

- **📊 Model:** Claude Fable 5 · worker · backlog-promotion slice

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

- (in progress)

⚑ Self-initiated: no — backlog promotion of the import-spec/schema drift
bullet captured by the #323 session.

## 💡 Session idea

(to be filled at close-out)

## ⟲ Previous-session review

(to be filled at close-out)
