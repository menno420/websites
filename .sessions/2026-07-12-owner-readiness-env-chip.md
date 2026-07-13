# 2026-07-12 — owner board: environments completeness rollup chip

> **Status:** `complete` — PR #223, branch `claude/owner-readiness-env-chip`;
> lands via the auto-merge-enabler on green.

- **📊 Model:** Claude Fable 5 · worker · feature-slice

**What this session was about:** backlog promotion — the captured idea
"Environments-completeness rollup chip on the /owner board"
(`.sessions/2026-07-12-envhub-group-chips.md` 💡, the #219 session): the
group completeness summary exists as a cheap pure function
(`envhub.group_summary`, PR #219, itself pure reuse of PR #216's
`annotate_completeness`) over the cached `railway.live_overview` read, but
it only renders on the hub index — the /owner readiness board, the owner's
actual habit path, says nothing about unfinished environments. This session
promotes it: ONE compact rollup chip on the /owner board — repeating the
promotion ladder that already paid off twice (#213 /prompts drift chip →
#217 /fleet coverage rollup → this).

## What was done

- **Rollup reduction** `app/envhub.py` `board_rollup(refresh)`: runs the
  UNCHANGED `group_summary` (#219) across ALL registry groups and reduces
  the results to one dict for the board chip — complete / incomplete /
  unknown buckets with group ids NAMED, the #217 `coverage_rollup` shape.
  Every honesty rule holds by construction (one ladder, zero forked
  semantics): a broken or empty registry, an unset RAILWAY_TOKEN, or a
  failed live read → `state: unknown` WITH the exact reason, never a
  fabricated green or "incomplete: 0"; under an ok read an out-of-scope
  group (the project-scoped token reads superbot-websites only —
  docs/RAILWAY-SAFETY.md) counts as unknown, never complete OR incomplete;
  green means strictly complete (`set_count == total`, the #219 chip
  rule). Never raises. Fed by the SAME TTL-cached `railway.live_overview`
  read the environments-hub makes — zero new network surface, zero new
  routes, GET-rendering only.
- **Route** `app/owner.py`: `owner_board` (and `_render_with_banner`, so
  the post-action re-render keeps the chip) gathers
  `envhub.board_rollup()` alongside `readiness.board()` and passes it as
  `envcov` — the exact `/fleet` + `projects.coverage_rollup` idiom.
- **Template** `app/templates/owner.html`: one chip paragraph in the
  header card — `b ok` "environments: all complete (N groups)" (plus an
  honest `+M unknown — outside the token's scope, never assumed` chip),
  `b warn` "environments: N groups incomplete" with the incomplete groups
  NAMED in `<code>` + the environments-hub deep link, `b unknown`
  "environments: live status unknown" + the exact reason otherwise — the
  existing badge ladder, no new CSS.
- **Tests** `tests/test_owner_readiness_env_chip.py` (11, fully offline —
  GraphQL monkeypatched, GitHub canned, mirroring
  `tests/test_envhub_group_chips.py`): all-set → green chip text; partial
  → amber with the correct count AND the group named; live read failure
  and token-unset → unknown WITH the exact reason; broken/empty registry
  → honest unknown, page still 200; `board_rollup` unit precision
  (incomplete names, no-live-truth, never-raises, strictly-complete
  green); NAMES-NEVER-VALUES (sentinel live values asserted absent from
  the rendered board); the /owner gate re-pinned (401 without/wrong
  creds).
- **Backlog** `docs/ideas/backlog.md`: the source idea was recorded on the
  #219 card but never appended to the backlog (that session's one capture
  miss) — repaired here by adding the bullet directly as `built`
  (PR #223) with its original capture text; claim file deleted at close.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — 891 passed (+11 new), 0 failed, 1 warning;
  `python3 bootstrap.py check --strict` — green apart from this card's own
  designed born-red HOLD (flipped by this commit) and the pre-existing
  `owner-action-fields` advisory on control/status.md (never
  exit-affecting, not owned here).

**Decisions made:** the rollup names groups by their registry `id` (the
slug the hub's URLs and filters use) rather than the long display title —
chip-sized, unambiguous, and grep-able; and the green chip never claims
more than it knows: it counts strictly-complete READABLE groups and carries
the out-of-scope remainder as an explicit unknown chip instead of silently
narrowing "all complete" to one group.

⚑ Self-initiated: no — coordinator-assigned slice executing the #219
session's captured idea.

## 💡 Session idea

**Environments rollup in the authed /owner readiness JSON** — the board
chip's rollup (`envhub.board_rollup`) renders on the `/owner` HTML only;
`/owner/api/readiness.json` (the authed machine view of the same board)
does not carry it, so a script or agent wanting the "N groups incomplete"
signal must scrape HTML. Attaching the same rollup dict to that JSON — the
exact #217 precedent, where `/fleet.json` carries the coverage rollup with
its key set pinned in `tests/test_fleet_json_contract.py` — would let the
scheduled healthcheck or a fleet-manager session alert on unfinished
environments mechanically. Worth having because the board chip only helps
while the owner is looking; the JSON makes the same honesty ladder
consumable by the machinery that watches when he is not. Deduped against
`docs/ideas/backlog.md` + the queue-state NEXT list: nothing touches the
owner JSON contract or a machine-readable environments rollup. Captured in
`docs/ideas/backlog.md`.

## ⟲ Previous-session review

The tester-task URL guard session (#221) did well — importing the arcade
probe's `probe_url` instead of forking verdict semantics kept one probe
ladder, and extracting the catalog loader pinned the probe and the route to
the same source; one honest carry: its probe reads the committed `status`
only (noted on its own card), so a task filled live-only in SQLite keeps
being probed — harmless today, but a standing surprise for whoever reads
the healthcheck output.
