# 2026-07-15 — seat digest regen + orientation headroom

> **Status:** `complete` — PR #347, branch `claude/seat-digest-headroom-20260715`;
> two payload slices: `docs/seat-digest.md` regeneration and an
> orientation-budget trim of the boot-read set.

- **📊 Model:** Claude Fable · medium · docs-only (seat-digest regen + boot-read trim)

**What this session is about:** two small maintenance slices in one PR.
(1) `docs/seat-digest.md` — the committed digest is stale against a fresh
render (pre-existing `seat-digest-stale` advisory, flagged as the baton in
`.sessions/2026-07-15-walls-cards-heartbeat.md`) and is missing the three
2026-07-15 walls PR #346 appended to `docs/CAPABILITIES.md`; regenerate
with `python3 bootstrap.py seat-digest` (derived render — never
hand-edited). (2) Orientation headroom — the boot-read set sat at
6997/7000 words (3 words of headroom; split: `docs/current-state.md` 6264
· `docs/AGENT_ORIENTATION.md` 733). Trim stale or duplicated narrative
from `docs/current-state.md` — superseded in-flight notes, history already
preserved in git and session cards — never factual claims still true,
never the Status badge placement, never `control/` files. Achieved:
6997/7000 → **6567/7000** (433 words of headroom).

⚑ Self-initiated: no — dispatched under the owner's live work grant
(accept-edits session mode).

## Close-out

**Evidence:**

- files touched this branch: `.sessions/2026-07-15-seat-digest-headroom.md`
  + `control/claims/claude-seat-digest-headroom-20260715.md` (first
  commit; claim deleted at this flip), `docs/seat-digest.md` (regenerated
  render — walls block now leads with venue-filtered entries including the
  new auto-mode-classifier wall; the other two 2026-07-15 walls fold into
  the "…plus 9 more" pointer because the block is budget-capped at
  `SEAT_DIGEST_BLOCK_BUDGET = 1500` chars by design — see the 💡 below),
  `.substrate/state.json` (the render's recorded hash),
  `docs/current-state.md` (trim only: condensed the superseded lane-set
  mechanism entries, the 20:00Z wake docs-sweep narrative already in
  cards, deploy-evidence elaboration already in `docs/deployment.md`, and
  the superseded 2026-07-13 ender baton → pointer; Status badge and all
  still-true claims untouched).
- git: branch `claude/seat-digest-headroom-20260715`, based on `main` @
  `8fb3ac5`; PR #347. Work done in an isolated `git worktree` (the
  EnterWorktree wall, per `docs/CAPABILITIES.md` 2026-07-15).
- verify: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — **1414 passed, 1 warning**; `python3 bootstrap.py
  check --strict` — the `seat-digest-stale` and `orientation-headroom`
  advisories present at branch base (main `8fb3ac5`) are **both gone**;
  the only red during the session was the DESIGNED born-red hold on this
  card, released by this flip. Orientation budget (kit math,
  `orientation_word_count`): before 6997/7000 (current-state 6264 ·
  AGENT_ORIENTATION 733), after **6567/7000** (current-state 5834 ·
  AGENT_ORIENTATION 733) — 433 words of headroom.

**Judgment:**

- Decisions made: (1) trimmed by condensation, not deletion — every
  Recently-shipped entry keeps its PR number, one-line what-shipped, and
  doc pointer; only elaboration duplicated in git/cards/routed docs was
  cut; (2) the superseded 2026-07-13 ender baton became a one-line pointer
  to `control/status.md` + the In-flight section instead of silently
  vanishing; (3) did NOT hand-edit `docs/seat-digest.md` to force all
  three new walls above the fold — it is a derived render and the
  truncation is the kit's budget cap, so the observation went to the 💡
  idea instead.
- Next session should know: the Status badge line of
  `docs/current-state.md` still cites main `3cac461` / open PRs #342+#343
  (its own 2026-07-15 reboot-truing stamp) — a truing refresh was out of
  this trim's scope; owner clicks pending per #346's baton: land #345 and
  #343.

## 💡 Session idea

**Walls-digest budget cap buries the newest walls — reserve above-the-fold
slots for the freshest ledger entries** — `bootstrap.py seat-digest` caps
the walls block at `SEAT_DIGEST_BLOCK_BUDGET = 1500` chars and renders
entries in ledger order, so the walls most recently verified (operationally
the hottest ones) are exactly the ones that fold into the "…plus N more"
pointer: this session's fresh render surfaces only 1 of the 3 walls added
in #346, while six older walls render in full. Worth having because the
digest's own stale-advisory rationale says "drift here ships stale walls
fleet-wide" — yet a perfectly fresh render still ships a seat prompt that
never names two of the three newest walls. Fix is kit-side (the render is
generated): sort or interleave newest-first within the venue filter, or
reserve the first K slots for the newest append-log entries. Deduped
against `docs/ideas/backlog.md`: the "Kit-gate advisory for the
capability-seed fence" bullet covers the fence markers, the
"Orientation-budget headroom readout" bullet covers the word budget;
nothing touches walls-digest ordering/truncation.

## ⟲ Previous-session review

`.sessions/2026-07-15-walls-cards-heartbeat.md` was this card's format
reference and its baton was directly consumable — "run `python3
bootstrap.py seat-digest` in a follow-up slice" plus the note that the
digest was missing its three new walls is exactly the work order this
session executed, the third consecutive card whose baton was picked up
verbatim. One observation: its close-out proved the pre-existing
advisories against "a pristine baseline worktree" — a habit this session
reused (baseline captured at `8fb3ac5` before branching) and that turned
the before/after advisory claim from assertion into evidence; worth
keeping as standard practice for any advisory-clearing PR.
