# 2026-07-13 — botsite /products: the fleet's storefront for venture-lab's products

> **Status:** `complete` — branch `claude/venture-products-page`, PR #232
> (READY + targeting main; merge is the coordinator/owner's call — this
> worker opens, never merges).

- **📊 Model:** Claude Fable · worker · self-initiated build slice

**What this session was about:** self-initiated rung — ORDER 022 item 4 (the
generative mandate). venture-lab has four sellable products (one live on
Gumroad, three publish-click-queued) and the fleet's public site had no page
that shows them. This session gives botsite a `/products` storefront page in
the arcade idiom: a committed registry (`botsite/data/products.json`, curated
from venture-lab launch copy @ e01fa01 — cross-repo data arrives only as
committed JSON), a validating loader, honest LIVE / COMING SOON labels, and a
buy link only for the one product that is really purchasable.

## What was done

- `botsite/data/products.json` — four products curated from venture-lab
  launch docs @ e01fa01, each with price, availability, per-entry `as_of`,
  and a `source` citation; only the live SWTK carries a URL.
- `botsite/products.py` — loader mirroring `arcade.py`: required-field
  validation, availability whitelist, never-buyable-without-live+url,
  `?ref=fleet-store` attribution, degrade-to-empty on missing/corrupt JSON.
- `GET /products` route + NAV entry in `botsite/app.py`;
  `botsite/templates/products.html` with honest badges and empty state.
- `botsite/tests/test_products.py` — page render, live-link, no-dead-link,
  degradation, loader, and committed-registry honesty tests.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — 927 passed (was 915; +12 new products tests);
  `python3 bootstrap.py check --strict` — green after this card's designed
  born-red hold was released at the flip.

⚑ Self-initiated: yes — ORDER 022 item 4 generative mandate; contained (new
page + registry inside botsite, no existing behavior changed, GET-only, no
payment handling) and reversible (delete the page/registry to revert).

## 💡 Session idea

**Storefront freshness pin** — a CI-time (or /products-page) check comparing
each `botsite/data/products.json` entry's `as_of` date against a staleness
horizon (~14 days), nagging when the curated registry has not been re-verified
against venture-lab. Worth having because a hand-curated storefront silently
drifts from reality the moment a product goes live or changes price, and the
honesty doctrine dies quietly through staleness, not lies. Deduped against
`docs/ideas/backlog.md` + the queue-state NEXT list: nearest neighbors are
tester-task `product_url` liveness pins — none cover registry as-of staleness.
Captured in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

The clarity-control-plane session (PR #229) did well — template-level fixes
that whole page families inherit, with pinning tests; it missed nothing this
lane depends on, and its clarity bar is adopted here as this page's binding
header standard.
