# console-dispatch-readiness

> **Status:** `in-progress`

## Slice
Surface the seat's **dispatch-readiness** on the `/projects/{package}` dispatch
screen (`app/templates/project_detail.html`). The launch console's checklist
already tells the owner to copy the Custom Instructions + coordinator prompt and
verify the failsafe — but it never flags when one of those role files is
*missing upstream*: the block just silently doesn't render below. The `/projects`
index already shows a coverage chip row + a dispatch-ready / NOT-ready label
(`pkg.coverage` / `pkg.dispatch_ready`, computed once in
`projects._build_package`), so the detail page can render the SAME data with
zero extra fetches — turning "this seat can't launch, coordinator prompt is
missing" from a mid-dispatch surprise into a glance at the top of the screen.

Read-only, contained to `project_detail.html` + a test in `tests/test_projects.py`.

## Files
- `app/templates/project_detail.html` — chip row + ready/not-ready label in the header card.
- `tests/test_projects.py` — render assertions (ready seat, incomplete seat).

💡 Idea: the same coverage model could drive a fleet-wide "seats not launchable" chip on `/fleet` beyond the existing incomplete-count rollup, deep-linking each blocked seat's dispatch screen.

📊 Model: Claude Opus · high · console-feature build

Prev-session review remark: `.sessions/2026-07-16-review-ledger-tally.md` landed the at-a-glance documented-count tally on review's Problems/Successes heroes — this slice extends that same at-a-glance idiom to the control-plane dispatch screen.
