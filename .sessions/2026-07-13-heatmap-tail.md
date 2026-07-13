# 2026-07-13 — owner queue: heatmap tail — render the walkthrough's full length

> **Status:** `in-progress` — branch `claude/heatmap-tail-0713`; born-red
> card holding the merge gate until the drop-off heatmap on GET
> /testing/owner renders the walkthrough's FULL length (never-reached
> tail cells + "of N steps" label), tests are green, and this card is
> flipped complete.

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

_(filled at close-out)_

## 💡 Session idea

_(filled at close-out)_

## ⟲ Previous-session review

_(filled at close-out)_
