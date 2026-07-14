# 2026-07-14 — botsite: export→import→export deep-equality round-trip pin

> **Status:** `in-progress`

- **📊 Model:** Claude 5 family · worker · backlog-promotion slice

**What this session is about:** backlog promotion — the captured bullet
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
