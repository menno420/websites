# 2026-07-13 — The Puddle Museum: botsite book marketing page + emoji exhibit gallery

> **Status:** complete — branch `claude/puddle-museum-v1`; PR #247.

- **📊 Model:** Fable 5 · worker · botsite page build

**What this session was about:** ORDER 022 item 4 — venture WEBSITE-IDEA
intake for "The Puddle Museum", the rainy-day picture-book venture
(venture-lab `control/outbox.md` WEBSITE-IDEA marker; vetting packet landed
in venture-lab PR #105, the EN/NL/DE manuscripts in PR #121). Build the
botsite page that presents the book concept: a `/puddle-museum` route with a
curated emoji exhibit gallery (six exhibits from the packet, trilingual
names), the three edition cards (EN "The Puddle Museum", NL "Het
Regenplassenmuseum", DE "Das Pfützenmuseum") shown honestly as coming-soon —
no buy links because none exist — and an honest "submissions open soon"
teaser (no form; the same storage + moderation wall as botsite `/submit`).
Follows the products-page idiom exactly (PR #232): committed JSON with
per-entry `source` + `as_of` provenance, stdlib-only loader with honest
empty states, GET-only route, structural clarity gate satisfied
(`section.sb-page-hero` h1 + `p.sb-lead`, PR #241).

⚑ Self-initiated: no — coordinator-dispatched ORDER 022 item 4 venture
WEBSITE-IDEA intake ("The Puddle Museum", venture-lab control/outbox.md
marker, PR #105 packet + PR #121 manuscripts).

## What was done

- **`botsite/data/puddle_museum.json`** — committed data, every entry with
  `source` + `as_of: "2026-07-13"`: 6 exhibits (Sky Mirror 🪞,
  Upside-Down Tree 🌳, Worm Rescue Wing 🪱, Splash Gallery 💦, Puddle of
  Many Colors 🌈, The Whale 🐋 — trilingual names where the packet gave
  them, omitted where not) + 3 editions (EN/NL/DE), all
  `availability: "coming-soon"`, `url: null` — verified: zero store URLs
  exist in venture-lab, so zero buy links ship here.
- **`botsite/puddle_museum.py`** — read-only loader mirroring
  `botsite/products.py`: disk read at request time, stdlib only, no
  network; missing/corrupt file → empty structures; `_valid_*` skip
  malformed entries; an edition is buyable ONLY if `availability == "live"`
  AND a url — with shipped data nothing is buyable.
- **`botsite/templates/puddle_museum.html`** — hero (sb-page-hero h1 +
  sb-lead), the sign callout ("OPEN TODAY ONLY — ADMISSION: ONE LEAF"),
  the packet blurb verbatim, emoji exhibit grid (honestly labeled: text and
  emoji until the book's illustrations exist), edition cards with
  coming-soon badges and no buy buttons, honest submissions teaser (no
  form), closing line quoted.
- **`botsite/app.py`** — one NAV tuple + one GET-only `/puddle-museum`
  route in the products-route shape.
- **`botsite/tests/test_puddle_museum.py`** — 16 network-free tests: page
  200 + h1 + sb-lead, all six exhibits, all three edition titles, honesty
  gates (no amazon/gumroad/store hrefs, no `<form`, buy button never
  renders), coming-soon + status notes visible, submissions teaser,
  verbatim sign + closing line, provenance rendered, nav link, loader
  degradation (missing/corrupt/wrong-shape → empty; invalid entries
  skipped; live-without-url never buyable), committed data nothing buyable.
- **`docs/botsite.md`** — `/puddle-museum` row added to the route table.

**Copy sources:** venture-lab `docs/publishing/vetting/the-puddle-museum.md`
+ `candidates/childrens-books/the-puddle-museum/the-puddle-museum.{en,nl,de}.md`
@ `467d619` (PRs #105 / #121).

**Verified:** `python3 -m pytest tests/ botsite/tests dashboard/tests
review/tests -q` — **1058 passed, 1 warning** (1042 baseline at origin/main
1a411d1 + 16 new, zero failures); `python3 bootstrap.py check --strict` —
green apart from this card's own designed born-red hold (cleared by this
flip) and the pre-existing never-exit-affecting owner-action advisory on
`control/status.md` (untouched by scope). The clarity structural gate
(botsite/tests/test_clarity_structure.py) walked the new page automatically
and passed.

**Evidence:** commits `bd6b9e3` (rails), `07f639e` (build + docs), plus this
flip; PR #247. Files touched this session: `botsite/puddle_museum.py`,
`botsite/data/puddle_museum.json`, `botsite/templates/puddle_museum.html`,
`botsite/tests/test_puddle_museum.py`, `botsite/app.py` (import + NAV tuple
+ route), `docs/botsite.md` (one table row), this card, and the claim file
(created at rails, removed at close).

**Decisions made:** exhibit descriptions written faithfully from the packet
(kid-friendly, one-two sentences) rather than quoted, since the packet gives
names + concept per exhibit, not per-exhibit prose; the two verbatim quotes
(the sign + the closing line) and the blurb are quoted exactly. Edition
cards carry `language` as a display field alongside `lang`. The buy-link
branch exists in the template but is provably unreachable with shipped data
(pinned by test).

**Next session should know:** when an edition goes live, flip its
`availability` to `"live"` and set a real store `url` in
`botsite/data/puddle_museum.json` — the loader + template + tests already
handle the transition; when the submissions wall falls (plan Q5 storage +
moderation), replace the teaser panel, and mirror whatever `/submit` does.

## 💡 Session idea

**Extract the committed-registry loader pattern into one shared helper** —
`products.py` and `puddle_museum.py` now duplicate the same idiom line for
line: read committed JSON at request time, degrade to empty on
missing/corrupt, `_valid()` skip, derive an is-live/is-buyable flag that
gates every outbound link. A third registry (the next venture intake will
want one) makes it three copies of the same honesty machinery. A tiny
`botsite/registry.py` (`load_registry(path, required, enrich)`) would keep
each data module to its schema + enrichment lambda, and the honesty rules
would live in exactly one audited place. Deduped: `docs/ideas/backlog.md`
has no bullet about registry/loader convergence.

## ⟲ Previous-session review

The clarity-structural-gate session (PR #241) paid off concretely here: my
new route was walked and held to the header idiom by a test I never had to
write — the gate absorbed a brand-new page with zero configuration, exactly
the "structural instead of page-by-page" promise. One workflow improvement
it suggests: the gate asserts headline + lede but not honest-empty-state
copy; pages built on committed registries (products, now puddle-museum) all
hand-roll a "Nothing is faked here" empty card, and a shared include (or a
gate check that a registry-backed page renders SOMETHING honest when its
loader returns empty) would pin that half of the doctrine structurally too.
