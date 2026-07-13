# 2026-07-13 — repo freshness page: control-plane /freshness fleet view

> **Status:** `in-progress` — branch `claude/repo-freshness-page`; building
> the control-plane `/freshness` page (per-repo last commit, last session
> card, open PR count, heartbeat age); this card flips to `complete` at
> close-out.

- **📊 Model:** Fable 5 · worker · feature-slice

**What this session is about:** a new GET-only control-plane page,
`/freshness`, answering "which fleet repos are moving and which are stale?"
in one table. One row per repo from the fleet registry
(`fleet.resolve_lanes()`), each showing: last commit (short sha + age),
last `.sessions/` card date + age, open PR count, and heartbeat `updated:`
age where the repo carries `control/status.md`. Amber staleness marks past
threshold (heartbeat > `config.FLEET_STALE_HOURS`, commit > 7 days), honest
"unknown — <reason>" on every degraded fetch (never fabricated freshness,
never a 500), archived/hub lanes exempt with a dim note. Ships as
`app/freshness.py` (domain module over existing `fleet` + `github`
primitives), a `/freshness` route + `/freshness.json` twin in
`app/main.py`, `app/templates/freshness.html`, a nav-manifest registration
in `app/nav.py`, and an offline monkeypatched test suite in
`tests/test_freshness.py`.

## What was done

- (in progress)

⚑ Self-initiated: yes — ORDER 022 item 4 scan-and-initiate; fleet-grounding §8 goal 5 (fleet visibility surfaces)
