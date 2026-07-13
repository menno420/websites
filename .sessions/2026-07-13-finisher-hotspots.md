# 2026-07-13 — botsite: finisher-question hotspots — hint-heavy steps on tasks with zero drop-offs

> **Status:** `in-progress` — branch `claude/finisher-hotspots-0713`; building
> the finisher-only step aggregate (`guided_finisher_hotspots()`) and its
> owner-queue strip so a task where every tester finished still surfaces
> which steps needed hints.

- **📊 Model:** Claude Fable 5 · worker · dispatched backlog-promotion slice

**What this session was about:** backlog promotion ("Finisher-question
hotspots — tasks with zero drop-offs never surface their hint-needing
steps", captured 2026-07-13 from the heatmap-survival-contrast session 💡).
The survival contrast (PR #298) only renders on tasks that HAVE drop-offs —
`guided_step_dropoff()` keys the strip off abandoned claims; finishers are
contrast, not subject — so a task where every tester finished but half of
them asked the guide about step 3 shows nothing at all. This session builds
the finisher-only aggregate over the already-persisted `finished` counts
(PR #292 stores every chat regardless of outcome) and lists it under the
drop-off heatmap.

## What was done

- [[fill: store accessor]]
- [[fill: route + template]]
- [[fill: tests]]
- [[fill: verify counts]]

## 💡 Session idea

[[fill: new idea, deduped against docs/ideas/backlog.md]]

## ⟲ Previous-session review

[[fill: honest remark on the venture-vetting-catalog card]]
