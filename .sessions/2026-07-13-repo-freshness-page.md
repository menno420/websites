# 2026-07-13 — repo freshness page: control-plane /freshness fleet view

> **Status:** `complete` — PR #235, branch `claude/repo-freshness-page`;
> the control-plane `/freshness` page ships with its `/freshness.json`
> twin and an offline 11-test suite; lands via the auto-merge enabler on
> green.

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

- **`app/freshness.py`** (new, 224 lines): domain module over the existing
  `fleet` + `github` primitives — one row per registry lane with the four
  movement signals (last commit short sha + age, newest dated
  `.sessions/YYYY-MM-DD-*.md` card + age, open PR count, heartbeat
  `updated:` age). `now` is injectable with a `clock.now()` fallback per
  the time-discipline convention.
- **Staleness classification**: amber strictly PAST threshold (heartbeat
  older than `config.FLEET_STALE_HOURS` — the existing /fleet threshold —
  OR last commit older than `COMMIT_STALE_DAYS = 7`); exactly AT a
  threshold is not stale. Archived/hub lanes are exempt — old ages there
  are honest history, rendered as a dim note, never amber.
- **Honest degradation everywhere**: any not-ok fetch renders
  "unknown — \<reason\>", never a fabricated freshness and never a 500;
  the lane set resolves live from the fleet-manager registry with the same
  visible fallback notice `/fleet` shows (`fleet.resolve_lanes()`).
- **Routes + surface**: GET `/freshness` + `/freshness.json` twin in
  `app/main.py`; `app/templates/freshness.html` (clarity lede, summary
  pills, one table); nav-manifest registration in `app/nav.py` under the
  overview category next to /fleet.
- **`app/fleet.py`**: `_commit_age`/`_open_pr_count` gained additive
  `sha`/`age_hours`/`reason` keys so /freshness reuses `repo_meta` without
  re-parsing — additive only, existing /fleet consumers untouched.
- **`tests/test_freshness.py`**: 11 offline monkeypatched tests (happy
  path, degraded fetches, JSON contract, threshold boundary at/past,
  exempt lanes), plus conscious manifest-pin updates in
  `tests/test_category_ia.py`, `tests/test_console_home.py`,
  `tests/test_time_discipline.py` for the new route.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — 957 passed, 1 warning (includes the 11 new freshness
  tests); `python3 bootstrap.py check --strict` — green apart from this
  card's own designed born-red HOLD (flipped by this close-out) and the
  pre-existing `owner-action-fields` advisory on control/status.md (never
  exit-affecting, not owned here).

**Decisions made:** commit-staleness floor set to 7 days (weekly cadence
floor so low-traffic-but-alive seats don't false-alarm) while heartbeat
staleness reuses `FLEET_STALE_HOURS` rather than growing a second knob;
strictly-past (not at-threshold) staleness so a seat exactly on cadence
never flickers amber; the fleet.py meta keys were extended additively
instead of building a parallel fetch path, so /freshness and /fleet stay
one source of truth per signal.

⚑ Self-initiated: yes — ORDER 022 item 4 scan-and-initiate; fleet-grounding §8 goal 5 (fleet visibility surfaces)

## 💡 Session idea

**Give /freshness the live-monitoring autorefresh /fleet has** — /fleet
and the board include `_autorefresh.html` + `/static/autorefresh.js`
(base.html carries the `.autorefresh` indicator styles already), but
/freshness ships static: a staleness page you leave open on a monitor is
exactly the page that should re-poll itself, otherwise it goes stale about
staleness. Cheap to add (the include + the script block, mirroring
fleet.html lines 5/135) and also a natural small follow-up to this PR.
Deduped against `docs/ideas/backlog.md`: no existing bullet covers
autorefresh on /freshness.

## ⟲ Previous-session review

The testing-ai-inventory session (#227) did well — its "document ALL
genuinely-consumed names, not just the minimum three" scope call and its
proven-red-then-green pin discipline are the honest-completeness bar this
session aimed at with the never-fabricated "unknown — reason" rows; its
habit of repairing downstream count pins it broke (the envhub 25-var
hardcodes) was reused here as the conscious manifest-pin updates landing
in the same commit as the route they pin, instead of as a surprise red in
the next unrelated PR.
