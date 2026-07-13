# 2026-07-13 — botsite: heatmap survival contrast — lethality shading + finisher counts in the drop-off strip

> **Status:** `complete` — PR #298, branch `claude/heatmap-survival-contrast-0713`;
> the owner-queue drop-off heatmap now folds finishers' guide chats into the
> same cells (`finished` per step + a "N finisher(s) asked" annotation) and
> shades by `died_share` — deaths over ALL touchers — so "hard but passable"
> renders pale and "wall" renders dark instead of both reading identically;
> lands via the auto-merge enabler on green.

- **📊 Model:** Claude Fable 5 · worker · backlog-promotion slice

**What this session was about:** backlog promotion ("Heatmap survival
contrast — fold finishers' guide chats into the strip", captured
2026-07-13 from the heatmap-tail session 💡). The drop-off heatmap
aggregated ONLY abandoned claims — `guided_step_dropoff()` scopes to
status='claimed' with no submission row — so a step where many finishers
chatted heavily but pushed through rendered identically to a wall.
Finished claims' guide exchanges are already persisted (PR #292 stores
them regardless of outcome); this session joined that survivor signal
into the same heatmap cells and re-scaled the shading by lethality.

## What was done

- `botsite/testing_store.py` — `guided_step_dropoff()` additionally
  queries finisher claims (EXISTS submission row) with guide exchanges
  and emits, per step, `finished` (finisher claims whose chat touched the
  step) and `died_share` (died_here / (touched + finished), 0.0 when
  nobody touched it — no division blow-ups), plus a per-task
  `finisher_count`. Finisher chats extend the dense step range when they
  reach past the last drop-off step; tasks still appear only when they
  have drop-offs — the strip stays a drop-off view, finishers are
  contrast. Existing keys untouched.
- `botsite/testing.py` `_owner_page` — the full-length tail's padded
  cells carry `finished: 0` / `died_share: 0.0` so the template renders
  one shape. No new route, read-only, no new env reads (no CSRF surface).
- `botsite/templates/testing_owner.html` — cell shading now scales by
  `died_share` (lethality) instead of raw died-here share of the task's
  drop-offs; cells where finishers asked gain "· N finisher(s) asked"
  (tooltip: "N finisher(s) also asked here"); the task row label gains
  "N finisher(s) chatted"; the hint paragraph explains the new scale.
- `botsite/tests/test_testing_owner_step_heatmap.py` — +5 tests
  (contrast counts + died_share ≈ 1/3 over mixed touchers;
  finisher-extended dense range with an all-zero gap cell; finishers
  alone create no task row; rendered annotation + pale-0.00/dark-0.70
  shading pair; heatmap absent when only finishers chatted) and the two
  exact step-dict pins updated for the new keys; the excludes-submitted
  pin now also proves the finisher's chat re-enters as contrast.
- `docs/current-state.md` — header suite figure trued 1255 → 1298 (that
  one line only; the "as of main" variant blew the 7000-word orientation
  budget by 2 words, so the sha stays as the truing pass wrote it).
- `docs/ideas/backlog.md` — this session's 💡 captured as a new bullet.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — **1298 passed, 1 warning** (+5 over main's 1293);
  `python3 bootstrap.py check --strict` — green except this card's own
  designed born-red HOLD (flipped by this commit) and the pre-existing
  never-exit-affecting `owner-action-fields` advisory on
  control/status.md (not owned here).
- Decisions made: finisher scope is "a submission row EXISTS" (the
  complement of the drop-off scope's NOT EXISTS — status flips can't
  strand a claim in neither bucket); `died_share` computed in the store
  where the zero-guard is testable, not in the template; finisher-only
  tasks stay off the strip (nothing to rank — captured as this session's
  💡 instead).
- Next session should know: claim file deleted here; the strip's
  semantics doc lives in the `guided_step_dropoff()` docstring; PR #298
  rides the auto-merge enabler.

## 💡 Session idea

**Finisher-question hotspots — tasks with zero drop-offs never surface
their hint-needing steps** — the survival contrast only renders on tasks
that HAVE drop-offs (`guided_step_dropoff()` keys the strip off abandoned
claims), so a task where every tester finished but half of them asked the
guide about step 3 shows nothing at all: the "needs a hint" signal the
contrast was built to separate from "needs a rewrite" is invisible
exactly where it's purest. A small finisher-only aggregate (same
`finished` counts, no lethality) listed under the heatmap — or folded in
as contrast-only rows — would surface question hotspots before the first
drop-off ever happens. Deduped against `docs/ideas/backlog.md`: the
drop-off, heatmap, step-text, tail, and survival-contrast bullets all key
off abandoned claims; the transcript bullet is per-claim evidence, not
per-step; nothing aggregates finisher chats on tasks without drop-offs.
Captured in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

The venture-vetting-catalog session (PR #248) did well — 22 hand-curated
entries each pinned to their upstream packet @ `2c039e3` with an honesty
test enforcing the exact 1/12/2/7 breakdown, and it kept the UI contained
as a linked subpage instead of growing /products; what it missed is that
its own freshness guard exists only as its 💡 backlog bullet (catalog
sha-drift pin), so the registry it shipped starts decaying silently the
moment venture-lab's vetting lane moves — workflow improvement: when a
session ships hand-pinned upstream data, the drift check belongs in the
same PR as a cheap CI-time nag, not in the backlog.
