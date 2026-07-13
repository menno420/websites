# 2026-07-13 — botsite vetting catalog: venture's full pipeline at /products/catalog

> **Status:** `complete` — PR #248, branch `claude/venture-vetting-catalog`;
> the venture publishing pipeline's 22 vetted titles & products now render
> at /products/catalog in honest status groups (1 live / 12 publish-ready /
> 2 hard-gated / 7 parked), curated as committed JSON from venture-lab
> @ `2c039e3`; lands via the auto-merge enabler on green.

- **📊 Model:** Claude Fable 5 · worker · initiation-slice

**What this session was about:** initiation under ORDER 022 item 4
(`control/inbox.md` — venture WEBSITE-IDEA markers are priority intake).
The marker (venture-lab `control/outbox.md` @ `d56ec31`, verbatim):
"WEBSITE-IDEA: static catalog/storefront page auto-generated from
docs/publishing/vetting/*.md + OWNER-QUEUE.md — the vetting pipeline is
already structured data (source: books lane)." The /products page
(PR #232) is the 4-item store; this session curated the FULL vetting
pipeline — 22 packets + the derived OWNER-QUEUE — into a committed
`botsite/data/catalog.json` rendered at a linked subpage
`/products/catalog`, with honest per-title states and a buy link only for
the one actually-live product.

## What was done

- `botsite/data/catalog.json` — 22 entries curated by hand from
  venture-lab `docs/publishing/vetting/*.md` + `OWNER-QUEUE.md`
  @ `2c039e3` (each status derived from that packet's own Status
  blockquote + Verdict paragraph; nothing invented). Breakdown: 1 live
  (Stripe Webhook Test Kit — the Gumroad URL from OWNER-QUEUE §4, the
  page's only buy link), 12 publish-ready (incl. the three NL editions
  with their EN-first sequencing / proofread gates noted honestly),
  2 hard-gated (bundle-starter on its component clicks, photo-packs on
  owner-held originals), 7 parked (six concept-stage "no manuscript"
  packets + The Painted Stones at its §5 illustration gate).
- `botsite/catalog.py` — loader mirroring `products.py`: stdlib-only,
  degrade-to-empty, skip-invalid, buyable only when live AND url,
  `?ref=fleet-store` on outbound; plus `group_by_status()`.
- `botsite/app.py` GET `/products/catalog` +
  `botsite/templates/catalog.html` (sb-page-hero + h1 + sb-lead,
  status-grouped cards with price/category/status_note/provenance,
  honest empty state). UI shape: a linked subpage, NOT growing
  /products — one link stub on `products.html` (hidden when the catalog
  is empty), no new top-nav entry.
- `botsite/tests/test_catalog.py` — 15 network-free tests incl. the
  `test_committed_registry_is_honest` pin (22 entries, unique slugs,
  1/12/2/7 status breakdown, every source @ 2c039e3); the structural
  clarity gate (PR #241) auto-walks the new page green.
- `docs/ideas/backlog.md`: this session's 💡 captured as a new bullet.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — 1057 passed, 1 warning (+15 over main's 1042);
  `python3 bootstrap.py check --strict` — green except this card's own
  designed born-red HOLD (flipped by this commit) and the pre-existing
  never-exit-affecting `owner-action-fields` advisory on
  control/status.md (not owned here).

⚑ Self-initiated: yes — an initiation under ORDER 022 item 4's standing
venture-marker intake (marker source: venture-lab `control/outbox.md` @
`d56ec31`); contained (botsite/** + committed JSON only, no live
cross-repo fetch, no payment surface, no nav change) and reversible
(delete the route, template, loader and data file).

## 💡 Session idea

**Catalog sha-drift pin — nag when the vetting catalog's pinned source sha
falls behind venture-lab HEAD** — every catalog.json entry pins venture-lab
@ `2c039e3`; a scheduled or CI-time check comparing that pin against
venture-lab's current HEAD for `docs/publishing/vetting/` + `OWNER-QUEUE.md`
(one raw-content read over the existing read-only channel) would nag when
packets changed upstream while the committed catalog still claims them.
Worth having because a 22-entry hand-curated registry decays the moment the
vetting lane moves — a title going live upstream while the page still says
publish-ready is exactly the dishonesty this page exists to avoid. Deduped
against `docs/ideas/backlog.md` + the queue-state NEXT list: the
storefront-freshness bullet is TIME-based (`as_of` horizon, products.json
only); nothing compares pinned source shas against upstream, and nothing
covers catalog.json. Captured in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

The model-line-hygiene session (PR #226) did well — it fixed the template
at the source AND proved the kit wasn't the origin (so the fix sticks
without upstream routing) before sweeping 102 historical cards in one
clean, single-line-per-card pass; what it missed: the protection is still
sweep-shaped — its proposed exact-ID gate advisory lives only as a backlog
bullet, so regressions still depend on card authors' discipline.
