# 2026-07-13 — botsite /stripe-gotchas: SWTK webhook-gotchas companion page

> **Status:** `complete` — branch `claude/swtk-gotchas`, PR opened READY
> (not draft) against main right after this flip was pushed; merge is the
> auto-merge lane / owner's call — this worker opens, never merges.

- **📊 Model:** Claude Fable 5 · worker · self-initiated build slice

**What this session was about:** self-initiated rung — ORDER 022 item 4 (the
generative mandate), venture WEBSITE-IDEA batch-2 marker "SWTK gotchas
microsite". The Stripe Webhook Test Kit is the fleet's one LIVE product
($29 on Gumroad since 2026-07-12), and its strongest marketing asset — the
six real webhook gotchas the kit exists to catch — had no public page. This
session ships a GET-only botsite page `/stripe-gotchas`: a free companion
checklist presenting the kit's own gotchas content (curated from venture-lab
@ 0679327 — cross-repo data arrives only as committed JSON), with an honest
buy CTA sourced from the existing committed products registry.

## What was done

- `botsite/data/stripe_gotchas.json` — the six gotchas (id/title/symptom/fix,
  plus the source's `why` and code sample where they exist) curated
  verbatim-faithfully from venture-lab
  `candidates/stripe-webhook-test-kit/GOTCHAS.md` +
  `docs/launch/stripe-webhook-test-kit/gotcha-article.md` (+ one-pager kit
  facts) @ `0679327a463c063dcd9fc62b33ffb9a3789fa7d3`, retrieved 2026-07-13;
  top-level provenance block records repo, paths, sha, and retrieved date.
  Nothing invented or embellished.
- `botsite/stripe_gotchas.py` — validating loader mirroring `products.py` /
  `field_manual.py`: required-field validation, degrade-to-empty on
  missing/corrupt JSON, and `swtk_product()` sourcing the CTA from the
  committed product registry (no duplicated buy-URL constants — the registry
  loader already applies `?ref=fleet-store` and the live-only rule).
- `GET /stripe-gotchas` route + NAV entry in `botsite/app.py` (docstring in
  the sibling clarity/provenance/honest-CTA idiom);
  `botsite/templates/stripe_gotchas.html` — `sb-page-hero` + honest lede,
  six symptom → fix cards, the kit's four checks + honest limits in the CTA,
  cross-links to /products, /field-manual, /agent-pr-check, and honest empty
  states.
- `botsite/tests/test_stripe_gotchas.py` — 13 tests: render + all six
  titles, clarity lede, exact `?ref=fleet-store` buy href, honest-CTA
  content, cross-links, provenance on-page, nav, degradation
  (missing/corrupt file), loader validation, committed-data honesty, and
  registry-sourced product facts. The page also rides the existing
  `test_clarity_structure.py` route walk automatically (non-parameterized
  HTML GET).
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — 1157 passed (was 1144; +13 new gotchas tests);
  `python3 bootstrap.py check --strict` — green after this card's designed
  born-red hold was released at the flip.

⚑ Self-initiated: yes — ORDER 022 item 4 generative mandate (venture
WEBSITE-IDEA batch-2 "SWTK gotchas microsite"); contained (new page + data +
loader inside botsite, no existing behavior changed, GET-only, no payment
handling) and reversible (delete the page/data to revert).

## 💡 Session idea

**Shared provenance schema for committed cross-repo data** — a tiny
`botsite/provenance.py` (validator + a single test) that every
`botsite/data/*.json` provenance block must satisfy (repo, path(s), full
sha, retrieved date), replacing the per-loader reimplementations in
`field_manual.py` / `stripe_gotchas.py` and giving un-provenanced data files
nowhere to hide. Worth having because the honesty doctrine currently relies
on each new page re-implementing provenance validation by hand, and that
drifts silently as pages multiply. Deduped against `docs/ideas/backlog.md` +
the queue-state NEXT list: nearest neighbor is the storefront `as_of`
freshness pin (staleness, not schema) — no overlap. Capture in
`docs/ideas/backlog.md` is deferred: this worker's assigned scope excludes
`docs/**`, so the bullet rides here for the coordinator/next session to land.

## ⟲ Previous-session review

The venture-products-page session (PR #232) did well — a committed registry
+ validating loader + honesty tests that this page reuses wholesale for its
CTA; what it missed is that the one live product's best content (the gotchas
themselves) stayed buried in venture-lab, which is exactly the gap this
session closes.
