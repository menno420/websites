# 2026-07-13 — structural clarity-bar gate: every HTML route proves its headline + lede

> **Status:** `in-progress`

- **📊 Model:** Claude Fable 5 · worker · structural test gate

**What this session was about:** ORDER 022 item 1 follow-through, dispatched
by the coordinator — make tonight's clarity bar STRUCTURAL instead of
page-by-page. Both clarity sessions captured the same idea independently
(`.sessions/2026-07-13-clarity-control-plane.md` 💡 and
`.sessions/2026-07-13-clarity-botsite-dashboard.md` 💡; backlog bullet
"Structural clarity-bar gate" in `docs/ideas/backlog.md`): the ledes pinned
in `tests/test_clarity_ledes.py` and the PR #231 pins protect existing pages
only — a brand-new route can still ship below the bar. This session builds
one route-walking suite per service (tests/, botsite/tests/,
dashboard/tests/, review/tests/), shaped like
`review/tests/test_privacy_lint.py` (PR #233): route introspection over
`app.routes`, PARAM_EXPANDERS with two-way completeness guards, an explicit
documented classification for structurally-different responses, zero
network. Small in-idiom template lede fixes where a walked page genuinely
misses the bar.

## What was done

(filled at flip)

⚑ Self-initiated:

## 💡 Session idea

(filled at flip)

## ⟲ Previous-session review

(filled at flip)
