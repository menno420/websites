# 2026-07-15 — Arcade: per-game detail pages with launch-blocker panels

> **Status:** `complete` — PR #349, branch `claude/arcade-detail-20260715`;
> new route `/arcade/{slug}` + `arcade_detail.html`, catalog cards link
> through, unavailable games render a structured "What's blocking launch"
> panel from the registry's new optional `blocker` object.

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

- files touched this branch: `.sessions/2026-07-15-arcade-detail.md` +
  `control/claims/claude-arcade-detail-20260715.md` (first commit; claim
  deleted at this flip), `botsite/data/arcade.json` (optional `blocker`
  object on lumen-drift + games-web, faithful to their status notes),
  `botsite/arcade.py` (`_normalized_blocker` fail-soft validation,
  `detail_url` derivation, `game_by_slug()`), `botsite/app.py` (GET
  `/arcade/{slug}`, feature_detail pattern, standard 404),
  `botsite/templates/arcade_detail.html` (new — detail head + blocker /
  status panels), `botsite/templates/arcade.html` (card title + Details
  link route to the detail page), `botsite/tests/test_arcade.py` (+16 test
  items: detail 200 per slug, 404 unknown, both blocker panels, mineverse
  play affordance with attribution ref, catalog links, blocker schema
  guard incl. 6 malformed-blocker degrade cases, committed-registry
  blocker pin), `botsite/tests/test_clarity_structure.py` (`_arcade_urls`
  expander registers `/arcade/{slug}` so the structural clarity gate walks
  every game page — the gate caught the unregistered route on first run,
  working as designed).
- arcade.json ownership verified before editing: hand-maintained — the
  only generator in the repo is `botsite/gen_graveyard.py` (graveyard);
  `arcade_probe.py` and the healthcheck only READ arcade.json through
  `arcade.load_games`.
- git: branch `claude/arcade-detail-20260715`, based on `main` @
  `4b7c20c`; PR #349. Work in an isolated `git worktree` (the recorded
  EnterWorktree wall — manual worktree substitute).
- verify: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — **1458 passed, 1 warning** (was 1442 at base; +16);
  `python3 bootstrap.py check --strict` — green except the DESIGNED
  born-red hold on this card (released by this flip).

**Judgment:**

- Decisions made: (1) the `blocker` field is OPTIONAL and fail-soft — a
  missing/malformed blocker normalizes to `None` and never invalidates the
  game entry; the panel then falls back to `status_note`, and to an honest
  "no blocker recorded" line below that — degrade, don't invent; (2) the
  detail route reads through the SAME loader as the catalog
  (`game_by_slug` wraps `load_games`), so the two surfaces can never
  disagree about which games exist or what they claim — the
  `LINKED_AVAILABILITIES` single-source-of-truth pattern applied to
  routes; (3) blocker copy was transcribed from the existing status_note
  prose (release click for lumen-drift, the Pages settings click for
  games-web), not authored fresh — no new claims entered the registry.
- Next session should know: the release-drift banner idea (page-level
  banner when a blocker has cleared upstream but the registry still says
  unavailable) is a coordinator-flagged FOLLOW-UP, deliberately not built
  here — it would add a network surface or a healthcheck join, both out of
  this slice's scope rail. When an owner click lands (lumen-drift release
  / product-forge Pages), flip the registry entry: set `availability` +
  `url`, drop the `blocker` — the detail page then swaps the panel for the
  real button automatically.

## 💡 Session idea

**One structured blocker schema across all public registries** — arcade's
new `blocker: {owner_action, unblocks}` object names the exact owner click
between a card and launch. The other botsite registries carry the same
information as unstructured prose: `catalog.json`'s hard-gated/parked
entries, `products.json` coming-soon notes, `puddle_museum.json`'s
no-edition state. If they adopted the same optional object, (a) every
"not live yet" public card could render the same honest "what's blocking
launch" panel, and (b) the gated `/owner` console could aggregate every
public-facing blocker into one list and join it against the OWNER-ACTIONS
ledger's asks (askverify already probes two of arcade's blockers — the
lumen-drift release tag and product-forge Pages status), so the owner
sees which public promises each errand unblocks. Deduped against
`docs/ideas/backlog.md`: no structured-blocker / owner-click-schema bullet
exists (blockers appear only in the enrich-continuation fix at line 699
and the lumen-drift flip note at line 853, neither a schema proposal).

## ⟲ Previous-session review

`.sessions/2026-07-15-launch-preflight-verdicts.md` is this card's format
reference and its close-out compounded here twice: its recorded worktree
wall (manual `git worktree add` substitute for EnterWorktree) was consumed
verbatim by this session's isolation setup, and its probe inventory
(gba-homebrew `lumen-drift-v1.3` release tag + product-forge Pages status
as public GETs) independently confirms the two blockers this session
rendered as panels are real, machine-checked owner clicks — the public
arcade page and the gated owner console now tell the same story from the
same facts, which is exactly what honest close-outs are for. Improvement
it points at: its verdict chips and this session's blocker panels share no
join key — the stable ask-ID idea that card filed would give the arcade
`blocker` objects an `ask_id` to reference, and both surfaces would flip
from one ledger edit. Still worth promoting.
