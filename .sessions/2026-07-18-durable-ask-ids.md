# 2026-07-18 — Durable ask IDs on the owner-action queue (C15)

> **Status:** `complete` — branch `claude/durable-ask-ids`; each ⚑ owner ask now
> carries a durable, content-derived identifier so the gated writeback console
> (`/owner/queue`) targets a mark-complete / assistance / note by that stable id
> instead of by the ask's raw headline text. `app/owner_queue.py` gained
> `ask_uid(item)` (the ledger `ID: ASK-NNNN` when present, else a short SHA-256 of
> the normalized headline) + `resolve_uid(items, uid)`, and `overview()` exposes
> `uid` on every ask object; `app/owner.py`'s writeback preview / confirm / the
> `complete` firing route resolve the target ask by that durable id, failing
> closed on an unknown id (never acting on the wrong ask); `owner_queue.html`
> carries the hidden identifier and the preview threads it into the confirm. The
> C14 auto-clear (`askverify.annotate` / `split_self_cleaned`) operates on the
> same ask objects — the id is additive and does not disturb it. The CSRF /
> same-origin + rate-limit floor on every state-changing POST is preserved.

- **📊 Model:** Claude Opus · high · feature build

**What this session is about:** the owner console lists each ⚑ needs-owner ask as a
card with per-ask MARK COMPLETE / REQUEST ASSISTANCE / ADD NOTE forms. Each form
had carried the ask's full **headline text** as its hidden `target`, and the
complete route re-found the ask by exact-headline match to fail closed when the
ask was gone. Headline-as-identity is brittle: it is the ask's WHAT prose, so a
rewording upstream (or two asks that normalize alike) can point the fail-closed
re-find at the wrong ask — or at none. C15 gives each ask a durable, deterministic
id derived from STABLE identifying content (its `ID: ASK-NNNN` when the ledger
block carries one — so the id survives a WHAT rewording — else a short hash of the
normalized headline, the same identity `/queue` dedups on). The id is identical
across reorders of the ledger and stable across runs; the writeback routes resolve
the target ask by it, rejecting an unknown id safely.

⚑ Self-initiated: no — coordinator-dispatched backlog slice (C15).

## Close-out

**Evidence:**

- files touched this branch:
  - `app/owner_queue.py` — `ask_uid(item)` (ask_id-or-normalized-headline →
    `ask-<12-hex>`, never positional) + `resolve_uid(items, uid)`; `overview()`
    attaches `uid` to every ask after the dedup/sort.
  - `app/owner.py` — `_find_ask(target, uid=…)` resolves by the durable id when
    supplied (legacy exact-headline fallback only when no uid); the writeback
    preview + confirm thread `uid`; `action_queue_complete` fails closed on an
    unknown/stale id exactly like a vanished ask; `_render_owner_queue` sets a
    belt-and-braces `uid` on the live surface so a per-ask form never renders a
    blank identifier.
  - `app/templates/owner_queue.html` — each per-ask form carries the hidden
    `uid`; the preview's confirm form (generic `owner_preflight.html`) threads it
    through unchanged.
  - `tests/test_json_contracts.py` — `/queue.json` `QUEUE_ITEM` pin gains `uid`
    (the contract-pin discipline: the serialized payload changed in this same
    PR).
  - `tests/test_durable_ask_ids.py` — 12 new tests (below), plus this card and
    `control/status.md`.
- test coverage (12): uid STABLE across a ledger reorder (same ask → same id
  regardless of position); distinct asks → distinct ids (opaque `ask-<hex>`);
  ask_id-keyed uid SURVIVES a WHAT rewording; `resolve_uid` finds the right ask
  after a reorder / returns None for a removed-or-unknown id; a contentless item
  → empty uid; `overview()` / `/queue.json` expose the uid; the complete CONFIRM
  resolves the correct ask by uid AFTER the ledger reorders between preview and
  confirm (the core regression — the completion commits against the intended
  ask); an unknown/stale uid FAILS CLOSED (nothing stored, no confirm form
  re-inviting the fire); the preview's confirm form carries the uid; the live
  gated page renders the uid in the per-ask forms; the CSRF/same-origin floor is
  intact on the uid-resolving route (cross-origin 403, unauth 401); C14
  auto-clear still partitions correctly with `uid` present on the items.
