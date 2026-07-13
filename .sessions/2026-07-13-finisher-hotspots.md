# 2026-07-13 — botsite: finisher-question hotspots — hint-heavy steps on tasks with zero drop-offs

> **Status:** `complete` — PR #303, branch `claude/finisher-hotspots-0713`;
> the owner queue now lists a finisher-only step strip under the drop-off
> heatmap (`guided_finisher_hotspots()`: per-step `finished` counts on
> tasks with ZERO drop-offs), so a task where every tester finished but
> half of them asked the guide about one step finally surfaces its
> hint-needing steps before the first drop-off ever happens; lands via
> the auto-merge enabler on green.

- **📊 Model:** Claude Fable 5 · worker · dispatched backlog-promotion slice

**What this session was about:** backlog promotion ("Finisher-question
hotspots — tasks with zero drop-offs never surface their hint-needing
steps", captured 2026-07-13 from the heatmap-survival-contrast session 💡).
The survival contrast (PR #298) only renders on tasks that HAVE drop-offs —
`guided_step_dropoff()` keys the strip off abandoned claims; finishers are
contrast, not subject — so a task where every tester finished but half of
them asked the guide about step 3 shows nothing at all. This session built
the finisher-only aggregate over the already-persisted `finished` counts
(PR #292 stores every chat regardless of outcome) and listed it under the
drop-off heatmap.

## What was done

- `botsite/testing_store.py` — new `guided_finisher_hotspots()`: per-task,
  per-step `finished` counts over FINISHER claims (a submission row
  EXISTS — the exact contrast scope from #298) with guide-chat activity,
  restricted to tasks with NO drop-off claims (tasks with any drop-off
  already show their finishers as heatmap contrast — no double-listing).
  Dense step range 0..max, tasks ordered by task_id, per-task
  `finisher_count`. No lethality anywhere — nobody died.
- `botsite/testing.py` `_owner_page` — same step-text tooltip join +
  full-length script padding as the drop-off heatmap (padded cells carry
  `finished: 0`); `finisher_hotspots` joins the template context.
  Read-only, no new route, no new env reads (no CSRF surface).
- `botsite/templates/testing_owner.html` — the hotspot strip renders
  directly under the heatmap block ("listed under the heatmap", per the
  backlog spec): info-tinted cells ("step 2 · 2 asked") where finishers
  asked, dashed zero cells, row label "N finisher(s) chatted · no
  drop-offs · of N steps".
- `botsite/tests/test_testing_owner_step_heatmap.py` — +6 tests
  (finisher-only task surfaces with dense per-step counts and
  claims-not-exchanges counting; drop-off tasks excluded + task_id
  ordering; empty/chatless/drop-off-only cases stay `[]`; rendered strip
  with padding + step-text tooltips on an otherwise-empty Drop-offs
  section; hotspots absent when the task has drop-offs; unknown-task
  observed-only strip).
- `docs/current-state.md` — header suite figure trued 1298 → 1325 (the
  #299–#301 landings had not trued it; one-word change, #298 precedent).
- `docs/ideas/backlog.md` — source bullet flipped `captured` → `built`
  (PR #303); this session's 💡 captured as a new bullet.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — **1325 passed, 1 warning** (+6 over main's 1319);
  `python3 bootstrap.py check --strict` — green except this card's own
  designed born-red HOLD (flipped by this commit) and the pre-existing
  never-exit-affecting `owner-action-fields` advisory on
  control/status.md (not owned here).
- Decisions made: of the backlog's two proposed shapes ("a small
  finisher-only aggregate listed under the heatmap — or folded in as
  contrast-only task rows") the separate aggregate won — folding
  drop-off-free rows into `guided_step_dropoff()` would have broken its
  tested "tasks appear only with drop-offs" pin (#298) and muddled two
  different signals (lethality vs hint density) in one strip; the
  hotspot strip uses the info tint, not the heatmap's red, so nothing
  suggests death where nobody died.
- Next session should know: claim file deleted here; the aggregate's
  semantics doc lives in the `guided_finisher_hotspots()` docstring;
  PR #303 rides the auto-merge enabler.

## 💡 Session idea

**Per-step question digest — surface WHAT testers asked at a hotspot, not
just how many** — the heatmap and the finisher hotspots (PRs
#294/#298/#303) rank WHERE guide chats cluster, but the owner still opens
each drop-off's per-claim transcript one by one to learn what confused
people, and finishers' transcripts on hotspot tasks render nowhere at all
(PR #292 attaches them to submissions, not to the strip). Grouping the
persisted `guide_exchanges` messages by (task, step) across ALL claims and
rendering the tester questions behind each cell (message text only,
untrusted-input framing, capped + collapsed) would turn "step 3 · 4 asked"
into the actual rewrite input: the four questions themselves. Worth having
because the hotspot says a hint is needed but not which hint — and the raw
questions that answer that are already persisted. Deduped against
`docs/ideas/backlog.md`: the transcript bullet (built, #292) is per-claim
evidence on submissions; the heatmap, survival-contrast, and
finisher-hotspots bullets (all built) count claims per step but never
render message text; nothing groups guide messages by step across claims.
Captured in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

The venture-vetting-catalog session (PR #248) did well — 22 hand-curated
entries each pinned to their upstream packet @ `2c039e3` with an honesty
test enforcing the exact 1/12/2/7 status breakdown, and it kept the UI
contained as a linked subpage instead of growing /products; what it
missed is that its own freshness guard shipped only as its 💡 bullet
(catalog sha-drift pin, still `captured` today), so the registry has now
been decaying-capable for the whole day's worth of venture-lab movement —
when a session ships hand-pinned upstream data, the cheap CI-time drift
nag belongs in the same PR, not the backlog.
