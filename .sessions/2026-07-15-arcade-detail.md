# 2026-07-15 — Arcade: per-game detail pages with launch-blocker panels

> **Status:** `in-progress`

- **📊 Model:** Claude Fable · medium · feature build (botsite /arcade/{slug} detail pages + blocker panels)

**What this session is about:** the FLEET ARCADE front door gets depth.
Today `/arcade` is a flat 3-card catalog — a visitor can see THAT a game
isn't playable but not WHY, and there is nowhere to go deeper. This slice
adds a server-rendered detail page per game at `/arcade/{slug}`, driven
entirely by the committed `botsite/data/arcade.json` (no new outbound
network surface — botsite keeps fetching only superbot's committed JSON
via `data_source.py`, and the arcade registry stays a disk read):

- each catalog card links to its detail page;
- an available game's page carries the same honest play affordance the
  catalog already offers (link only when really reachable, `ref=fleet-arcade`);
- an unavailable game's page renders a structured "What's blocking launch"
  panel: the blocker already recorded in the registry, stated plainly as
  the named owner click, plus a "how it unblocks" line;
- unknown slug → the site's standard 404 (`not_found.html`);
- GET-only, no forms — the CSRF floor is untouched.

The registry is hand-maintained (no `gen_*.py` owns `arcade.json`; the
drift probe reads it through the same loader), so the schema is extended
minimally in place: an optional `blocker` object (`owner_action`,
`unblocks`) on the two unavailable games, faithful to their existing
`status_note` prose — honest rendering only, no invented status, no live
probes.

⚑ Self-initiated: no — dispatched under the owner's live work grant
(accept-edits session mode), coordinator-approved mission slice.

## Close-out

**Evidence:**

- files touched this branch: [[fill: files]]
- git: [[fill: branch/PR]]
- verify: [[fill: pytest + strict-check lines]]

**Judgment:**

- Decisions made: [[fill: decisions]]
- Next session should know: [[fill: handoff]]

## 💡 Session idea

[[fill: idea]]

## ⟲ Previous-session review

[[fill: review of .sessions/2026-07-15-launch-preflight-verdicts.md]]
