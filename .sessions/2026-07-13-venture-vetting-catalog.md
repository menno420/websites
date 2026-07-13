# 2026-07-13 — botsite vetting catalog: venture's full pipeline at /products/catalog

> **Status:** `in-progress` — branch `claude/venture-vetting-catalog`; flips to `complete`
> + PR number as the deliberate LAST code step.

- **📊 Model:** Claude Fable 5 · worker · initiation-slice

**What this session is about:** initiation under ORDER 022 item 4
(`control/inbox.md` — venture WEBSITE-IDEA markers are priority intake).
The marker (venture-lab `control/outbox.md` @ `d56ec31`, verbatim):
"WEBSITE-IDEA: static catalog/storefront page auto-generated from
docs/publishing/vetting/*.md + OWNER-QUEUE.md — the vetting pipeline is
already structured data (source: books lane)." The /products page
(PR #232) is the 4-item store; this session curates the FULL vetting
pipeline — 22 packets + the derived OWNER-QUEUE — into a committed
`botsite/data/catalog.json` rendered at a linked subpage
`/products/catalog`, with honest per-title states (live / publish-ready /
hard-gated / parked) and a buy link only for the one actually-live
product.

## What was done

- `botsite/data/catalog.json` — 22 entries curated by hand from
  venture-lab `docs/publishing/vetting/*.md` + `OWNER-QUEUE.md`
  @ `2c039e3` (statuses derived from each packet's Status blockquote +
  Verdict paragraph; nothing invented; exactly 1 live entry — the
  Stripe Webhook Test Kit's Gumroad URL per OWNER-QUEUE §4).
- `botsite/catalog.py` — loader mirroring `products.py` (stdlib-only,
  degrade-to-empty, skip-invalid, buy-link only when live AND url,
  `?ref=fleet-store` on outbound).
- `botsite/app.py` GET `/products/catalog` +
  `botsite/templates/catalog.html` (sb-page-hero + sb-lead, grouped by
  status, per-card provenance, honest empty state); one link stub on
  `products.html` — no new top-nav entry.
- `botsite/tests/test_catalog.py` — network-free suite incl. the
  committed-registry honesty pin.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — pending (filled at flip); `python3 bootstrap.py
  check --strict` — pending (filled at flip).

⚑ Self-initiated: yes — an initiation under ORDER 022 item 4's standing
venture-marker intake (marker source: venture-lab `control/outbox.md` @
`d56ec31`); contained (botsite/** + committed JSON only, no live
cross-repo fetch, no payment surface) and reversible (delete the route +
data file).

## 💡 Session idea

**Catalog freshness pin against venture-lab HEAD** — a scheduled or
kit-gate advisory that compares `botsite/data/catalog.json`'s pinned
source sha (`2c039e3`) against venture-lab's current HEAD vetting
directory and nags when packets changed (draft — refined at flip).
Worth having because a hand-curated committed registry decays silently
the moment the vetting lane moves. Dedup check against
`docs/ideas/backlog.md` pending at flip.

## ⟲ Previous-session review

(drafted, refined at flip) The model-line-hygiene session (PR #226) swept
102 historical cards cleanly and fixed the template at the source; review
finalized at flip.
