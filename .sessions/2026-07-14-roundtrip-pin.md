# 2026-07-14 — botsite: export→import→export deep-equality round-trip pin

> **Status:** `complete` — PR #327, branch `claude/roundtrip-pin-0714`;
> the backup valve's whole trip is now pinned by deep equality — an
> import that quietly coerces, defaults, or drops ANY covered value goes
> red, instead of only the fields the old round-trip test remembered to
> spot-check.

- **📊 Model:** Claude 5 family · medium · test writing (round-trip pin, backlog-promotion slice)

**What this session was about:** backlog promotion — the captured bullet
"Export→import→export deep-equality round-trip pin"
(`docs/ideas/backlog.md`, captured 2026-07-14 by the import-schema-pin
session, source card `.sessions/2026-07-14-import-schema-pin.md`).
Populate every `_IMPORT_SPEC` table with representative rows, run
`export_all()`, restore the export into a fresh DB via the real valve
path (`import_all()`), re-export, and assert the two exports are DEEPLY
equal — ids, values, base64 blobs, everything — instead of the existing
round-trip test's spot-checks of fields someone remembered to assert.
Plus a legacy-shape round trip: an old backup missing newer columns
imports to the documented defaults-filled shape, never blind equality.

## Close-out (auto-draft edited — evidence corrected to this session)

**Evidence (corrected — the auto-collected lists counted the whole repo,
not this session's diff):**

- tests touched (1, new): `botsite/tests/test_import_roundtrip.py` — 2
  network-free store-level tests (`import_all` IS the valve's restore
  path; the route's auth/size/CSRF gates stay covered by
  `test_testing_import.py`). The deep-equality pin populates every
  `_IMPORT_SPEC` table through the real store writers with
  coercion-catching values — non-defaults everywhere a default exists,
  unicode + newlines, null-vs-set score, an all-256-byte-values blob
  through the renamed `data`/`data_base64` column, every `_IMPORT_REFS`
  FK edge — exports, imports into a brand-new DB file, re-exports, and
  asserts the exports identical. The ONLY normalizations are export-act
  metadata, each documented in-test: `exported_at` (stamped at
  export-call time) and `db_path` (the second DB is a different file BY
  DESIGN — the simulated redeploy wipe); row timestamps import verbatim
  and are NOT normalized. A spec-driven guard fails if any
  `_IMPORT_SPEC` table is fixture-empty, so future tables must join the
  pin. The legacy-shape test imports an old backup missing newer columns
  and whole newer tables, asserts the DOCUMENTED defaults-filled shape
  against explicit expected rows (never blind equality with the input),
  then proves the upgraded export round-trips deep-equal from there.
- docs touched (1): `docs/ideas/backlog.md` — source bullet flipped to
  `built`; this session's 💡 captured as a new bullet.
- git: branch `claude/roundtrip-pin-0714` off main @ `0e97b73` (the #326
  merge); commits: the born-red card, the tests + backlog flip + claim
  file, this close-out (which also deletes the claim file). A pre-work
  rescue branch `rescue/2026-07-14-substrate-state` preserves a dirty
  `.substrate/state.json` found at boot.
- verify: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — 1397 passed, 1 warning (+2 over main's 1395);
  `python3 bootstrap.py check --strict` — exit 0 (the only red being
  this card's own designed born-red HOLD, flipped by this commit).
- teeth proven live (local mutation, never committed): monkeypatching
  `_validated_import_rows` to quietly blank `claims.paypal_email` failed
  the deep-equality pin.

**Judgment:**

- Decisions made: store-level tests instead of route-level (the valve's
  restore path is `import_all`; the route's gates are already pinned
  elsewhere — retesting them here would be duplication, not coverage);
  only export-act metadata normalized, each with a documented reason;
  the fixture-empty guard iterates `_IMPORT_SPEC` itself so schema
  growth forces fixture growth.
- Next session should know: the import-valve ladder is now valve (#320)
  → referential pass (#323) → spec pin (#326) → round-trip pin (#327);
  the remaining honest gap is that "legacy" is still simulated, not
  real bytes — see this session's 💡.

⚑ Self-initiated: no — backlog promotion of the round-trip-pin bullet
captured by the #326 session.

## 💡 Session idea

**Freeze a real export.json as a committed golden legacy fixture** —
today every "legacy backup" in the import tests is a hand-simulated
shape: the test author guesses which columns old exports lacked, and if
that guess is wrong the valve's legacy tolerance is tested against a
fiction. Committing a REAL `export_all()` output now (tiny fixture data,
secrets-free by construction — the export carries no secret) as e.g.
`botsite/tests/data/export-2026-07.json`, then asserting forever that
THIS file imports cleanly, would give future schema changes a genuine
past to be backward-compatible with — each era freezes one more file
instead of re-simulating history. Worth having because the valve's whole
purpose is restoring backups taken by OLDER code, and no test currently
exercises bytes an older version actually wrote. Deduped against
`docs/ideas/backlog.md` + the queue-state NEXT list: the import bullets
are the valve (#320), the referential pass (#323), the spec pin (#326),
and this session's round-trip pin; nothing commits a frozen real-export
fixture. Captured in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

The import-schema-pin session (PR #326) did well — deriving the actual
structure from a live in-memory DB, pinning both deliberate spec↔schema
gaps explicitly with staleness checks, and proving the drift-catch live
with a seeded throwaway column; what it missed: coverage is not
fidelity — its pin proves the spec NAMES every column, not that values
survive the trip (the gap it honestly named in its own 💡, closed here).
Workflow improvement: when a pin test ships, prove its teeth with a
throwaway mutation and record it on the card — #326 did this and it made
this session's review trivially checkable; keep that a habit.
