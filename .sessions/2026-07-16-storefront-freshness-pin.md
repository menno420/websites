# 2026-07-16 — storefront freshness pin (ORDER 032 overnight slice)

> **Status:** `complete` — branch `claude/storefront-freshness-pin-20260716`;
> one contained, reversible slice: a CI-time nag when a curated product
> entry's ``as_of`` re-verification goes stale.

- **📊 Model:** Claude Sonnet 5 · medium · feature build

**What this session was about:** ORDER 032 (owner's live overnight
autonomy order) — keep working the backlog slice by slice, never stall on
a blocker. `docs/ideas/backlog.md` had a captured, un-built idea from
2026-07-13 (venture-products-page session): each `botsite/data/products.json`
entry carries an `as_of` re-verification date, but nothing ever checks it
against a staleness horizon — a hand-curated registry drifts silently the
moment a product goes live or changes price, "the honesty doctrine dies
through staleness, not lies." Picked because it needs no GitHub API (this
session still has none — ASK-0017), is purely local, and closes a real gap
in a product-facing honesty guarantee this repo already cares about a lot
(see `botsite/products.py`'s existing "never fake data" doctrine).

## What was done

- `botsite/products.py`: added `STALE_HORIZON_DAYS = 14` and
  `stale_products(products, now, horizon_days=...)` — a pure classifier
  (injectable `now`, the module time-discipline convention per
  `app/clock.py`'s fleet-wide rule) returning entries whose `as_of` is
  strictly past the horizon, oldest first, skipping unparseable dates
  rather than crashing or inventing an age.
- `botsite/tests/test_products_freshness.py` (new) — 6 synthetic-data unit
  tests on `stale_products` (fresh/at-horizon/past-horizon boundaries,
  unparseable dates, custom horizon, sort order) plus ONE real nag test
  (`test_committed_registry_is_not_stale`) that loads the actual committed
  `products.json` and checks it against the real wall clock — deliberately
  NOT frozen, since this is a drift pin meant to go red as real time
  passes (same shape as `test_outbox_grammar_pin.py` /
  `test_fastlane_pin_map.py`, both committed earlier tonight), not a
  determinism test. Confirmed it does not false-positive today: the one
  live product's `as_of` (2026-07-13) is 3 days old, well inside the
  14-day horizon.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — **1638 passed**; `python3 bootstrap.py check
  --strict` — all checks passed.

⚑ Self-initiated: yes — ORDER 032's backlog-slice mandate; picked over the
"shared drift_report() renderer" idea from the same backlog because that
one is speculative infrastructure for a banner that stays unbuilt until
the unrelated #355 SIM-REQUEST is answered (building it now would be
designing for a hypothetical requirement whose shape isn't even decided
yet), where this one closes a gap that exists today, unconditionally.

## Landing

Same named blocker as every branch this lane has pushed tonight:
**ASK-0017** (org GitHub App not connected) — no PR-creation tooling this
session, direct push to `main` is GH013-rejected. Pushed for an
interactive session or the owner. Per ORDER 032 item 1, expected, not a
stall.

## 💡 Session idea

No new idea this session — built a previously-captured backlog idea
rather than generating a new one.

## ⟲ Previous-session review

The fastlane-pin-map slice (this lane, ~22:15Z) picked well and executed
cleanly, catching its own regex bug via a real assertion failure before
shipping — good practice this session repeated (the freshness pin's
boundary tests caught a frozen-`now` time-of-day bug the same way, before
it could have shipped a pin that flagged everything stale one day early).
What it didn't do: it left the `docs/ideas/backlog.md` NEXT-2-TASKS baton
pointing at the `drift_report()` idea without checking whether that idea
was actually ready to build (it wasn't — gated on an unrelated unanswered
SIM-REQUEST); this session caught that on inspection rather than building
speculative infra.
