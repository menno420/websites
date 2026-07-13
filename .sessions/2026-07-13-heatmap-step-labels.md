# 2026-07-13 — owner queue: step text labels on the drop-off heatmap

> **Status:** `in-progress`

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

## Plan

- `botsite/testing.py` `_owner_page`: after `store.guided_step_dropoff()`,
  join each task's step entries against `task_steps(task_by_id(task_id))`
  and attach a `step_text` (the step's `title`, truncated sensibly);
  unknown task / out-of-range index falls back to empty → the template
  keeps the bare number.
- `botsite/templates/testing_owner.html`: carry the step text in the
  cell's `title` tooltip; visible cell stays compact (number + counts),
  matching the existing strip.
- `botsite/tests/test_testing_owner_step_heatmap.py`: extend with
  rendered-page tests — step text present for a known step, bare-number
  fallback when the task has no step text.
- No new routes, no state changes — the page stays read-only.
- Verify: full four-suite pytest + `bootstrap.py check --strict`; PR ready
  (non-draft), auto-merge armed by the repo's enabler workflow.

## What was done

[[fill: close-out]]

⚑ Self-initiated: no — backlog promotion of the `captured` bullet
"Step text labels on the drop-off heatmap" (`docs/ideas/backlog.md`,
2026-07-13, #294 session 💡).

## 💡 Session idea

[[fill: idea]]

## ⟲ Previous-session review

[[fill: previous-session review]]
