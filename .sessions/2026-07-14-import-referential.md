# 2026-07-14 — referential pass on the testing-DB import valve: reject backups with orphan rows

> **Status:** `complete` — PR #323, branch `claude/import-referential-0714`;
> a cross-table reference check in `_validated_import_rows` so a truncated
> or hand-edited backup whose rows reference missing targets 400s loudly
> instead of importing "successfully" and vanishing from the owner queue's
> INNER JOINs.

- **📊 Model:** Claude (Fable family) · medium · feature build (backlog promotion, validation-layer hardening)

**What this session was about:** backlog promotion — the `docs/ideas/backlog.md`
bullet "Cross-table reference check on the testing-DB import valve — reject
backups with orphan rows" (captured 2026-07-14, testing-import-valve session 💡).
SQLite foreign keys are OFF by default (`PRAGMA foreign_keys` is never enabled
in `testing_store._connect()`), so orphan rows import silently through
`POST /testing/owner/import.json` (PR #320) and the owner queue's INNER JOINs
then drop them — a restore that reports ok but shows less than it inserted.
This session adds the referential pass in the validation layer (nothing is
written before the check) while preserving PR #320's legacy-backup tolerance.

## What was done

- `botsite/testing_store.py` — `_IMPORT_REFS`, the cross-table reference
  edges derived from the schema's `REFERENCES` clauses and the store's JOIN
  usage: `submissions.claim_id` / `guide_exchanges.claim_id` /
  `payout_ledger.claim_id` → claims, `ai_reviews.submission_id` /
  `screenshots.submission_id` → submissions. A referential pass at the end
  of `_validated_import_rows` requires each referencing row's FK to resolve
  among the UPLOADED rows of the target table (the import lands into an
  empty DB — the backup must be self-contained); orphans raise
  `ImportValidationError` (route → 400) naming the referencing table, the
  row id, the FK column, and the missing target table + id.
- Legacy tolerance (PR #320) preserved: a whole absent newer table means no
  referencing rows to check; every FK column is NOT NULL + `_REQUIRED` on
  import, so there is no nullable-reference case to wave through. Uploaded
  JSON is untrusted — a non-scalar value where an id belongs takes the loud
  400 path, never a `TypeError` 500 out of set membership.
- `botsite/tests/test_testing_import.py` — 8 new tests: one parametrized
  orphan per FK edge (400 + the detail names table / row id / FK column /
  missing target), a full backup with resolving references imports whole,
  a legacy-shape backup (absent newer tables) still imports, a non-scalar
  FK value is a 400 not a 500.
- `docs/ideas/backlog.md` — the referential-check bullet flipped to `built`
  (PR #323); this session's 💡 appended.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — 1389 passed, 1 warning (baseline 1381 + 8 new);
  `python3 bootstrap.py check --strict` — green once this card flipped
  complete (the only red during the session was this card's designed
  born-red hold).

⚑ Self-initiated: no — backlog promotion (the referential-pass bullet, captured
2026-07-14 by the testing-import-valve session).

## 💡 Session idea

**Pin `_IMPORT_SPEC`/`_IMPORT_REFS` against the live schema with a drift
test** — the import valve's field spec and now its reference-edge list are
hand-kept constants that mirror `_SCHEMA` by convention only: the next table
or FK column added to `_SCHEMA` imports as silently-absent (spec) or
silently-unchecked (refs), and nothing goes red — the exact hand-kept-list
drift class this repo has already been bitten by twice. A test that opens an
in-memory DB, walks `PRAGMA table_info` + `PRAGMA foreign_key_list` per
table, and asserts the derived column set and FK edges match the two
constants would make schema growth un-forgettable (the alternative — deriving
the constants from the pragmas at runtime — trades an explicit reviewable
spec for introspection magic; the drift TEST keeps the explicitness and adds
the tripwire). Worth having because this session hand-derived the edges from
`REFERENCES` clauses and JOIN grep — the derivation was manual exactly once
and should never need to be trusted manual again. Deduped against
`docs/ideas/backlog.md` + the queue-state NEXT list: no
import-spec/schema-drift/foreign_key_list bullet exists anywhere. Captured
in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

The md-relative-links session (PR #322) did well — it rewrote links on the
FINAL bleach-sanitized HTML so the sanitization pipeline stayed untouched,
and it deleted the smoke-crawl's `.md`-container carve-out so the browser
gate now guards its own fix; what it missed: its own 💡 concedes the failure
class moved rather than died — the rewriter can mint dead external GitHub
links no gate measures — and the proposed bounded sample-verify is still
unbuilt.
