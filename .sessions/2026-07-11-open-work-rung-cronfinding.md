# 2026-07-11 — Wake-tooling batch: cron no-show finding + open-work script + rung telemetry

> **Status:** `complete` — PR #90 (`claude/open-work-rung-cronfinding`),
> squash-merge on `quality` green. (Flipped after the PR existed.)

- **📊 Model:** Claude Fable 5 · worker · routine-fired build slice (continuous mode, slice 12 — 02:22Z nudge)

**What this session was about:** the 02:22Z send_later continuation (timed
after what the record believed was the healthcheck cron's first slot).
Collision check: heartbeat at HEAD is this chain's 01:51Z stamp — clear.
Inbox: nothing past 009. Three-part bundle: **(a)** the healthcheck cron
verdict — a NO-SHOW, plus the discovery that this chain's own "~02:17Z"
expectation was a cron-arithmetic error (`17 */6 * * *` anchors to hours
0/6/12/18 — the real first slot was 00:17Z, which ALSO did not fire) —
captured as a dated CAPABILITIES finding, provisional until the 06:17Z
slot; **(b)** the **open-PR-awareness script** (backlog; lived twice on
2026-07-10); **(c)** **ladder-rung telemetry** — the `rung:` heartbeat line
(backlog), with the KNOWN_KEYS leak-guard the routine:-line incident
taught.

## What was done

- **(a) Cron verdict + CAPABILITIES append**: `list_workflow_runs
  healthcheck.yml` at 02:22Z → `total_count: 1`, only the 21:03Z
  `workflow_dispatch` run — NO `schedule` event has ever fired; the first
  eligible slot (00:17Z) passed ~2h earlier. Appended to
  `docs/CAPABILITIES.md` as a dated PROVISIONAL wall with verbatim
  evidence, the known GitHub best-effort/new-schedule-lag explanations, the
  06:17Z re-check condition, and the workaround (wake sessions run
  `scripts/healthcheck.py` themselves; manual dispatch proven by run 1).
  Also corrected on the record: five heartbeats said "~02:17Z" — cron
  fields are wall-clock anchored; compute slots from the epoch, not
  "+interval from now".
- **(b) `scripts/open_work.py`** (+ provenance/kill-switch header):
  `remote_branches` (pure `git ls-remote`), `open_prs` (api.github.com,
  None on the documented wall), `has_unmerged_commits` (single-ref fetch +
  `merge-base --is-ancestor`), and a pure `classify` — PR-OPEN / PR-LESS /
  MERGED-STALE / PR-UNKNOWN / UNKNOWN, partial truth always labeled.
  **Live run this session**: PR list unreachable (labeled), four branches
  found — exactly the known gen-1 leftovers (harden-verify,
  rework-dashboard, wire-github-token-docs, manager/control-plant), zero
  false alarms on the auto-deleted merged slice branches.
- **(c) `rung:` telemetry**: `control/README.md` optional-line doc
  (`rung: <order|queue|backlog|self|upkeep-dry>[, …]`), `fleet.KNOWN_KEYS`
  (leak-guard), `/fleet` row when present; this repo's heartbeat writes it
  from this wake's close-out on.
- **`tests/test_open_work_and_rung.py`** (+5, suites 207 → 212): classify
  with live PR list (all four states), honest degradation without the PR
  list, empty-input, rung KNOWN_KEYS no-leak parse, /fleet rung row render.
- **Backlog:** open-PR-awareness → Built (+ idea file front-matter),
  ladder-rung telemetry → Built. No decision-ledger entry — tooling + an
  optional protocol line, no product-surface decision beyond what
  control/README.md documents.

## Close-out (auto-drafted 2026-07-11 — edit, don't author)

<!-- substrate:auto-draft -->

**Evidence (auto-collected — verify, then keep or correct):**

- files touched: `scripts/open_work.py` (new),
  `tests/test_open_work_and_rung.py` (new), `app/fleet.py` (KNOWN_KEYS),
  `app/templates/fleet.html` (rung row), `control/README.md` (format line),
  `docs/CAPABILITIES.md` (dated finding), `docs/ideas/backlog.md`,
  `docs/ideas/open-pr-awareness-at-wake-2026-07-10.md`, this card — the
  auto-draft had no session-start anchor; list verified by hand against
  `git diff origin/main --stat`.
- git: branch `claude/open-work-rung-cronfinding`, HEAD 90dad4d28 at draft
  time (this flip commit supersedes it).
- verify: `python3 -m pytest tests/ botsite/tests dashboard/tests -q` —
  **212 passed**; `python3 bootstrap.py check --strict` — **all checks
  passed** with this card complete (kit v1.8.0); `scripts/open_work.py`
  executed live (output summarized above).

**Judgment (the half only the session knows — resolve every slot):**

- Decisions made: cron finding filed PROVISIONAL, not final (one no-show +
  documented platform lag is not yet a proven wall); `rung:` values kept to
  the five ladder rungs, comma-joinable.
- Next session should know: **re-check the healthcheck cron after 06:17Z**
  (`list_workflow_runs healthcheck.yml` — a second no-show upgrades the
  CAPABILITIES entry to a real wall and the workaround becomes doctrine);
  the four gen-1 leftover branches are prune-candidates awaiting delete
  rights; remaining backlog picks: nav overflow guard, /ideas state
  filter, wait-deploy.py, review-row auto-check, backlog fact-check pass.

⚑ Self-initiated: no — coordinator cron-verdict task + two backlog
promotions (rung 3).

## 💡 Session idea

**Cron-slot helper (`next-slot`)** — a tiny utility (script function or
`open_work.py` addition) that parses a workflow's cron expression and
prints its next wall-clock fire slots, so heartbeats stop hand-computing
them. Worth having because this wake found FIVE heartbeats carrying the
same wrong "~02:17Z" slot (cron anchors to wall-clock hours, not "+interval
from now") and plans were timed against the wrong number — a mechanical
helper makes the record self-correcting. Deduped against
`docs/ideas/backlog.md` + queue-state NEXT: nothing covers cron-slot
computation. Captured in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

Slice 11 (same chain, PR #88) did investigation-before-build exactly right —
sizing the PR #9 branch first and converting a potential salvage slice into
a cheap retire-with-evidence; what it missed: it scheduled this nudge "after
the 02:17Z cron" using the SAME wrong slot arithmetic the whole record
carried — when a plan depends on a timer, verify the timer's actual
schedule semantics instead of inheriting the record's number (the
CAPABILITIES lesson this slice adds keeps the next reader from inheriting
it again).
