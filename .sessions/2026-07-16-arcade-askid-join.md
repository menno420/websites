# 2026-07-16 — Arcade: launch-blocker panels join asks by ask_id

> **Status:** `complete` — PR #360, branch `claude/arcade-askid-join`; the
> two arcade owner clicks became ledger rows ASK-0010/0011, the committed
> arcade blockers and the askverify probe registry now join on those ids
> exactly, and the keyword-signature scan remains the honest fallback for
> id-less rows.

- **📊 Model:** Fable (Claude 5 family) · medium · feature build

**Goal:** the arcade per-game launch-blocker panels (PR #349) and the owner
console's verification chips (PR #358) tell the same story from the same
facts — but they shared NO join key. The only machine join between a blocker
and its ask was `app/askverify.py`'s two arcade probe entries
(`lumen-drift-release`, `product-forge-pages`), which sat `ask_id=None` and
bound purely by brittle keyword signatures over ask headline text. This slice
switched that join to the ledger's stable `ASK-NNNN` id as the PRIMARY key,
keeping the signature scan as the fallback for id-less rows.

⚑ Self-initiated: no — coordinator-dispatched slice promoted from the
NEXT-2-TASKS baton (`.sessions/2026-07-15-arcade-detail.md` idea, promoted
by `control/status.md` at a0a6e66).

## Close-out

**Evidence:**

- files touched this branch: `.sessions/2026-07-16-arcade-askid-join.md` +
  `control/claims/2026-07-16-arcade-askid-join.md` (first commit; claim
  deleted at this flip), `docs/owner/OWNER-ACTIONS.md` (two appended
  six-field ⚑ rows, ids ASK-0010 lumen-drift-v1.3 release + ASK-0011
  product-forge Pages source — append-only scheme, next free numbers),
  `app/askverify.py` (the two arcade REGISTRY entries flip from
  `ask_id=None` to the new exact ids; `match()` already prefers exact-ID
  with signature fallback since PR #358, so only the key flips),
  `botsite/arcade.py` (`_normalized_ask_id` — optional validated
  `ASK-\d{4}`, fail-soft to None; blocker dicts now always carry the
  `ask_id` key), `botsite/data/arcade.json` (both committed blockers carry
  their ledger id), `botsite/templates/arcade_detail.html` (muted "Ledger
  ref" line when an id is present; id-less blockers render exactly as
  before), `botsite/tests/test_arcade.py` (+11 test items: valid-id
  normalization, 8 malformed-id degrade cases keeping the blocker alive,
  committed-registry id pin, detail-page ledger-ref render, id-less
  fallback render), `tests/test_askverify.py` (+5: ID-primary join binds
  where the old brittle key mismatches, id-less signature fallback,
  annotate() end-to-end by id, cross-surface consistency pin arcade.json ↔
  ledger Open rows ↔ probe registry; ledger pins updated 9 → 11 open
  asks), `control/status.md` (coordinator-delegated heartbeat overwrite:
  11-ask mirror + next-2 baton).
- git: branch `claude/arcade-askid-join` from `main` @ `a0a6e66`; PR #360
  (draft, born-red until this flip). Commits: d8ac525 (card + claim),
  0f2b558 (implementation), a2a1342 (heartbeat), this flip.
- verify (before the implementation push): `python3 -m pytest tests/
  botsite/tests dashboard/tests review/tests -q` — **1519 passed, 1
  warning in 91.94s (0:01:31)** (+16 vs main's 1503); `python3
  bootstrap.py check --strict` — green except the DESIGNED born-red hold
  on this card ("HOLD (by design): session card
  .sessions/2026-07-16-arcade-askid-join.md declares an in-progress
  Status"), released by this flip and re-verified after it.

**Judgment:**

- Decisions made: (1) the arcade owner clicks became REAL ledger rows
  (ASK-0010/0011) instead of leaving `blocker.ask_id` dangling — an id
  join is only honest when both sides exist; the rows transcribe the
  registry's existing blocker prose, no new claims. (2) `ask_id` on the
  blocker is optional and fail-soft exactly like the blocker itself: a
  malformed id costs only the ledger ref, never the panel (degrade, don't
  invent). (3) no new join code path — askverify's PR-#358 exact-ID
  matcher IS the join; this slice only flips the arcade entries onto the
  primary key, so there is one matcher to maintain, not two.
- Next session should know: the baton's two follow-ups are now cheap —
  the same optional blocker+ask_id object fits catalog.json /
  products.json / puddle_museum.json unchanged, and a release-drift check
  can join blocker.ask_id to its probe inside scripts/healthcheck.py
  (which already imports both app and botsite) with zero new botsite
  network surface. When an owner click lands, ONE ledger edit (move the
  row to Decided) plus the registry availability flip retires both the
  panel and the chip.

## 💡 Session idea

**Pin the ASK-NNNN grammar across services the way listfilter is pinned.**
The stable-id shape now lives in three places that can never import each
other: `app/owner_queue.py` `_ID_RE` (parser), `app/askverify.py`'s
well-formedness checks, and `botsite/arcade.py` `_ASK_ID_RE` (blocker
join key). The repo already solves exactly this class of drift for
`listfilter` with a byte-identity test on the vendored copy — a small
`tests/` contract test asserting the id regexes agree on one canonical
positive/negative example table (ASK-0042 yes; ask-0042 / ASK-42 /
embedded-in-prose no) would make it impossible for the public join key
and the gated parser to drift apart silently. Deduped: no such
cross-service grammar pin exists today (the new consistency test pins the
committed VALUES, not the SHAPE rules).

## ⟲ Previous-session review

`.sessions/2026-07-15-arcade-detail.md` earned its keep twice here: its
close-out review is what promoted this slice (it named the missing join
key explicitly — "the stable ask-ID idea that card filed would give the
arcade `blocker` objects an `ask_id` to reference, and both surfaces would
flip from one ledger edit" — which this session implemented almost
verbatim), and its discipline of transcribing blocker copy from existing
status_note prose made minting the ledger rows honest and mechanical: the
six-field asks are restatements of already-committed facts, not new
claims. Its sequencing judgment also held up — it deliberately did NOT
invent an id scheme inside arcade.json a day before #358 existed, so no
throwaway key ever shipped. The improvement it points at: a card whose
review names a concrete promotable slice could also name the files the
slice will touch (this one had to be re-derived here from three PRs);
one line of expected-surface would have saved most of this session's
orientation reads.
