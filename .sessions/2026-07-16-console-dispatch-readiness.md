# 2026-07-16 — Console dispatch-readiness chips on the launch screen

> **Status:** `complete` — branch `claude/console-dispatch-readiness`; the
> seat dispatch-readiness chip row (`pkg.coverage` / `pkg.dispatch_ready`,
> already computed for the `/projects` index) now also renders on the
> `/projects/{package}` launch console. Read-only, zero extra fetches; +2 tests.

- **📊 Model:** Claude Opus · high · feature build (console dispatch-readiness chips)

**What this session is about:** the `/projects/{package}` dispatch screen is the
owner's single-screen launch console — full role-file text, copy-ready, plus a
3-step dispatch checklist (copy Custom Instructions, copy coordinator prompt,
verify the failsafe). But the screen never surfaced whether the seat is actually
*launchable*: the `/projects` index already shows a coverage chip row
(`instructions ✓ / coordinator ✗ / failsafe ✓`) + a dispatch-ready / NOT-ready
label from `pkg.coverage` / `pkg.dispatch_ready`, yet the detail page — the
place you dispatch FROM — showed none of it. A missing coordinator prompt just
silently didn't render a block below the checklist. This slice renders the SAME
already-computed coverage data at the top of the dispatch screen, so
"this seat can't launch — the coordinator prompt is missing upstream" is a glance
before dispatch, not a mid-dispatch surprise.

⚑ Self-initiated: no — coordinator-dispatched overnight build slice on the
control-plane public console.

## Close-out

**Evidence:**

- files touched this branch: `app/templates/project_detail.html` (chip row +
  ready/NOT-ready label in the header card, guarded by `pkg.coverage`, above
  the meta table — reuses the index's `.b ok`/`.b bad` chip idiom, no new CSS);
  `tests/test_projects.py` (+2 render tests — a ready seat shows all-✓ +
  "dispatch-ready" and no ✗; an incomplete seat missing its coordinator shows
  `coordinator ✗` + "NOT dispatch-ready"); this card +
  `control/claims/console-dispatch-readiness.md` (first commit; claim deleted
  at this flip).
- git: branch `claude/console-dispatch-readiness` from `origin/main` @
  `e0a3cc0` (#374); commits `0e96eef` (born-red card + claim), `9d3c8ce`
  (template + tests), + this flip.
- verify: `python3 -m pytest tests/ botsite/tests dashboard/tests review/tests
  -q` — **1633 passed, 1 warning**; `python3 bootstrap.py check --strict
  --session-log <this card>` — the only red during the session was the DESIGNED
  born-red hold on this card, released at this flip.

**Judgment:**

- Decisions made: (1) no new data path — the chip row renders `pkg.coverage` /
  `pkg.dispatch_ready` that `projects._build_package` already computes for BOTH
  the index and the detail page, so there is zero extra network surface and one
  source of truth; (2) the row is guarded by `pkg.coverage` (empty on an
  unlistable package), so a package whose listing failed shows NO fabricated ✗,
  matching the index's honest-unknown discipline; (3) placed above the meta
  table in the header card so readiness is the first thing seen on the launch
  console; (4) read-only throughout — no new route, no state change, no CSRF
  surface, the gated `/owner/*` console untouched.
- Next session should know: the coverage model is now surfaced on both the
  index and the detail page; the remaining reuse is fleet-wide (see the idea).

## 💡 Session idea

**A fleet-wide "seats not launchable: N" chip on `/fleet` that deep-links each
blocked seat's dispatch screen.** `projects.coverage_rollup` already reduces the
same `pkg.coverage` data to an incomplete-count for `/fleet`; the next step is to
make that count a linked list — each incomplete seat name a link to
`/projects/{name}#dispatch` — so the owner jumps straight from "which seat can't
launch" to the exact missing role file. Captured for the backlog at flip.

## ⟲ Previous-session review

`.sessions/2026-07-16-review-ledger-tally.md` (PR #372's sibling review pass)
landed the at-a-glance documented-count tally on the review service's Problems /
Successes hero cards — promoting a count that lived only in the data up to the
top of the page. This slice extends that exact at-a-glance idiom to the
control-plane dispatch screen: a readiness signal already computed for the index,
surfaced where the owner acts on it. One miss worth noting from that card: it
tallied the review heroes but did not thread the same hero-count pattern into
`docs/SKILLS.md`, so each service's author re-derives the idiom per-page rather
than from one routed "at-a-glance count" recipe.
