# 2026-07-18 — Cross-link /games ↔ /arcade (A2)

> **Status:** `complete` — branch `claude/arcade-games-crosslink`; the two
> overlapping game surfaces on botsite — `/games` (mini-games that run in chat)
> and `/arcade` (the fleet's playable-games catalog) — were only reachable in
> ONE direction: `/games` already carries an "Explore the Arcade" cross-link
> (`games.html`), but `/arcade` had no link back to `/games`, a dead end for a
> visitor who lands on the arcade first. A2 adds the missing reverse link on
> `arcade.html`, mirroring the existing games→arcade strip's style/placement, so
> the two surfaces are mutually reachable. Template + nav only — no product
> logic, no serialized JSON/env, no route change; all links are GET, so the
> CSRF/same-origin floor is untouched.

- **📊 Model:** Claude Opus · high · feature build — botsite /arcade↔/games nav

**What this session is about:** botsite presents games across two surfaces that
overlap in intent — `/games` lists the in-chat mini-games and casino modes, and
`/arcade` is the public catalog of the fleet's playable games with honest
maturity/availability labels. `/games` already links across to `/arcade` (the
"Fleet Arcade … Explore the Arcade →" strip under its hero), but the arcade page
offered no way back, leaving a visitor who arrives at `/arcade` first at a
dead end relative to the in-chat games. A2 closes the loop with a single reverse
link on `arcade.html`.

⚑ Self-initiated: no — coordinator-dispatched backlog slice (A2).

## Close-out

**Evidence:**

- files touched this branch:
  - `botsite/templates/arcade.html` — a reverse cross-link strip to `/games`,
    placed directly under the page hero (before the `{% if arcade_games %}`
    catalog block) so it renders regardless of registry state; a muted
    `section-sm` strip mirroring the games→arcade twin — a bold `In chat:`
    label, a one-line blurb, a `·` separator, and an `<a href="/games">Play in
    chat →</a>` chevron link (`icon("chevron", 12)`, the same affordance the
    games page uses for "Explore the Arcade").
  - `botsite/tests/test_arcade.py` — two assertions (below).
- test coverage (2): `test_arcade_links_back_to_games` — `/arcade` renders
  `href="/games"` (the new reverse half); `test_games_links_to_arcade` — `/games`
  renders `href="/arcade"` (the already-shipped half), so a regression on EITHER
  surface is caught and the mutual-reachability invariant is pinned in one file.
- git: branch `claude/arcade-games-crosslink` from `origin/main` @ `85539e0`
  (#392); commits `e7925e0` (born-red card), `e76c81d` (the reverse-link
  template change), `a4ac524` (the 2 tests), `cd2c975` (heartbeat status), +
  this flip.
- verify: `python3 -m pytest tests/ botsite/tests dashboard/tests review/tests -q`
  — **1806 passed, 1 warning** (exit 0; 1804 + 2 new); `python3 bootstrap.py
  check --strict` and `--require-session-log` (the CI form) — both exit 0, the
  only red the DESIGNED born-red hold on this card, released at this flip. The
  one advisory warning is on another session's card
  (`2026-07-17-arcade-owner-action-queue.md`, an off-PL-004 `botsite-feature
  build` task-class segment), pre-existing and not this work — noted here as the
  reason this card uses the valid `feature build` class instead.

**Judgment:**

- Decisions made: (1) Placement — put the reverse strip directly under the hero,
  BEFORE the `{% if arcade_games %}` block, so it renders even when the arcade
  registry is empty/unreadable (the arcade's own degraded state still offers the
  way back to /games); the games→arcade twin sits in the same post-hero slot, so
  the two pages are now structurally symmetric. (2) Markup — reused the existing
  `sb-muted section-sm` strip + `sep` + `icon("chevron")` vocabulary verbatim
  rather than inventing a button/panel, so the twin links read as one system and
  nothing new lands in the CSS. (3) Scope — no data dependency: the reverse link
  is static markup (the arcade→games direction needs no summary counts), unlike
  the games→arcade strip which is gated on `arcade_summary.total`; keeping it
  unconditional is what makes it a dead-end fix rather than another conditional
  surface.
- Next session should know: the two cross-links are now hand-maintained twins —
  `games.html`'s "Explore the Arcade" strip and `arcade.html`'s "Play in chat"
  strip each hardcode the other surface's blurb + href. If a third overlapping
  surface appears, single-source the pairing (see the idea below) rather than
  adding a third bespoke strip.

## 💡 Session idea

**A link-graph "no internal dead end" test.** This A2 fix was a manually-spotted
dead end: `/arcade` simply had no link back to `/games`, and nothing failed —
every page still returned 200. A lightweight botsite test could render the nav +
each page's in-body anchors, build the internal-link graph over the known routes,
and assert that every internal surface both is reachable from another page AND
links onward (no orphan, no sink) — catching the NEXT one-way dead end
automatically instead of by eye. It reuses the existing `TestClient` fixture and
the route list already enumerated in `test_botsite.py`'s status-code parametrize;
the only new machinery is a regex over rendered `href="/…"` internal links. It is
distinct from the current per-page 200 checks (those prove a page loads, not that
it is reachable or non-terminal) and from the two bespoke cross-link asserts this
PR adds (which pin one pair by name).

## ⟲ Previous-session review

`.sessions/2026-07-18-durable-ask-ids.md` (C15) replaced the owner-queue
writeback's brittle headline-text ask handle with a durable content-derived
`ask_uid`, so a resolution always points at the intended ask; A2 is the trivial
nav cousin of the same instinct — a reference that was incomplete/fragile (a
one-way link, a dead end) made robust — pinned, like C15, by a test that asserts
the property directly rather than trusting the surface.
