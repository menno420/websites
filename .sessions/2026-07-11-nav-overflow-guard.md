# 2026-07-11 — Nav overflow guard: grouped "more ▾" dropdown (backlog promotion, last buildable)

> **Status:** `complete` — PR #109, branch `claude/nav-overflow-guard`.

- **📊 Model:** Claude Fable 5 · worker · routine-fired build slice (continuous mode, slice 19 — 08:21Z nudge) — family from this session's own harness, per ORDER 010.

**What this session was about:** the 08:21Z send_later continuation, timed
after the ~08:00Z 4-hourly fire window. Ritual findings: the fire left NO
trace (heartbeat at HEAD still this chain's 07:52Z, no new branch on
open_work, ZERO open PRs via MCP) — per the coordinator's decision tree the
reserved pick unlocks: **nav overflow guard** (rung 3, the LAST buildable
captured bullet — the low-water signal is already on the bus). The header
nav had grown to 11 top-level links, one per fleet-info slice, wrapping to
multiple rows on a phone with nobody's slice feeling responsible.

## What was done

- `app/templates/base.html` — nav reduced 11 → 6 top-level entries
  (readiness board, fleet, owner queue, activity, journal browser,
  **more ▾**); environments / projects / reviews / orders / ideas grouped
  in a no-JS `<details class="navmore">` dropdown. When a grouped page is
  active the details renders `open` and the summary carries `class="on"`
  (same highlight as top-level links). Pure HTML/CSS — plays with the
  existing sticky header and the 640px mobile media query; default
  disclosure marker suppressed (`list-style:none` +
  `::-webkit-details-marker`).
- `tests/test_nav_overflow.py` (+2) — every grouped + primary href stays
  reachable from any page; dropdown closed on non-grouped pages; `open` +
  highlighted summary on `/orders`. Offline via the `github._get`
  monkeypatch + `with TestClient(app) as c` lifespan pattern.
- `docs/ideas/backlog.md` — nav-guard bullet moved to Built (it was the
  last buildable captured bullet: **buildable backlog now dry**); slice 💡
  captured (nav manifest, below).

## Close-out (auto-drafted 2026-07-11 — edit, don't author)

<!-- substrate:auto-draft -->

**Evidence (corrected — the auto-collected list was tree-wide/polluted by
sibling merges; regenerated from `git diff origin/main --stat`):**

- code touched (1): `app/templates/base.html`
- docs touched (1): `docs/ideas/backlog.md`
- sessions touched (1): `.sessions/2026-07-11-nav-overflow-guard.md`
- tests touched (1): `tests/test_nav_overflow.py` (new, +2 tests)
- git: branch `claude/nav-overflow-guard`, born-red card first commit
  `1921781`, build commit `9c779a3`, this close-out commit flips the gate.
- verify: `python3 -m pytest tests/ -q` → **177 passed** (175 + 2 new);
  full three-service suite (`tests/ botsite/tests dashboard/tests`) →
  **235 passed**; `python3 bootstrap.py check --strict` → green. Born-red: first quality
  run held red by design on the in-progress card; this flip commit carries
  the real PR number (#109) and goes green.

**Judgment (the half only the session knows — resolve every slot):**

- Decisions made: no D-entry needed — a template-level presentation change
  inside the existing routes→templates layer; no contract, payload, or
  doctrine touched. Grouping choice (5 fleet-info/secondary pages under
  "more ▾", 5 primary destinations kept top-level) recorded here.
- Next session should know: buildable backlog is DRY after this reserved
  pick — rung 3 has nothing left; next useful work is rung 5 upkeep or new
  orders in control/inbox.md. Manager-side asks still outstanding:
  review-queue rows, lanes.json, meta.md convention, stale-branch prunes.

## 💡 Session idea

**Nav manifest: one `(href, label, group)` list driving base.html and a
membership test** — captured in `docs/ideas/backlog.md`. Worth having
because today the "which pages live under more ▾" decision exists only as
hand-kept template markup plus a hand-kept tuple in the test; page 12 can
be added top-level with nobody noticing the overflow guard was the point.

## ⟲ Previous-session review

Slice 18 (#107 board conveyor chips + heartbeat #108): clean — chips
live-verified on the deployed board, heartbeat carried the first
`tooling: pr-capable` stamp and the `backlog: low` signal, and the
reserved-pick handoff it set up is exactly what this slice consumed.
Workflow improvement adopted here: the coordinator's decision-tree framing
("if the fire took it / if it didn't") made the collision check a
30-second verdict instead of an investigation — worth using for every
reserved pick. Fire watch for the manager: the ~08:00Z 4-hourly fire
produced no visible session (no heartbeat, no branch, no PR) — second
silent window after the 04:03Z fire's stranded heartbeat (#98); the
send_later chain is currently the only consistent producer.
