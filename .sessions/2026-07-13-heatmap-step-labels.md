# 2026-07-13 — owner queue: step text labels on the drop-off heatmap

> **Status:** `complete` — PR #295, branch `claude/heatmap-step-labels-0713`;
> the drop-off heatmap cells on GET /testing/owner now carry the
> walkthrough step's own text in their tooltip ("step 1 — Homepage first
> impression: …" instead of "step 1: …"), joined read-only in
> `_owner_page` from the same step script the guide renders.

- **📊 Model:** Claude Fable 5 · worker · backlog-promotion

**What this session is about:** backlog promotion — the `captured` bullet
"Step text labels on the drop-off heatmap" in `docs/ideas/backlog.md`
(2026-07-13, from the #294 dropoff-heatmap session 💡). PR #294's heatmap
strip on GET /testing/owner names steps by number only — "step 3 · 2
touched · 1 died" — so the owner still has to open the tester page to
learn what step 3 asks. This session joins each heatmap cell's
`step_index` against the guided task's walkthrough step text (the same
`steps` list the guide renders) so the cell tooltip says WHAT the
deadliest step asks the tester to do.

## What was done

- `botsite/testing.py`: new pure helper `_heatmap_step_text(steps,
  step_index)` (title lookup, 80-char truncation with ellipsis, empty on
  out-of-range/missing title) + the join in `_owner_page` — each
  `dropoff_heatmap` step entry now carries `step_text` from
  `task_steps(task_by_id(task_id))`; unknown tasks fall back to empty.
- `botsite/templates/testing_owner.html`: the cell `title` tooltip
  becomes `step N — <text>: X chat(s) touched it, Y died here` when text
  exists, byte-identical to before when it doesn't; the visible cell
  stays compact (number + counts), no layout change.
- `botsite/tests/test_testing_owner_step_heatmap.py`: +3 tests — tooltip
  carries real step titles for the catalog task, bare-number fallback
  for an unknown task, and the helper's truncation/bounds behavior.
- `docs/ideas/backlog.md`: source bullet flipped `captured` → `built`
  (PR #295 noted); this session's 💡 captured as a new bullet.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — 1279 passed, 1 warning (+3 over main's 1276);
  `python3 bootstrap.py check --strict` — green except this card's own
  designed born-red HOLD (flipped by this commit) and the pre-existing
  never-exit-affecting `owner-action-fields` advisory on
  control/status.md (not owned here).

⚑ Self-initiated: no — backlog promotion of the `captured` bullet
"Step text labels on the drop-off heatmap" (`docs/ideas/backlog.md`,
2026-07-13, #294 session 💡).

## 💡 Session idea

**Heatmap tail — render the walkthrough's full length, not just the
observed steps** — `guided_step_dropoff()` densifies cells from 0 to the
highest step any drop-off's chat TOUCHED (`top = max(...)`), so steps no
tester ever reached are invisible: a claim dying at step 2 of a 6-step
script renders an identical strip to one dying at step 2 of 2. The step
script's real length is already in `_owner_page` since this session's
join (`task_steps(task_by_id(...))`), so padding the strip with zero
cells out to `len(steps)` is a few lines. Worth having because
distance-to-finish is the severity signal the strip currently hides —
"died 4 steps from the end" and "died at the last step" should not read
the same. Deduped against `docs/ideas/backlog.md`: the heatmap bullet
(built) aggregates observed steps only, the step-text bullet (built this
session) covers labels; nothing covers the unreached tail. Captured in
`docs/ideas/backlog.md`.

## ⟲ Previous-session review

The venture-vetting-catalog session (PR #248) did well — 22 packets
hand-curated with per-title provenance and the honesty pin
(`test_committed_registry_is_honest`) that locks the 1/12/2/7 status
breakdown; what it missed, by its own admission: the catalog is frozen
at venture-lab `2c039e3` with no drift signal, and that sha-drift 💡 is
still an unbuilt backlog bullet two sessions later.
