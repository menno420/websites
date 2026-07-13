# 2026-07-13 — botsite: /field-manual free-chapter funnel page

> **Status:** `in-progress` — branch `claude/field-manual-funnel`; born-red
> until this line flips at close.

- **📊 Model:** Claude Fable 5 · worker · feature-slice

**What this session is about:** ORDER 022 item 4 follow-through — venture
WEBSITE-IDEA batch-2 intake, marker "field-manual free-chapter funnel page"
(venture-lab `control/outbox.md`, batch 2, @ 0679327). Goal: a GET-only
botsite marketing page `/field-manual` for the **Agent Fleet Field Manual**
($39, `botsite/data/catalog.json`, publish-ready but not yet purchasable):
the book pitch built from the committed catalog entry + launch-kit copy, the
kit's designated free chapter (chapter 1, "The D1 Lesson") committed as data
with explicit provenance (repo, path, sha, retrieved date — no live
cross-repo fetch on the request path), cross-links to `/products` and
`/products/catalog`, and an HONEST CTA: while the catalog entry carries no
`url` the page says the publish click is queued to the owner and renders no
buy link; the moment the committed catalog gains a `url` for the entry, the
page automatically shows it as the buy link (both states test-covered).
Conforms to the structural clarity gate (`test_clarity_structure.py`, #241).

## What was done

(in progress)
