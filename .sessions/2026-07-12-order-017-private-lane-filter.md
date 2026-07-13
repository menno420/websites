# 2026-07-12 — ORDER 017 D compliance: the Pokémon lane stays private on the review site

> **Status:** `complete` — branch `claude/order-017-private-lane-filter`,
> parks as a READY PR to main (build worker; merge is deliberately not this
> session's call — auto-merge arms itself).

- **📊 Model:** Claude Fable 5 · build worker · order

**What this session was about:** Rung: order — ORDER 017 workstream D
requires "the Pokémon lane stays private", but the public review site's
`/fleet` page rendered a lane card for the private repo (name + github link
+ "live" chip + no-heartbeat lines). Scope: remove the private lane from
every public surface of the review/ service — bake-time exclusion,
defensive render-time filter, regenerated mirrors, evidence-corpus scrub,
and rendered-HTML regression tests.

## What was done

- **Bake-time exclusion** — `review/gen_fleet.py`: `PRIVATE_LANES =
  {"pokemon-mod-lab"}` filters registry entries in `main()` and seat
  members in `bake_seats()`; `parse_heartbeat()` scrubs any
  `pok[eé]mon…` token out of mirrored free text (other lanes' heartbeat
  prose named the private lane), replacement `[a private lane]`.
- **Defensive render-time filter** — `review/fleetdata.py`:
  `strip_private_fleet()` / `strip_private_stats()` applied at the load
  choke points (`load_fleet` / `load_stats`) every page and `/fleet.json`
  read through — an OLDER unfiltered mirror still never renders the lane;
  registry `total_seats`/`repo_seats` decremented alongside the dropped
  lanes so displayed counts stay consistent; recursive text scrub;
  `/fleet/pokemon-mod-lab` 404s.
- **Regenerated mirrors** — `review/data/fleet.json` re-baked via
  `gen_fleet.py` (2026-07-12T15:47Z: 18 seats, 17 repo-backed, 17
  heartbeats — counts come from the regenerated data, never edits).
  `review/data/stats.json`: the REST bake is walled in this env
  (fail-soft, "every repo stat fetch failed"), so the identical
  `strip_private_stats` filter was hand-applied to the committed file
  (17 repos; said plainly here and in the PR).
- **Public-mention scrub** — evidence corpus `review/data/evidence/`
  (README.md privacy bullet reworded; 01-provenance.md table row;
  03-roster-consolidation.md seat table + heartbeat line;
  05-screenshots.md fig-15a + fig-20 descriptions), `templates/fleet.html`
  reading-key footnote, and `ai.py` prompt rule 6 (the privacy rule stays,
  the repo name goes — a grounded answer can no longer emit it). Two of
  these were the accented "Pokémon" form that plain `grep -i pokemon`
  misses — the new tests caught them.
- **Tests** — `review/tests/test_fleet.py`: rendered `/`, `/fleet`,
  `/fleet.json` and both committed mirrors carry no pokemon/pokémon
  (accent-aware), `/fleet/pokemon-mod-lab` is 404, plus defensive-filter
  unit tests over deliberately unfiltered old fleet/stats mirrors (lane
  dropped, counts decremented, seat member removed, free text scrubbed).
  `test_ai.py`: the system prompt (rules + embedded corpus) never names
  the lane. Fixture in the seats-view unit test renamed to a neutral
  `unreadable-repo` (the honest-gap mechanism it pins is generic).
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — 555 passed; `python3 bootstrap.py check --strict` —
  green (sole hold during the session was this card's designed born-red
  state; final run on the flipped card: PASS).

⚑ Self-initiated: no — ORDER 017 workstream D compliance fix, routed by
the coordinator.

## 💡 Session idea

**Site-wide privacy lint for the review service** — one test (or bake-time
lint) that walks EVERY GET route in `review/app.py` plus every committed
`review/data/**` file and asserts no private-lane token, accent-aware.
Worth having because privacy compliance shouldn't depend on remembering
which surface to grep — today's two escapees were accented "Pokémon" forms
that plain `grep -i` missed on pages nobody had pinned. Deduped against
`docs/ideas/backlog.md` + the queue-state NEXT list: healthcheck/bake ideas
exist, nothing covers a privacy sweep. Captured in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

The ORDER 017 workstream-A refresh session (PR #175) did well: regenerated
mirrors were never hand-edited, and provenance for the first stats.json was
pinned to the exact Actions run. What it missed: it recorded
"pokemon-mod-lab stays an honest 404 gap" as a virtue while workstream D of
the very same order said the lane stays private — honesty about a lane the
public page should not have shown at all. This session closed that gap;
the lesson is that compliance lines in an order need their own checklist
pass, separate from data-freshness goals.
