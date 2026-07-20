# 2026-07-20 — refresh current-state.md to #456 truth + trim orientation headroom

> **Status:** `in-progress` — branch `claude/records-refresh`, PR #<pending>.
> Refreshing `docs/current-state.md` to present truth (header lagged at #421;
> HEAD is #456), folding the 2026-07-19→20 build cycle into the ledger, trimming
> superseded history into terse past-tense lines to open orientation headroom,
> and fixing the three off-taxonomy PL-004 model lines. Born red; the flip to
> `complete` is the deliberate LAST step so merge-on-green lands the PR.

- **📊 Model:** opus-4.8 · low · docs-only

**What this session is about:** Records/orientation hygiene (the 2026-07-19
cycle plan → Hygiene; NEXT-2-TASKS baton in `control/status.md`).
`docs/current-state.md`'s header still cited `main 07b4bb9 (#421)` while HEAD is
`79d57e0 (#456)`, and the boot-read set sat at 6909/7000 words (91 of headroom,
≥95% of budget — the kit's near-cliff advisory). This session trues the ledger
to the present and folds superseded changelog detail (which `git log` records
better) into terse past-tense lines to open real headroom, without dropping any
current-truth content. It also fixes the three 2026-07-19 cards whose `📊 Model`
lines are off the PL-004 taxonomy.

Work-ladder rung: order — the `control/status.md` NEXT-2-TASKS baton (records
refresh + headroom trim), continuing the 2026-07-19 cycle's Hygiene slice.

⚑ Self-initiated: no — coordinator-assigned records-refresh baton.

## What was done

- `docs/current-state.md` — header trued to `main 79d57e0 (#456)`, open PRs
  none, four-suite 2132, kit v1.17.0; the wind-down blockquote tightened (EAP
  session surface ~2026-07-21, extended per ORDER 031; repo + services stay
  live). "What this repo is" + "Stability baseline" refreshed for the fleet
  Discord login, the Postgres-backed `/submit`+`/testing`, and the hands-off
  `BAKE_PAT` bake. "In flight" rewritten to the 2026-07-20 snapshot (orders
  001–038 all done per `control/status.md`; live owner asks). "Recently shipped"
  gained a 2026-07-19→20 build-cycle entry (Discord login #426/#442/#443,
  Postgres stores #425/#446/#447/#449, bake #434/#438, arcade #428/#435, NAV
  guards #416/#418/#450, askverify #451, signal registry #453, AST guard #454,
  /directory probe #455) and folded the older waves into terse past-tense lines.
- `.sessions/2026-07-19-botsite-discord-oauth.md`,
  `.sessions/2026-07-19-dashboard-discord-oauth.md`,
  `.sessions/2026-07-19-submissions-store-shim.md` — `📊 Model` lines corrected
  to the PL-004 `model · low|medium|high · <class>` form (the botsite/dashboard
  cards' `effort medium–high` / `task-class: …` prose replaced with
  `high · feature build`; the submissions card's exact ID `claude-opus-4-8`
  replaced with the family name `opus-4.8`).
- `control/claims/records-refresh.md` — work claim for this branch (deleted in
  the flip commit so it merges away with the PR).
- Verified before flip: [[fill: four-suite pass count + strict result, at flip]].

**Verify plan:** four-suite
(`env -u DATABASE_URL python3 -m pytest tests/ botsite/tests dashboard/tests review/tests -q`)
+ `python3 bootstrap.py check --strict`; confirm the `[orientation-headroom]`
advisory reports meaningful headroom (boot-read well under the 7000 budget) and
the three PL-004 model-line advisories no longer fire.

## 💡 Session idea

The boot-read budget is a single lump sum across `docs/current-state.md` +
`docs/AGENT_ORIENTATION.md`, but only current-state grows unbounded (it is the
append-only changelog). A tiny `check`-time advisory that warns when the newest
"Recently shipped" entry pushes the file past a per-file soft cap — nudging a
trim-as-you-append habit — would keep the ledger from creeping back to the cliff
between hygiene passes. Deduped against `docs/ideas/backlog.md` + NEXT: not
present. To capture in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

`.sessions/2026-07-20-directory-probe-follow-redirects.md` (#455, cycle slice 6)
taught the botsite `/directory` .gba download probe to follow a 302 → CDN so a
redirected asset stops reading as a false negative — a tight, test-covered
signal-accuracy fix that landed clean, leaving nothing in flight. This
records-refresh baton is the cycle's Hygiene follow-through: it trues the ledger
those six slices moved past and pays down the orientation-headroom debt they
accreted.
