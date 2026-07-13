# 2026-07-13 — botsite: /field-manual free-chapter funnel page

> **Status:** `complete` — branch `claude/field-manual-funnel`; lands via
> the auto-merge-enabler on green.

- **📊 Model:** Claude Fable 5 · worker · feature-slice

**What this session was about:** ORDER 022 item 4 follow-through — venture
WEBSITE-IDEA batch-2 intake, marker "field-manual free-chapter funnel page"
(venture-lab `control/outbox.md`, batch 2, @ 0679327). Goal: a GET-only
botsite marketing page `/field-manual` for the **Agent Fleet Field Manual**
($39, `botsite/data/catalog.json`, publish-ready but not yet purchasable).

## What was done

- **Data** `botsite/data/field_manual.json`: the book pitch (tagline,
  description, feature bullets, the 11-chapter list with the kit's 2 free
  chapters marked, who-it's-for, the honest "What it is NOT" list) curated
  from the launch kit's `LISTING.md` + `one-pager.md`, and the free chapter
  (ch. 1, "The D1 Lesson") as structured blocks — the kit's own funnel plan
  designates chapter 1 as the first free chapter. Explicit provenance
  committed in-file: repo `menno420/venture-lab`, path
  `docs/launch/agent-fleet-field-manual/chapter-01-the-d1-lesson.md`,
  commit `0679327a463c063dcd9fc62b33ffb9a3789fa7d3`, retrieved 2026-07-13.
  Committed-data pattern: nothing fetched cross-repo on the request path.
- **Loader** `botsite/field_manual.py`: validating read-only loader in the
  `puddle_museum.py` idiom (degrade to empty on missing/corrupt file, skip
  invalid blocks/chapters, never crash); `catalog_entry()` finds the book
  in the committed vetting catalog; `buy_url()` returns a link ONLY when
  the catalog entry carries a real `url` (with `ref=fleet-store`
  attribution) — the single condition under which a buy button may render.
- **Route** `GET /field-manual` in `botsite/app.py` (+ NAV entry): pitch,
  chapter list, honest CTA, the free chapter rendered readably, provenance
  line, cross-links to `/products` and `/products/catalog`. Honest CTA both
  ways: today (url null) the page says the publish click is queued to the
  owner and renders zero buy/store links; the moment the committed catalog
  gains a url, the page shows it automatically.
- **Template** `botsite/templates/field_manual.html`: `sb-page-hero` +
  `<h1>` + `p.sb-lead` per the structural clarity gate (#241); honest empty
  states for missing pitch/excerpt halves.
- **Tests** `botsite/tests/test_field_manual.py` (23, all offline): page
  200 + clarity hero; pitch, chapter list, honesty list; excerpt content +
  provenance sha; both cross-links in every CTA state; honest CTA pinned
  against the committed url-less entry (no "Buy —", no gumroad.com
  anywhere); buy link appears from a tmp catalog with a url (both live and
  status-lagging states); entry-missing fallback; missing/corrupt data
  degradation; loader unit coverage; a pin that the committed catalog entry
  is still publish-ready + url-less.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — 1144 passed (635 + 299 + 60 + 150), 0 failed, 1
  warning; `python3 bootstrap.py check --strict` — green apart from this
  card's own designed born-red HOLD (flipped by this commit) and the
  pre-existing `owner-action-fields` advisory on control/status.md (never
  exit-affecting, not owned here).

**Decisions made:** the CTA wires on the catalog entry's `url` itself
rather than `status == "live"` — a real store URL is honest to link the
moment it exists even if the status field lags a beat, and no URL means no
button regardless of status; both states are test-pinned. The excerpt is
committed as structured blocks (not raw markdown) so it renders with
stdlib only — no new dependency, no `|safe` HTML injection surface.

⚑ Self-initiated: yes — INITIATION lane, ORDER 022 item 4's standing
"treat venture's WEBSITE-IDEA markers as priority intake"; no per-slice
routing existed.

## 💡 Session idea

**Single funnel-CTA helper for catalog-backed pages** — `/agent-pr-check`
gates its Merge-Wall Cookbook CTA on `has_link` (live+url) while
`/field-manual` gates on url-presence via `field_manual.buy_url()`; a
third catalog-backed page would make three hand-rolled CTA wirings. Move
the "entry → honest CTA state" derivation into `botsite/catalog.py` as one
helper both templates consume, with a pin that no template renders a buy
href outside it. Worth having because the store's whole promise is "a buy
link only when really purchasable", and that promise currently lives in N
per-page implementations. Deduped against `docs/ideas/backlog.md` at HEAD:
no existing bullet covers CTA unification.

## ⟲ Previous-session review

The agent-PR diagnostic tree session (#255, merged at this branch's base)
did well — its honest coming-soon CTA for the Merge-Wall Cookbook was the
direct pattern this page reused, and its committed-data + loader + gate
conformance shape transplanted cleanly. One miss: it hardcoded the
cookbook slug lookup inline in the route rather than in its data module,
which is why this session put `catalog_entry()` in `field_manual.py` —
the route stays declarative.
