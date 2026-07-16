# 2026-07-16 — owner-console "unblocks N cards" reverse-join chip

> **Status:** `complete` — branch `claude/console-unblocks-chip`; one
> read-only slice: a pure `app/card_gating.py` reverse join wired into the
> gated owner queue, rendered as an "unblocks N cards" chip.

- **📊 Model:** Claude Opus · high · feature build (owner-console unblocks-N-cards reverse-join chip)

**What this session is about:** the owner console already tells the owner
*what* each open owner-action ask is and whether a read-only probe can
verify it (`app/askverify.py` verdict chips). It did not tell him the
*blast radius* — how many public product cards are held closed behind that
one owner click. This session adds the reverse of the same `ask_id` join:
a pure, testable helper (`app/card_gating.py`) loads the four committed
botsite registries from disk, walks their `blocker.ask_id` fields, and
returns `ask_id -> [cards it gates]` aggregated across every registry.
`app/owner.py`'s `_render_owner_queue` attaches the count per queue item
and `owner_queue.html` renders an "unblocks N cards" chip beside the verify
chip. Read-only end to end: no new route, no state change, no CSRF surface.

⚑ Self-initiated: no — dispatched build slice.

## Close-out

**Evidence:**

- files this branch: `app/card_gating.py` (new pure helper),
  `app/owner.py` (import + one `card_gating.annotate_unblocks` call in
  `_render_owner_queue`), `app/templates/owner_queue.html` (the chip,
  shown only when count > 0, tooltip naming the gated cards),
  `tests/test_card_gating.py` + `tests/test_owner_queue_unblocks_chip.py`
  (new), plus the first-commit `.sessions/2026-07-16-console-unblocks-chip.md`
  + `control/claims/console-unblocks-chip.md` (claim deleted at this flip).
- git: branch `claude/console-unblocks-chip`, based on `origin/main` @
  `16a116c`. Commit 1 = born-red card + claim; commit 2 = implementation +
  tests; this flip is the last commit.
- verify: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — **1599 passed, 1 warning**; `python3 bootstrap.py
  check --strict` — the ONLY red during the session was the DESIGNED
  born-red hold on this card, released by this flip.
- live check over the committed registries: ASK-0012 (the Gumroad publish
  pass) reverse-joins to **14 cards** spanning catalog + products, and
  ASK-0015 (the illustration gate) to **5 cards** spanning catalog +
  puddle-museum — the cross-registry aggregation the chip exists to show.

**Judgment:**

- Decisions made: (1) the helper lives in `app/` and reads botsite's
  committed JSON from disk but imports NOTHING from the `botsite` package —
  the four-service import rule forbids it, so the `ASK-NNNN` shape is
  re-stated as a local constant and a test pins it equal to
  `botsite.blockers.ASK_ID_RE`; (2) the chip HIDES at count 0 rather than
  rendering "unblocks 0" — matches the verify chip's present-only idiom and
  keeps the panel quiet; (3) a single ordered title-candidate list
  (`title` → `name` → `name_en` → `slug`) spans all four registry shapes,
  and the dict-shaped puddle-museum is walked across every list-valued key
  so a blocker on any collection is caught.
- Next session should know: the same reverse join could surface on
  `/owner/briefing`'s ASKS section (it already composes `briefing.asks`),
  and a "sort open asks by unblocks-count" affordance would rank the owner's
  clicks by blast radius — captured below, not built here.

## 💡 Session idea

**Rank the owner's clicks by blast radius** — the reverse-join count this
session computes is a natural PRIORITY signal: one Gumroad publish click
(ASK-0012) unblocks 14 public cards, an illustration decision (ASK-0015)
unblocks 5, most asks unblock one or none. A "sort by unblocks" option on
`/owner/queue` (and the same count on `/owner/briefing`'s ASKS section,
which already composes the asks) would let the owner spend his scarcest
resource — his own clicks — on the actions that open the most surface
first, instead of scanning a flat newest-first list. Pure presentation over
the map `card_gating.load_gating()` already returns; no new data. Dedupe
check against `docs/ideas/backlog.md` before filing.

## ⟲ Previous-session review

`.sessions/2026-07-15-walls-cards-heartbeat.md` was this card's format
reference: its close-out models the exact-run-id evidence and the honest
"only red was the designed born-red hold" framing this card reuses, and its
own 💡 idea (whole-history model-line drift sweep) is a clean
capture-don't-derail example — the same discipline that kept this session's
"sort by blast radius" idea in the card rather than in the diff.
