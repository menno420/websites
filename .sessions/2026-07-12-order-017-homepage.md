# 2026-07-12 — ORDER 017 workstream C: homepage rebuild (30-second front door)

> **Status:** `in-progress` — branch `claude/order-017-homepage`; flips to
> `complete` + PR number as the deliberate LAST code step.

- **📊 Model:** Fable (Claude, family-level) · worker (ORDER 017 dispatch, PR 3 of the review-site refresh) · homepage rebuild + wiring

**What this session was about:** ORDER 017 (control/inbox.md,
2026-07-12T13:46Z, P1, window through 2026-07-14) workstream C plus the
workstream-D accuracy floor, dispatched by the sprint coordinator: replace
the review service's stats-readout landing page with a real front door a
busy reviewer gets in 30 seconds — one-line what-this-is, a key-stats row
read from the committed data files, the five start-here findings from the
July 12 email (each deep-linked and commit-pinned), the AI panel wired to
/ask, a "how this site is organized" map, and the evidence/email-pairing
links. Built on top of the in-flight sibling branches
`claude/order-017-ai-assistant` (PR #174) and
`claude/order-017-data-refresh` (PR #175), merged in because neither had
landed on main at branch time.

## What was done

- **`review/templates/index.html` rebuilt** as the 30-second front door:
  hero ("the public, evidence-backed review of running Claude Code Projects
  as an autonomous software fleet — every claim links to a public commit",
  July 8 + July 12 email pairing named); key-stats row; five "Start here"
  finding cards; the prominent "Ask the project / Review with an AI" panel
  (both actions link `/ask`); the eight-section organization map; the
  evidence-itself links (superbot `docs/eap` + this repo). The old services
  grid and long how-to-read list left to the pages that own that material.
- **`review/story.py`:** new homepage domain content — `START_HERE` (the
  five findings, phrased per the sent email @ `8558179e`, each card's first
  link a deep link: `/problems#incident-2026-07-12`,
  `/questionnaire#gates`, `/questionnaire#memory`, plus the commit-pinned
  email/night-review/figure permalinks); `homepage_stats()` (snapshot tiles
  + a seats tile counted from the fleet mirror's own `seats`/`consolidation`
  data — "peaked ~15 Projects → 8 standing" comes from the baked JSON, and
  a text `gen-3` generations tile that deliberately names the era instead
  of inventing an uncounted number); `site_map()` (seat count injected only
  when the mirror provides one); `EVIDENCE_LINKS`; and an
  `id: incident-2026-07-12` anchor on the lead problems entry.
- **`review/app.py`:** overview route now loads the fleet mirror and passes
  the homepage context; `Ask AI` added to the shared `NAV` (so `base.html`
  renders it on every page, drawer included); `/ask` now carries its own
  active-nav id.
- **`review/templates/problems.html`:** optional per-entry `id=` anchor so
  the homepage incident card deep-links the real entry.
- **`review/static/site.css`:** homepage styles on the existing tokens
  (start-card sizing, the accent-bordered AI panel, map/action spacing) —
  light + dark for free, no new JS, no layout shift.
- **Tests (+9 in `review/tests/test_review.py`):** stats row provably from
  the committed snapshot + fleet mirror (as-of stamps included) with unit
  coverage for `homepage_stats` and honest degradation when the fleet
  mirror is missing; all five start-here cards render with their deep links
  and commit-pinned evidence; the `/problems` anchor exists; `/ask` linked
  from every page and prominent on the homepage; the organization map
  complete; the accuracy floor pinned (no Pokémon mention, `peaked ~15`
  never a bare 15).
- **Smoke-checked live:** local uvicorn, `GET /` → 200 (hero, stats with
  "peaked ~15 Projects → 8 standing", start-here, AI panel, map all
  rendering), `/ask` → 200, `/problems` → 200.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — 400 passed (109 of them the review suite); `python3
  bootstrap.py check --strict` — passes with only the standing advisory
  warning; while this card is in-progress it reports the designed born-red
  HOLD.

⚑ Self-initiated: no — ORDER 017 dispatch (sprint coordinator,
owner-directed); the one flagged choice: the generations stat renders as
the text tile `gen-3` (the era's name, from the email's committed
narrative) rather than a counted number, because no data file counts
generations and the accuracy floor forbids invented metrics.

## 💡 Session idea

**A shared "finding" registry between the homepage and /problems.** The
start-here cards and the problems entries now both carry curated
finding-shaped dicts with evidence links; a third surface (say a findings
index for the email's b-series) would make it worth extracting one
`FINDINGS` registry in `story.py` that pages select from by id — one place
to update phrasing/evidence, impossible for the homepage one-liner and the
full entry to drift apart. Not done now: two surfaces don't yet justify the
indirection. Deduped against `docs/ideas/backlog.md` (nothing there covers
cross-page narrative dedup; the nearest item is the evidence-permalink
CI check idea from the data-refresh card, which is complementary).

## ⟲ Previous-session review

The data-refresh session (PR #175) attributed every unverifiable number and
verified its evidence permalinks resolve before commit — this session
reused its commit-pinned URL constants and its softening rules ("~15",
never 15; attribute, never assert) verbatim, which is the payoff of
curating narrative in the domain layer. What it left that this session hit:
the homepage still said "three deployed services" energy in structure —
rebuilt here. Gap this session leaves for the next: the homepage's
start-here phrasing and /problems' incident entry share facts but not code
(see the idea above), and the sibling AI branch's `/ask` page styles are
page-scoped while the homepage panel's live in site.css — one of the two
conventions should win eventually.
