# 2026-07-10 — Heartbeat enrichment: machine-readable fields + /fleet support (queue-state NEXT item 4)

> **Status:** `complete` — PR #66 (`claude/heartbeat-enrichment`),
> squash-merge on `quality` green.

- **📊 Model:** claude-fable-5 · worker · routine-fired build slice (continuous mode, slice 2)

**What this session was about:** slice 2 of the 20:00Z continuous-mode wake
(manager Q-0265). Work-ladder rung 2 again: inbox at HEAD has nothing past
008; queue-state NEXT item 4 / the `planned` backlog bullet — **heartbeat
enrichment** (retro G3): machine-readable outstanding-orders + the `routine:`
(armed-but-silently-dead wake clocks) and `landing:` (stranded-work catch)
sibling captures, parsed by `app/fleet.py` and surfaced on `/fleet` so the
manager computes "what's left" without diffing inbox vs status vs git.

## What was done

- **`app/fleet.py`** — `parse_orders` (`acked=`/`done=` id lists, `001-008`
  ranges expanded with padding kept, >500-wide range refused as a typo;
  **outstanding = acked minus done**; `claimed-by:` captured verbatim;
  free-text → `ok=False`, never invented ids), `classify_routine` (armed /
  cron / last-fired age; **silent** = armed with a fire older than
  `FLEET_STALE_HOURS`; armed with no parseable fire = honest
  `no_fire_recorded`), `classify_landing` (`clean` / `pushed` / `local` /
  `unknown` + `claude/*` branch extraction; pushed/local set `attention`).
  `routine`/`landing`/`deployed` added to `KNOWN_KEYS` — which also fixes a
  LIVE parse bug: the websites heartbeat's own `routine:` line was leaking
  into `blockers:` as a continuation on the deployed fleet page. Stranded
  landings + silent routines join the stale rank in `_sort_key`
  (attention-first); summary rolls up `stranded` / `silent_routines` /
  `outstanding_orders`.
- **`app/templates/fleet.html`** — per-lane rows: outstanding-ids /
  all-acked-done badge on orders; routine row with "armed but no fire in Xh" /
  "no fire recorded yet"; landing row with "LOCAL-ONLY — stranded work" /
  "pushed, unmerged — rescue candidate" / "all merged"; deployed passthrough
  row; three new summary-header badges.
- **`control/README.md`** — the three OPTIONAL lines added to the status
  format block + a D-0028 enrichment note (additive protocol change: a lane
  writing none of them renders exactly as before).
- **Docs:** [D-0028] appended to `docs/decisions.md`; `docs/site.md` § 3a
  extended; `docs/ideas/backlog.md` bullet `planned` → Built (sibling
  captures folded in) + new idea captured; queue-state NEXT item 4 struck
  DONE, resume point → item 5/backlog; `docs/current-state.md` Recently
  shipped updated for the whole wake.
- **`tests/test_fleet_enrichment.py`** (+14, suites 143 → 157): orders parses
  (ranges/commas/claimed/free-text/absurd-range), routine
  (fresh/silent/no-fire/prose/none), landing kinds + attention + branch,
  lane_status flow (enriched through; no blockers leak; plain lane unchanged),
  overview sort (stranded green lane above plain healthy) + roll-ups.
- Live-local render verified (TestClient, mocked github): `/fleet` HTML shows
  every new badge; `/fleet.json` carries `orders_info` / `routine_info` /
  `landing_info`; HTTP 200.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests -q` —
  **157 passed**; `python3 bootstrap.py check --strict` — green with this
  card complete.

⚑ Self-initiated: no — queue-state NEXT item 4 (work-ladder rung 2), the
`planned` heartbeat-enrichment bullet in `docs/ideas/backlog.md`.

## 💡 Session idea

**Own-heartbeat parse self-check in `quality`** — a small test that runs THIS
repo's `control/status.md` through the `/fleet` parsers (`parse_status` →
`parse_orders` / `classify_routine` / `classify_landing`) and asserts the
machine-readable lines actually parse. Worth having because a malformed
heartbeat currently renders wrong on the live fleet page with zero feedback —
the pre-D-0028 `routine:` line leaked into `blockers:` for hours and nothing
red-flagged it; a parse self-check catches that class at PR time. Deduped
against `docs/ideas/backlog.md` + queue-state NEXT: nothing covers validating
one's own heartbeat (enrichment defines the fields; this checks we write
them well). Captured in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

Slice 1 (same wake, PR #64) did the trap-hunting well — it verified how the
gate scans `.sessions/` BEFORE choosing where the template lives, which is
the whole reason the template works; what it missed: it wrote the predicted
PR number on the card before the PR existed (it guessed right, but a sibling
opening a PR in the gap would have made a merged card lie — flip the card
after the PR number is real, or amend before merge).
