# 2026-07-16 — Registry blockers join the ledger by ask_id (catalog, products, puddle museum)

> **Status:** `complete` — PR #362, branch `claude/registries-askid`;
> extended PR #360's optional blocker+ask_id object from arcade.json to the
> three remaining botsite registries (catalog.json, products.json,
> puddle_museum.json), with the ledger rows ASK-0012..0016, askverify
> joins, blocker panels, and the four-registry cross-surface pin to match.

- **📊 Model:** Fable 5 · high · feature build (build-slice: registries ask_id join)

**Goal:** PR #360 gave arcade.json blockers a stable `ASK-NNNN` join key
into `docs/owner/OWNER-ACTIONS.md` and `app/askverify.py`. Its own baton
said the follow-up is cheap: "the same optional blocker+ask_id object fits
catalog.json / products.json / puddle_museum.json unchanged." This slice
does exactly that: a shared `botsite/blockers.py` normalizer (arcade's
fail-soft semantics, refactored out and imported back), optional `blocker`
objects on the not-live entries of the three registries, honest six-field
ledger rows for the genuine owner actions (Gumroad publish pass,
photo-packs originals handoff, ultramarine rename decision, §5
illustration gate, de-papieren-sinaasappel proofread), askverify REGISTRY
joins with `probe=None` + honest reasons, blocker panels on catalog /
products / puddle-museum templates mirroring arcade_detail's ledger-ref
line, and the cross-surface consistency pin extended to all four
registries. The 5 write-slice parked catalog titles get NO blocker — they
are agent work, not owner actions.

⚑ Self-initiated: no — coordinator-dispatched slice, promoted from PR
#360's close-out baton (`.sessions/2026-07-16-arcade-askid-join.md`,
"Next session should know").

## Close-out

**Evidence:**

- files touched this branch: new `botsite/blockers.py` (shared fail-soft
  normalizer) + `botsite/arcade.py` refactored onto it; loaders
  `botsite/catalog.py` / `botsite/products.py` / `botsite/puddle_museum.py`
  wired through it; registries `botsite/data/catalog.json` /
  `products.json` / `puddle_museum.json` (blocker objects on the
  owner-gated entries); templates `catalog.html` / `products.html` /
  `puddle_museum.html` (blocker panels with guarded Ledger-ref lines);
  `docs/owner/OWNER-ACTIONS.md` (rows ASK-0012..0016); `app/askverify.py`
  (five probe-less REGISTRY joins with honest reasons); tests
  `botsite/tests/test_catalog.py` / `test_products.py` /
  `test_puddle_museum.py` + `tests/test_askverify.py` (four-registry
  cross-surface pin, open-ask pin 11 → 16); this card +
  `control/claims/claude-registries-askid.md`. 19 files, +943/−69.
- git: branch `claude/registries-askid` from `main` @ `bd79558`; PR #362;
  commits `bace7eb` (born-red card + claim), `e47f4a9` (normalizer + four
  registries wired), `d8b20a5` (ledger rows + registry blockers join by
  id), `ca811a4` (panels + cross-surface test pins). Cross-agent review
  verdict: APPROVE (reviewer ran mutation tests on the normalizer's
  degrade paths and an XSS probe against the rendered panels).
- verify: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — **1578 passed, 1 warning** (+59 vs main's 1519);
  `python3 bootstrap.py check --strict` — pass at this flip (the only red
  during the session was the DESIGNED born-red hold on this card,
  released here).

**Judgment:**

- Decisions made: (1) the five write-slice parked catalog titles
  (marginalia-society, night-kiln, paper-orange, pepper-ledger,
  windmill-mouse) got NO blocker and NO ledger row — a missing manuscript
  is agent work, not an owner action; (2) arcade's normalizer was
  extracted to `botsite/blockers.py` and imported back rather than
  copied, so all four registries share one fail-soft semantics (malformed
  blocker → `None`, never invalidates the entry) and arcade's tests
  passed unchanged; (3) all five new ledger rows say plainly they are NOT
  machine-checkable (Gumroad state / off-repo files / owner decisions) —
  askverify registers them `probe=None` with the honest reason instead of
  inventing a probe; (4) ledger ids continued at the next free numbers
  (ASK-0012..0016), none reused.
- Next session should know: the baton's two tasks are both joins on the
  now-proven ask_id key — the release-drift FLAG (parked at PR #349,
  buildable with zero new botsite network surface) and the owner-console
  reverse join below; ASK-0012 alone un-gates 14 public cards, so the
  Gumroad publish pass is the highest-leverage owner click on the ledger.

## 💡 Session idea

**Owner-console reverse join — an "unblocks N cards" chip per ask.** The
forward join is now complete (every public blocker panel names its
ASK-NNNN), but the owner console's asks panel still shows each ask bare,
with no weight. Invert the join: for each open ask, scan the four botsite
registries for `blocker.ask_id` matches and render a read-only "unblocks
N public cards" chip with the card slugs — ASK-0012 alone would read
"unblocks 14 cards" (11 catalog + 3 products) while ASK-0009 reads
"unblocks 0". That single number is a priority signal the ledger cannot
express today: it lets the owner spend his one click where it un-gates
the most public surface. Read-only, no new POST surface; the
cross-surface consistency pin added this session already guarantees the
reverse scan can never dangle.

## ⟲ Previous-session review

`.sessions/2026-07-15-walls-cards-heartbeat.md` is an exemplary
docs-slice card — its window-drift reasoning (fixing all fourteen model
lines, not just the nine inside the lint window, because the window
slides) is exactly the durable-over-minimal judgment this repo asks for,
and this session leaned on its taught model-line grammar directly at
flip time; one gap: its "seat-digest stale" flag has now ridden the
next-session note without being consumed — it still needs a
`bootstrap.py seat-digest` follow-up slice.
