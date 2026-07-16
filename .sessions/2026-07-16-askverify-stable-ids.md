# 2026-07-16 — Askverify stable ask IDs: exact-ID matching

> **Status:** `complete` — PR #358 (ready-for-review), branch
> `claude/askverify-stable-ids`; stable `ID: ASK-NNNN` lines on all 9 open
> ledger asks + exact-ID matching in `app/askverify.py` with honest
> signature fallback.

- **📊 Model:** Claude Fable · medium · feature build (stable ask IDs across ledger + parser + matcher)

**What this session is about:** the 07-15 preflight-verdicts session's own
filed idea, promoted: askverify matches asks by keyword signatures over
their WHAT lines, so a reworded ask silently falls to honest-unmatched
(`UNMATCHED_REASON` literally names the fix). Each `⚑ OWNER-ACTION` block
in `docs/owner/OWNER-ACTIONS.md` gains one `ID: ASK-NNNN` line (assigned
once, append-only, never reused — the 9 open asks become ASK-0001..0009 in
document order). `owner_queue._parse_block` learns the line
(`item["ask_id"]`, absent-safe for legacy blocks), every askverify
REGISTRY entry carries the `ask_id` of the ledger row it verifies today
(derived by running the CURRENT signature matcher against the real ledger
before editing), and `match()` prefers exact-ID lookup — an unknown ID
falls through to the signature scan so a not-yet-registered new ask still
matches honestly; items without an ID keep the signature path unchanged.

⚑ Self-initiated: no — dispatched slice (coordinator), building on the
07-15 card's filed session idea.

## Close-out

**Evidence:**

- files touched this branch: `.sessions/2026-07-16-askverify-stable-ids.md`
  + `control/claims/claude-askverify-stable-ids.md` (first commit
  `206b76f`; claim deleted at this flip), `docs/owner/OWNER-ACTIONS.md`
  (scheme note + `ID: ASK-0001..0009` on the 9 open blocks, nothing
  reworded), `app/owner_queue.py` (`_ID_RE` + header-region extraction in
  `_parse_block`, `item["ask_id"]` in `_make_item`, id-preserving dedup
  merge), `app/askverify.py` (`ask_id` on all 11 REGISTRY entries — 9
  mapped, `lumen-drift-release`/`product-forge-pages` explicitly None —
  `_BY_ASK_ID` lookup, id-first `match()`, annotate passes
  `item.get("ask_id")`, UNMATCHED_REASON reworded), `app/briefing.py`
  (`asks()` items carry `ask_id`; headline fallback skips it),
  `tests/test_askverify.py` (real-ledger tests pin 9 unique ids +
  id/signature agreement; new: id-beats-signature, unknown-id fallback,
  id-less unchanged, parser extraction incl. flattened lane copies,
  prose-mention never binds, ledger-wide never-reused scan),
  `tests/test_json_contracts.py` (/queue.json item pin gains the
  deliberate `ask_id` key), `control/status.md` (coordinator-delegated
  heartbeat, commit `810e158`). `app/owner.py` deliberately untouched
  (open PR #357 conflict risk) — /owner/queue gets ids for free through
  `owner_queue.overview()`.
- id→entry mapping derived BEFORE editing by running the live signature
  matcher against the real ledger: ASK-0001 q-0004 · 0002 discord-oauth ·
  0003 armed-service · 0004 botsite-database-url · 0005 paypal-credentials
  · 0006 botsite-gate · 0007 order-020-pat · 0008 bake-pat · 0009
  dashboard-site-password. (Registry holds 11 entries, not the 12 the
  dispatch brief said — counted live.)
- verify (pre-push, this flip): `python3 -m pytest tests/ botsite/tests
  dashboard/tests review/tests -q` — **1503 passed, 1 warning in 83.18s**
  (main baseline 1502; the born-red-hold run before this flip printed
  verbatim: `check: HOLD (by design): session card
  .sessions/2026-07-16-askverify-stable-ids.md declares an in-progress
  Status — the born-red session gate holds the merge red until the card
  flips complete.`); `python3 bootstrap.py check --strict` re-run after
  this flip — see PR #358 for the recorded line.
- git: branch `claude/askverify-stable-ids` based on `main` @ `c2653b4`;
  commits `206b76f` (card+claim) → `65ed0d7` (implementation) → `810e158`
  (heartbeat) → this flip. PR #358, created draft then flipped
  ready-for-review (flip succeeded, no denial).

**Judgment:**

- Decisions made: (1) only the block HEADER (before the first six-field
  label) is scanned for `ID:`, so an ask's prose mentioning another ask's
  id — the ledger already does this ("extends the ORDER 020 ask") — can
  never bind; (2) an unknown ASK-NNNN falls through to the signature scan
  instead of returning unmatched, so a brand-new ask whose id is not yet
  registered still verifies on its keywords, honestly; (3) claim-once
  ambiguity stays exactly as-was and now guards only the signature path —
  id matches are exact and two different ids cannot collide; (4) the
  /queue.json contract pin was updated deliberately (`ask_id` on items) —
  contract tests exist to catch accidental drift, and this drift is the
  feature.
- Next session should know: lane status files and the fleet-manager
  owner-queue doc carry FLATTENED copies of the ledger asks WITHOUT id
  lines until their sources adopt the scheme — those items ride the
  unchanged signature path (absent-safe by design); the flattened-copy
  parser case is already tested. New asks: take the next free number
  (ASK-0010) and register the id in askverify's REGISTRY when adding a
  probe.

## 💡 Session idea

**Ask IDs as anchors + cross-links on the owner surfaces** — every ask now
has a permanent machine-readable identity, but it is invisible in the UI.
Render the id as a small mono badge on each /owner/queue card and
/owner/briefing row, make it an HTML anchor (`#ask-0006`), and link the
verdict chip back to the ledger row (raw GitHub URL) while ledger tooling
links forward to `/owner/queue#ask-0006` — chips, writeback targets, and
ledger rows would all cross-reference by one stable key, and the owner
could paste `ASK-0006` in chat instead of quoting a WHAT line. Deduped:
`.sessions/2026-07-15-arcade-detail.md` names `ask_id` only as an arcade
blocker join key; no anchor/deep-link bullet exists in `docs/ideas/` or
any session card.

## ⟲ Previous-session review

`.sessions/2026-07-15-launch-preflight-verdicts.md` is the direct parent
of this slice and its close-out carried unusually well: its 💡 idea (this
exact feature) was specific enough to implement without re-derivation —
it named the line format, the assignment rule, and the parser tolerance,
all of which held true in code. Its evidence section's "9/9 open asks
matched, 9 distinct entries" claim re-verified exactly on today's ledger
before any edit, which is what made assigning ids off the live matcher
safe. One honest gap: it says the parser "already tolerates unknown
lines", which is true for FIELD lines but underspecified for header
lines — the ID extraction still needed a deliberate header-region-only
rule to avoid prose mentions binding. The 07-16 rerun-jobs card on PR
#357's branch (`.sessions/2026-07-16-rerun-jobs-preflight.md`, fetched
via `refs/pull/357/head` @ `e8f1c78`) is likewise a clean template: its
"batons decay fast — verify-then-act" lesson applied here too (the brief
said 12 registry entries; a live count said 11), and its judgment section
pointing at "stable ask IDs" as the next increment is exactly what this
session consumed — two cards in a row handing work forward accurately.
