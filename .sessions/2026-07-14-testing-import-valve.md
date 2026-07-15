# 2026-07-14 — testing-DB import valve: restore export.json after a redeploy wipe

> **Status:** `complete` — PR #320, branch `claude/testing-import-valve-0714`;
> the export valve's missing other half: `POST /testing/owner/import.json`
> restores a previously downloaded export.json backup after Railway's
> ephemeral disk wiped the tester-program SQLite DB.

- **📊 Model:** Claude Fable 5 · medium · feature build (owner-route build + restore semantics)

**What this session was about:** backlog promotion — the `docs/ideas/backlog.md`
bullet "Import valve for the testing-DB export — restore `export.json` after a
redeploy wipe" (captured 2026-07-13, step-provenance session 💡). The export
valve (`GET /testing/owner/export.json`) is half a lifeboat: the backup can be
pulled before a redeploy but nothing can put it BACK. This session builds the
owner-auth import counterpart with honest `.get`-default handling for legacy
backups lacking newer columns (`step_title` et al.).

## What was done

- `botsite/testing_store.py` — `import_all(payload, replace=False)`: validates
  the export.json shape per record (`_validated_import_rows`: required fields,
  enum columns re-checked, screenshot `data_base64` decoded with
  `validate=True`, raising `ImportValidationError`), then inserts every table
  in ONE transaction with row ids preserved so cross-table references survive.
  REPLACE-into-empty semantics: `ImportNotEmptyError` when any table already
  holds rows unless `replace=True` wipes-then-inserts atomically. Legacy
  backups missing newer columns (`guide_exchanges.step_title`,
  `claims.paypal_email`/`status`, `submissions.answers_json`, whole
  postdating tables) restore with the schema defaults via `.get` — never
  invented values.
- `botsite/testing.py` — `POST /testing/owner/import.json`: same owner auth as
  every owner route (`require_owner`: 503 fail-closed when SITE_PASSWORD is
  unset, 401 on bad credentials) plus the standard `guard_state_change`
  dependency (same-origin Origin/Referer check + rate limit — the repo's
  existing CSRF pattern on state-changing routes); body bounded at 10 MB
  (413, declared and actual size both checked), invalid JSON/shape → 400 with
  the exact reason, non-empty DB without `?replace=1` → 409.
- `botsite/tests/test_testing_import.py` — 8 tests: 503 fail-closed, 401
  missing/wrong credentials, cross-origin + headerless 403 (auth alone is no
  CSRF defense), full export→wipe→import round trip (blobs byte-exact,
  `step_title` pin preserved), legacy-backup defaults, malformed-shape 400s,
  oversize 413, non-empty refusal / replace flag.
- `docs/ideas/backlog.md` — the import-valve bullet flipped to `built`
  (PR #320); this session's 💡 appended.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — 1373 passed, 1 warning (baseline 1365 + 8 import
  tests); `python3 bootstrap.py check --strict` — green once this card
  flipped complete (the only red during the session was the designed
  born-red hold on this card).

⚑ Self-initiated: no — backlog promotion (the import-valve bullet, captured
2026-07-13 by the step-provenance session).

## 💡 Session idea

**Cross-table reference check on import — reject backups with orphan rows** —
SQLite foreign keys are OFF by default (`PRAGMA foreign_keys` is never
enabled in `testing_store._connect()`), so a truncated or hand-edited backup
whose submissions reference missing claims imports "successfully" today, and
the owner queue's INNER JOINs (`list_submissions`) then silently drop the
orphan rows — a restore that reports ok but shows less than it inserted. A
referential pass in `_validated_import_rows` (submission.claim_id ∈ claim
ids, ai_review/screenshot.submission_id ∈ submission ids, guide_exchange +
ledger claim_ids ∈ claim ids) would 400 loudly instead. Worth having because
the valve's entire promise is a faithful restore, and orphan rows are the one
corruption class its validation still admits silently. Deduped against
`docs/ideas/backlog.md` + the queue-state NEXT list: no
foreign-key/referential/orphan bullet exists anywhere. Captured in
`docs/ideas/backlog.md`.

## ⟲ Previous-session review

The claims-drift-gate session (PR #318) did well — it validated its detector
against real history by letting the new gate flag the exact stale claim it
then swept, and covered all four terminality lanes with synthetic-repo
tests; what it missed: its own 💡 concedes the pruned-ref lane stays
undetectable, so the gate's one blind spot is exactly the state GitHub's
"delete branch on merge" setting would make common — the PR-number claim
token it proposed is still unbuilt.
