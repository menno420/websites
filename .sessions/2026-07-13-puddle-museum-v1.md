# 2026-07-13 — The Puddle Museum: botsite book marketing page + emoji exhibit gallery

> **Status:** in-progress — branch `claude/puddle-museum-v1`.

- **📊 Model:** Fable 5 · worker · botsite page build

**What this session is about:** ORDER 022 item 4 — venture WEBSITE-IDEA
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

## Goal

Ship `/puddle-museum` on botsite: `botsite/puddle_museum.py` (loader),
`botsite/data/puddle_museum.json` (committed data @ venture-lab 467d619),
`botsite/templates/puddle_museum.html`, `botsite/tests/test_puddle_museum.py`,
one NAV tuple in `botsite/app.py`. Honesty gates: zero buy links, zero
forms, no fake images — the collection is text and emoji until the book's
illustrations exist.
