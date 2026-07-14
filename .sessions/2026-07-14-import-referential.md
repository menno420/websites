# 2026-07-14 — referential pass on the testing-DB import valve: reject backups with orphan rows

> **Status:** `in-progress` — branch `claude/import-referential-0714`;
> a cross-table reference check in `_validated_import_rows` so a truncated
> or hand-edited backup whose rows reference missing targets 400s loudly
> instead of importing "successfully" and vanishing from the owner queue's
> INNER JOINs.

- **📊 Model:** Claude (Fable family) · worker · backlog promotion, validation-layer hardening

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

(in progress — filled at close-out)

⚑ Self-initiated: no — backlog promotion (the referential-pass bullet, captured
2026-07-14 by the testing-import-valve session).

## 💡 Session idea

(at close-out)

## ⟲ Previous-session review

(at close-out)
