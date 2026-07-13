# 2026-07-13 — owner queue: heatmap tail — render the walkthrough's full length

> **Status:** `complete` — PR #296, branch `claude/heatmap-tail-0713`;
> the drop-off heatmap on GET /testing/owner now renders the
> walkthrough's FULL length: never-reached steps show as hollow cells
> with a "never reached" tooltip and each task's strip carries an
> "of N steps" label, so distance-to-finish is visible at a glance.

- **📊 Model:** Claude Fable · worker · backlog-promotion

**What this session is about:** backlog promotion — the `captured` bullet
"Heatmap tail — render the walkthrough's full length, not just the
observed steps" in `docs/ideas/backlog.md` (2026-07-13, from the #295
heatmap-step-labels session 💡). `guided_step_dropoff()` densifies cells
from 0 to the highest step any drop-off's chat touched, so steps no
tester ever reached are invisible: dying at step 2 of a 6-step script
renders the same strip as dying at step 2 of 2. The step script's real
length is already joined in `_owner_page` (`task_steps(task_by_id(...))`
since #295), so this session pads each task's strip with zero-count,
`reached: False` cells out to `len(step_script)` — rendered hollow with
a "never reached" tooltip plus an "of N steps" label — while
`guided_step_dropoff()` in the store stays observed-data-only. Unknown
tasks / empty scripts keep today's observed-only strip.

## What was done

- `botsite/testing.py` `_owner_page`: after the #295 step-text join,
  observed cells gain `reached: True` and the cell list is padded with
  zero-count `reached: False` entries out to `len(step_script)` (each
  padded cell still carries its step text for the tooltip); every task
  gains `script_len` (0 for unknown tasks / empty scripts) to drive the
  label. `guided_step_dropoff()` in `botsite/testing_store.py` untouched.
- `botsite/templates/testing_owner.html`: never-reached cells render
  visually distinct (dashed border, transparent background, muted) with
  a "step N — <text>: never reached by any drop-off's chat" tooltip;
  the per-task header line gains "· of N steps" when the script length
  is known. Observed cells render byte-identical to before.
- `botsite/tests/test_testing_owner_step_heatmap.py`: +3 tests — a
  6-step script with drop-offs only at steps 0–2 renders 6 cells
  (3 never-reached tail cells + the "of 6 steps" label + step-text in
  the tail tooltip); a drop-off dying at the last step pads nothing;
  an unknown task keeps the observed-only strip (no padding, no label).
- `docs/ideas/backlog.md`: source bullet flipped `captured` → `built`
  (PR #296 noted); this session's 💡 captured as a new bullet.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — 1282 passed, 1 warning (+3 over main's 1279);
  `python3 bootstrap.py check --strict` — green except the pre-existing
  never-exit-affecting `owner-action-fields` advisory on
  control/status.md (not owned here); this card's designed born-red
  HOLD is flipped by this commit.

⚑ Self-initiated: no — backlog promotion of the `captured` bullet
"Heatmap tail — render the walkthrough's full length, not just the
observed steps" (`docs/ideas/backlog.md`, 2026-07-13, #295 session 💡).

## 💡 Session idea

**Heatmap survival contrast — fold finishers' guide chats into the
strip** — the drop-off heatmap aggregates ONLY abandoned claims
(`guided_step_dropoff()` scopes to status='claimed' with no submission
row), so a step where ten finishers also chatted heavily but pushed
through renders identically to one where every toucher died: the strip
cannot distinguish "hard but passable" from "wall". Finished claims'
guide exchanges are already persisted (PR #292 stores them regardless
of outcome; the heatmap scope merely excludes them), so a per-step
survivor count ("N finishers also asked here") joined into the same
cells — or shading scaled by died-share among ALL touchers, not just
drop-offs — would rank rewrite urgency by lethality rather than raw
death count. Worth having because a step everyone asks about but
everyone passes needs a hint, while a step half its touchers die on
needs a rewrite — today both read the same. Deduped against
`docs/ideas/backlog.md`: the drop-off, heatmap, step-text, and tail
bullets (all built) aggregate abandoned claims only; nothing folds
finished claims' guide activity into the step strip. Captured in
`docs/ideas/backlog.md`.

## ⟲ Previous-session review

The venture-vetting-catalog session (PR #248) shipped a genuinely honest
22-packet registry — statuses hand-derived from each packet's own
Status/Verdict text and locked by `test_committed_registry_is_honest`
rather than invented — but it froze itself at venture-lab `2c039e3` and
its own sha-drift 💡 is still an unbuilt `captured` bullet, so the
honesty it shipped decays silently with every upstream vetting change.
