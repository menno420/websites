# 2026-07-18 — Cross-link /games ↔ /arcade (A2)

> **Status:** `in-progress` — branch `claude/arcade-games-crosslink`; the two
> overlapping game surfaces on botsite — `/games` (mini-games that run in chat)
> and `/arcade` (the fleet's playable-games catalog) — were only reachable in
> ONE direction: `/games` already carries an "Explore the Arcade" cross-link
> (`games.html`), but `/arcade` had no link back to `/games`, a dead end for a
> visitor who lands on the arcade first. A2 adds the missing reverse link on
> `arcade.html`, mirroring the existing games→arcade link's style/placement, so
> the two surfaces are mutually reachable. Template + nav only — no product
> logic, no serialized JSON/env, no route change; all links are GET.

- **📊 Model:** [[fill: model · effort · feature build]]

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
  - [[fill: botsite/templates/arcade.html — the reverse cross-link to /games]]
  - [[fill: botsite/tests — the assertion(s) added]]
- test coverage: [[fill: what the new test asserts]]
- git: [[fill: branch base + commit shas]]
- verify: [[fill: four-suite count + both bootstrap checks]]

**Judgment:**

- Decisions made: [[fill: placement + markup choice]]
- Next session should know: [[fill:]]

## 💡 Session idea

[[fill: one genuine session idea, deduped vs recent cards]]

## ⟲ Previous-session review

[[fill: one-line remark on .sessions/2026-07-18-durable-ask-ids.md]]
