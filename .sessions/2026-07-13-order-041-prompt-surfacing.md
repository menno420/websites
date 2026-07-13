# 2026-07-13 — ORDER 041 remainder: prompt data on the dispatch screen + owner console

> **Status:** complete — PR #239, branch `claude/order-041-prompt-surfacing`;
> lands via the pre-armed auto-merge on green.

- **📊 Model:** Claude Fable · worker (order execution) · feature-build

**What this session is about:** the ORDER 041 remainder (fleet-manager
inbox; the core shipped as PR #236) — "surface the same prompt data
everywhere it helps (the /prompts library, each seat's page on the
projects/console surfaces, the owner console) as views of ONE source — no
duplicated prompt copies anywhere in the site." Two surfaces were still
HEAD-copy-only: the per-seat dispatch screen (`/projects/{package}`) and
the gated owner console (`/owner`). Rung: order — ORDER 041.

## What was done

- **`/projects/{package}` prompt-versions strip** (`project_detail.html` +
  a registration-only touch in `app/main.py`): current canonical version +
  the ladder labels (via the EXISTING `prompt_history.history()` — the one
  /prompts/history data path, zero new fetch semantics), the seat's
  deployed-vs-canonical state ("deployed v3.4 · canonical v3.6" + per-
  artifact state badges + stale count — the SAME row model the /prompts
  drift table renders), and the `/prompts/history/{seat}` deep link. Only
  for packages that map to a roster seat (`roster.seat_for` — alias-aware,
  `superbot-next` → `superbot-2.0`; stubs get no strip); an unavailable
  ladder SAYS "history not available — <reason>" in the strip, never
  hidden, never invented.
- **`/owner` fleet prompt-state card** (`owner.html` + `app/owner.py`
  gathers `prompts.console_rollup()`): one row per roster seat — deployed
  vs canonical (the Custom-Instructions version line), stale count across
  the seat's 3 artifacts, worst-state badge, per-artifact states, history
  deep link; headline chip = fleet-wide stale/drifted count, with the
  honest "N rows unreachable — no verdict assumed" chip when nothing was
  comparable (never a fabricated green), plus the snapshot capture time.
- **Plumbing, all reuse** (`app/prompts.py`): `_build_deployed` gained a
  `seats` parameter (default unchanged); `seat_drift(seat)` = the drift
  rows for ONE seat (same URLs as /prompts → shared TTL cache);
  `console_rollup()` = a pure reduction of `deployed_drift()` over the
  roster. `prompt_history.strip(package)` composes `history()` +
  `seat_drift()`. `roster.seat_for()` added. No second fetch path, no
  prompt copy stored, GET-rendering only — zero new state-changing routes.
- **Tests**: `tests/test_prompt_surfacing.py` (+10) — rendering + honest
  degradation for both surfaces, seat-alias mapping, strip-reuses-history
  invariant, unreachable-world console, auth + GET-only pins.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — **984 passed** (+10 new); `python3 bootstrap.py check
  --strict` — green except the designed born-red hold on this card (one
  pre-existing owner-action advisory).

## 💡 Session idea

**Surface the seat's prompt state on /fleet's lane rows** — the /fleet
monitoring page already carries per-lane freshness/coverage chips;
`prompts.console_rollup()` now yields a per-seat stale count that could
become one more chip ("prompts: 2 stale") via the same rollup-promotion
ladder as `coverage_rollup` (#217) — zero new fetch semantics, one chip.
Deduped: no prompt chip exists on /fleet today and `docs/ideas/backlog.md`
has no such entry.

## ⟲ Previous-session review

`.sessions/2026-07-13-prompts-version-history.md` (PR #236): its captured
idea IS this session's slice — the card's file map (`prompt_history.py` as
the reusable data path, `prompts.py` drift rows) was accurate and made the
build mostly composition. One friction: `_build_deployed` iterated the
whole roster unconditionally, so the single-seat strip needed the `seats`
parameter added — the card's "zero new fetch semantics" claim held, but
"one reusable data path" mildly overstated how directly reusable the drift
half was. Its test fixtures (real committed shapes) were copied here and
worked unchanged. Nothing misleading found.
