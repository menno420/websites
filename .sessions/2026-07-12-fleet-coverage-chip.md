# 2026-07-12 — /fleet coverage-chip rollup (packages incomplete: N)

> **Status:** `complete` — PR #217, branch `claude/fleet-coverage-chip`;
> lands via the auto-merge-enabler on green.

- **📊 Model:** Claude Fable · websites worker · backlog promotion

**What this session was about:** Promote the backlog bullet "Coverage-chip
rollup on the /fleet board": one "packages incomplete: N" rollup cell on
the `/fleet` monitoring surface, reduced from the SAME per-seat
instructions/coordinator/failsafe coverage `/projects` already computes
(`projects.role_coverage` over the TTL-cached registry listing — zero new
network surface, GET-rendering only, no new state-changing routes). Honest
states: green complete / amber "packages incomplete: N" with the seats
named / unknown when the registry (or a seat's listing) cannot be read —
never a fabricated zero.

## What was done

- **Rollup layer** `app/projects.py`: `coverage_rollup()` reduces
  `projects.overview()` (the exact data /projects renders — same TTL-cached
  `github` layer and URLs) to `{state, reason, seats, complete, incomplete,
  incomplete_names, unlistable, unlistable_names}`. Honesty ladder pinned
  in the docstring + tests: degraded registry (empty / not-configured /
  unavailable) or zero active seats → `unknown` with the reason; a seat
  whose own listing failed is `unlistable` (never complete OR incomplete),
  so green is only claimable when every active seat was actually listed;
  retired stubs excluded — same population as the /projects "N of M
  dispatch-ready" summary.
- **Routes** `app/main.py`: `/fleet` and `/fleet.json` gather the rollup
  alongside `fleet.overview()`; the JSON payload gains a top-level
  `coverage` object for machine consumers (the manager's registry-lint
  signal where it already reads).
- **Template** `app/templates/fleet.html`: one "seat packages:" chip line
  in the header card (drift-chip/envhub idiom): `b ok` "coverage: complete
  (N seats)" / `b warn` "packages incomplete: N" with the incomplete seats
  named inline as `<code>` + a /projects link / `b unknown` "coverage
  unknown" carrying the reason (also the partial-unknown case: listed
  seats all complete but one unlistable → unknown chip, never green).
- **Tests** `tests/test_fleet_coverage_chip.py` (11, fully offline):
  rollup full / partial-with-names / registry-404 / registry-unavailable /
  unlistable-seat / stubs-only states; rendered chip states on /fleet
  (amber names the seat, green, unknown, partial-unknown); /fleet.json
  carries the rollup. `tests/test_fleet_json_contract.py`: `TOP_KEYS` +
  `COVERAGE_KEYS` pinned in the SAME PR that extends the payload.
- **Backlog** `docs/ideas/backlog.md`: the source bullet flipped
  `captured → built` (PR #217); claim file deleted at close.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — 817 passed (806 before, +11 here), 0 failed;
  `python3 bootstrap.py check --strict` — green apart from this card's own
  designed born-red HOLD (flipped by this commit) and the pre-existing
  `owner-action-fields` advisory on control/status.md (never
  exit-affecting, not owned here).

**Decisions made:** rollup computed from `projects.overview()` rather than
a leaner listing-only walk — stub exclusion needs meta.md anyway, and
reusing the one code path keeps the honesty ladder single-sourced; rollup
added to `/fleet.json` (not HTML-only) so the manager's machine reads get
the same registry-lint signal, contract re-pinned same PR.

**Next session should know:** the chip lives in the /fleet header card;
per-lane placement (joining seat package ↔ lane repo) is captured as this
card's 💡 idea, not built.

⚑ Self-initiated: no — coordinator-assigned promotion of the captured
backlog bullet (source:
`.sessions/2026-07-12-projects-role-coverage-chips.md` 💡).

## 💡 Session idea

**Per-lane package-coverage badge on the /fleet lane cards** — the rollup
lands in the header, but lane repo names and seat package names are the
same identifier space: joining `coverage_rollup`'s `incomplete_names` to
each lane card would put a "seat package incomplete" badge ON the lane
whose seat can't relaunch, so the manager sees WHO is blocked from its
heartbeat card, not just that someone is. Zero extra fetches — the join is
over data /fleet now already has. Worth having because the header count
still costs a hop to /projects to find the culprit. Deduped against
`docs/ideas/backlog.md` + the queue-state NEXT list: nothing joins lane
cards to package coverage (this PR built the header rollup only).

## ⟲ Previous-session review

The env-hub completeness diff (#216) did well — the names-never-values
rail pinned as a test (sentinel live values asserted absent from the page)
is the right way to make a privacy contract survive refactors; one
workflow improvement: its card records the suite total ("806 passed") but
not the delta its PR added, so the next session's baseline check needs a
re-run instead of a subtraction — cards should say "N passed (+M new)"
(this one does).
