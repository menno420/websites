# Release-drift parity

> **Status:** `in-progress`

**Goal:** Surface review's already-baked release-drift signal (`review/data/releases.json`)
on two other owner surfaces — dashboard `/status` and the console public board — read-only
over raw content, with no cross-service package imports and no recomputing of drift.

## Slice 1 — /questions (verified live, skipped)

The review `/questions` surface was verified live and needs no change (honest null).
See Step 4 for the verification evidence recorded at completion.

## Slice 2 — dashboard /status + console board

Add a fetch/shape of the committed releases mirror on each surface, rendering a
drift card/indicator only when drift is present.
