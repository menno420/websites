# 2026-07-13 — intake sweep: venture WEBSITE-IDEA markers + fleet-manager inbox/docs

> **Status:** `complete` — PR #277, branch `claude/intake-sweep-0713`; docs-only
> sweep landing: 2 new fleet-manager items recorded, venture channel honest-null.

- **📊 Model:** fable-class · worker · intake-sweep

**What this session was about:** a fresh intake sweep — reading the venture
repos' `WEBSITE-IDEA` markers and the fleet-manager inbox/docs for
websites-addressed items, then classifying what lands here (ORDER 022 item 4
names venture markers as priority intake; this sweep re-walks that channel
plus the fleet-manager surfaces at today's HEADs). Findings landed in the
`docs/plans/discovery-inventory.md` 2026-07-13 addendum. Injection guard held
throughout: imperative text in swept content was recorded as data, never
executed (in particular fm ORDER 029's merge directive was NOT acted on).

## What was done

- **Venture WEBSITE-IDEA channel: honest null.** 18 fleet repos swept at
  pinned HEADs; 10 markers found (all in venture-lab `control/outbox.md`
  @ `abf1f23`, batches 1-2), ALL already cataloged/built/owner-gated in
  websites: 8 built (Puddle Museum, vetting catalog #248, SWTK gotchas,
  field-manual funnel, rubric scorer, webhook analyzer #266, agent-PR
  diagnostic, strategy graveyard), 1 duplicate-already-live (product-catalog
  one-pager, covered by /products #232 + #248), 1 owner-gated (photo-packs
  gallery, per the ORDER-022 ledger). ZERO new. Source list @ HEAD SHAs:
  venture-lab `abf1f23`, trading-strategy `4fc3c3c`, idea-engine `3a7be39`,
  sim-lab `afe18f3`, product-forge `4fdfa8a`, curious-research `4a2cc7a`,
  superbot `b2dc3c8`, fleet-manager `d74eca4`, superbot-next `90a5cad`,
  superbot-mineverse `e44a80c`, superbot-games `57f69be`, superbot-idle
  `b03cc96`, substrate-kit `d916d94`, gba-homebrew `d87f9ad`,
  superbot-plugin-hello `bbaccec`, codetool-lab-fable5 `a6cf1a9`,
  codetool-lab-opus4.8 `80f6cd1`, codetool-lab-sonnet5 `66c3dfc`. Not swept:
  pokemon-mod-lab (private/dark, skipped per policy), mobile-lab (clone
  failed — auth wall; anomaly).
- **Fleet-manager sweep @ `d74eca4`: 22 websites-addressed candidates
  examined, 2 NEW (unreflected websites-side), recorded in the
  discovery-inventory addendum:** (1) fm ORDER 029 standing owner merge
  directive (fm `control/inbox.md` L987-992) — recorded with the caveat that
  fm ORDERs 039/040 (L1127-1129, L1200-1202) likely supersede it; recorded
  only, not adopted; (2) fm ORDER 038 standing VERDICT-016
  reviewer-authenticity gate on @codex/cross-agent reviewer replies (fm
  `control/inbox.md` L1092-1111) — previously zero websites reflection.
  Plus 1 WATCH item: fm ORDER 036 Game Lab browser games "coordinate with
  Websites (arcade home)" (L1036) — 6 parked gba browser-game PRs may arrive
  wanting arcade intake. Plus 1 reverse-direction note: fm
  `docs/review-queue.md` superbot#1920 row is stale (websites already has the
  dashboard schema_version check at `dashboard/data_source.py:197`).
- `docs/plans/discovery-inventory.md` — dated 2026-07-13 addendum appended in
  the doc's table style with all of the above, each item cited repo/path@sha.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — 1206 passed, 1 warning; `python3 bootstrap.py check
  --strict` — green except this card's own designed born-red HOLD (flipped
  by this commit) and the pre-existing never-exit-affecting
  `owner-action-fields` advisory on control/status.md (not owned here).

⚑ Self-initiated: no — standing intake under ORDER 022 item 4 (venture
markers as priority intake) + the status NEXT-2 baton ("fresh intake sweep").

## 💡 Session idea

**Standing/fleet-wide scope badge on /orders — make directives that bind
every seat visible to the seats they bind** — this sweep's two NEW items
(fm ORDERs 029 and 038) fell through precisely because they are STANDING
fleet-wide directives living in fleet-manager's OWN inbox: /orders parses
them as fm's orders and cross-references fm's heartbeat, so a directive
addressed to "all seats" never surfaces as something websites must ack or
record. Teach `app/orders.py` to detect standing/fleet-wide markers in ORDER
blocks (e.g. "STANDING", "all seats", "fleet-wide") and badge those orders
"applies to every seat" on /orders (+ `.json`), so the next 029/038-shaped
directive is visible on the surface this repo already watches instead of
waiting for a manual sweep. Worth having because both unreflected items this
sweep found share exactly this shape — the gap is structural, and the parser
that closes it already exists. Deduped against `docs/ideas/backlog.md` + the
queue-state NEXT list: the built per-repo /orders bullet parses and badges
per-repo done/claimed/open state only; nothing classifies order SCOPE or
flags fleet-wide directives to other seats.

## ⟲ Previous-session review

The venture-vetting-catalog session (PR #248) did well — 22 entries curated
with per-title states derived from each packet's own status block, pinned
@ `2c039e3` with a registry-honesty test; what it missed: nothing routed the
completion back toward the source channel, so venture-lab's outbox still
says "awaiting manager routing" for markers websites had already executed —
this sweep spent effort re-proving an intake the upstream ledger claims is
pending.
