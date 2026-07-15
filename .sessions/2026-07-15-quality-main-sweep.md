# 2026-07-15 — quality-main-sweep: backfill missing quality runs on main

> **Status:** `in-progress`

- **📊 Model:** [[fill: model line at the flip]]

**What this session is about:** the reboot-truing baton
(`.sessions/2026-07-15-reboot-truing.md`, next-session item 1) flagged that
main HEAD commits landed by github-actions[bot] merges get **no push-event
`quality` run** — the GITHUB_TOKEN recursion guard suppresses the push
event, so the 4 commits after `214ed0f` (ee47f8d, 6fafc1a, 68ad331,
3cac461) carry no quality check and main health is unmeasured between
merges. This slice adds a host-owned scheduled sweep workflow
`.github/workflows/quality-main-sweep.yml` that detects a main HEAD with no
completed `quality` check run and dispatches `quality.yml` on main —
mirroring the repo's documented recursion-guard exception (review-bake's
GITHUB_TOKEN `workflow_dispatch` chain, already documented in
`quality.yml`'s `on:` block).

⚑ Self-initiated: yes — contained, reversible, from the previous session's
baton (decide-and-flag).

## Close-out

[[fill: evidence + judgment at the flip]]

## 💡 Session idea

[[fill: one genuine idea at the flip, deduped against docs/]]

## ⟲ Previous-session review

[[fill: review of .sessions/2026-07-15-reboot-truing.md at the flip]]