- git: branch `claude/durable-ask-ids` from `origin/main` @ `8b918f4` (#391);
  commits `81ae24b` (born-red card), `aea66fe` (the durable-id build + the
  `/queue.json` contract-pin), `3d79993` (the 12 tests), `7191755` (heartbeat
  status), + this flip.
- verify: `python3 -m pytest tests/ botsite/tests dashboard/tests review/tests -q`
  — **1804 passed, 1 warning** (exit 0; 1792 + 12 new); `python3 bootstrap.py
  check --strict` and `--require-session-log` (the CI form) — both exit 0, the
  only red the DESIGNED born-red hold on this card, released at this flip. The
  one advisory warning is on another session's card
  (`2026-07-17-arcade-owner-action-queue.md`, an off-PL-004 task-class segment),
  pre-existing and not this work.

**Judgment:**

- Decisions made: (1) The identity being replaced was, in fact, the ask's raw
  HEADLINE TEXT (not a positional index) — headline-matching is already
  reorder-stable, so the concrete win is that an ask carrying `ID: ASK-NNNN` now
  keys on that id and stays resolvable even when its WHAT prose is REWORDED (where
  headline matching breaks); the id is still, by construction, non-positional, so
  the reorder-stability property holds and is pinned. (2) ADDITIVE, not
  replacing: keep `target` = headline as the human-readable record that lands in
  the committed note/ORDER block (no writeback-store migration — the SQLite audit
  log was never keyed by position), and add a separate `uid` used only for
  RESOLUTION. (3) uid basis = `ask_id` else `_dedup_key` (the SAME normalized
  headline the queue merges on) — so an id-less ask's uid is exactly its dedup
  identity, and two copies of one ask across sources share a uid. (4) An unknown
  uid resolves to None and is treated as "ask gone" — fail closed only when
  sources are fully readable, reusing C14's honest-unknown ladder, so a stale id
  never fakes a "gone" against a partially-unreadable world. (5) Belt-and-braces
  `setdefault` on the live gated surface so a future item-builder that skips
  `overview()` can never render a blank hidden identifier.
- Next session should know: the durable id is `owner_queue.ask_uid` — a stable
  `ask-<12 hex sha256>` over `ask_id` or the normalized headline; anything that
  needs to point at an ask across a request boundary should carry that, not the
  headline. The `/queue.json` `uid` field is contract-pinned; the assist/note
  firing routes accept the confirm's `uid` form field harmlessly (FastAPI drops
  the undeclared field) — only `complete` reads it. The uid is NOT yet persisted
  into the writeback audit log (the committed note still carries only the target
  prose) — see the idea below.

## 💡 Session idea

**Persist the durable `ask_uid` into the writeback audit log + the committed
completion note.** This PR resolves an ask by its durable id at REQUEST time, but
the lasting record — the `writeback_entries` row and the `owner marked COMPLETE`
block appended to `docs/owner/owner-notes.md` — still carries only the human
`target` PROSE. A fleet session reconciling a completion assertion back into the
source heartbeat therefore re-matches on prose, the exact brittleness C15 removed
from the live console. Adding a `uid` column to the SQLite schema (idempotent
`ALTER`, mirroring the existing runtime-created table) and one `ask uid: ask-…`
line to `render_note_block` would make the DURABLE record id-keyed too: the
owner-notes reconciler could join a completion straight to the ask it resolved,
closing the loop end-to-end. It reuses `ask_uid` verbatim and is contained to
`writeback.py` + one contract-pin bump.

## ⟲ Previous-session review

`.sessions/2026-07-18-review-bake-generator-tests.md` (R6) added network-free unit
coverage over the three review bake generators by stubbing each generator's one
IO seam and deriving every expectation from the generator's OWN transform, never
an invented invariant — the same seam-stubbed, offline, derive-from-real-code
discipline this C15 work leans on (the `_patch_overview` fake and the fake
contents-API drive the real routes), so the two cards pin behavior the same
honest way on opposite sides of the queue pipeline: R6 on the bake INPUT, C15 on
the owner-action OUTPUT.
