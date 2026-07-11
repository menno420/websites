# 2026-07-11 — Conveyor-health idea chips on the readiness board rows (backlog promotion)

> **Status:** `complete` — PR #104 (`claude/board-conveyor-chips`),
> squash-merge on `quality` green. (Flipped after the PR existed.)

- **📊 Model:** claude-fable-5 · worker · routine-fired build slice (continuous mode, slice 17 — 07:00Z nudge) — family from this session's own harness, per ORDER 010.

**What this session was about:** the 07:00Z send_later continuation. Start
ritual clean (no new orders past 010; heartbeat at HEAD is this chain's own
06:39Z; open_work shows only the four known gen-1 leftovers). Work-ladder
rung 3 — this chain's designated pick: **conveyor-health chips on the
readiness board rows** (backlog; nav overflow guard stays reserved for the
~08:00Z fresh session). The board (`/`) is the owner's habit path; `/ideas`
already computes per-repo lifecycle counts — one small chip per board row
puts idea-flow health where the owner already looks, reusing
`ideas.repo_ideas`' TTL-cached counts (zero new fetch on a warm cache).

## What was done

- **`app/main.py`** (board route only — `readiness.py` untouched,
  composition over entanglement): gathers `readiness.board()` and
  `ideas.overview()` concurrently; builds `idea_chips` per repo from
  `state_counts` (skipping repos with no counts or a listing error) and
  passes it to the template. `/api/readiness.json` untouched.
- **`app/templates/board.html`**: an "ideas conveyor:" line under each repo
  row's header when a chip exists — lifecycle count chips deep-linking to
  the matching `/ideas?state=` filter + the honest "newest N of T" scope
  label; no chip when ideas are absent/unreadable (the board stays a
  readiness surface; `/ideas` is the honest home for idea errors).
- **`tests/test_board_conveyor_chips.py`** (+3, suites 225 → 228): chips
  render with filter deep-links for the repo with ideas (and exactly ONE
  chip line in the mock); no chip + board still 200 when the ideas path is
  unreadable; `/api/readiness.json` shape untouched. Test-harness note: the
  board route needs the `github._get`-offline + lifespan-TestClient pattern
  from test_app's client fixture (the first run failed on a bare
  TestClient — client not initialised).
- **Backlog:** board-chips bullet → Built. No decision-ledger entry —
  additive page nicety, no product-surface decision.

## Close-out (auto-drafted 2026-07-11 — edit, don't author)

<!-- substrate:auto-draft -->

**Evidence (auto-collected — verify, then keep or correct):**

- CORRECTED file list — the auto-draft's tree-wide diff again included
  SIBLING/PRIOR-slice merges pulled in via main syncs (kit v1.9.0 files,
  the slice-16 lane-source files, control/status.md etc. are NOT this
  slice's work). THIS branch's diff against its base (verified via
  `git diff origin/main --stat`): `app/main.py`,
  `app/templates/board.html`, `tests/test_board_conveyor_chips.py` (new),
  `docs/ideas/backlog.md`, this card.
- git: branch `claude/board-conveyor-chips`, HEAD 327bf2fc2 at draft time
  (this flip commit supersedes it).
- verify: `python3 -m pytest tests/ botsite/tests dashboard/tests -q` —
  **228 passed**; `python3 bootstrap.py check --strict` — **all checks
  passed** with this card complete (kit v1.9.0).

**Judgment (the half only the session knows — resolve every slot):**

- Decisions made: chips composed at the route level so `readiness.py` stays
  a pure readiness module; no-chip-on-error over error-badge-on-board (the
  board's noise budget); `/api/readiness.json` deliberately untouched.
- Next session should know: nav overflow guard remains the reserved pick
  for the ~08:00Z fresh session; post-merge live check should show chips on
  `/` for repos with ideas dirs and `/fleet.json` still registry-sourced;
  remaining captured bullets: nav guard, tooling: token, board-row fleet
  chip (this slice's 💡), plus the two manager-side asks.

⚑ Self-initiated: no — backlog promotion (rung 3), this chain's designated
pick.

## 💡 Session idea

**Board-row fleet chip (heartbeat freshness on the habit path)** — the same
composition trick can chip each board row with its lane's heartbeat age from
`fleet.overview()`'s cached lanes ("heartbeat 12m ago" / stale badge), so
the owner's FIRST glance carries the one signal /fleet exists for without a
second click. Worth having because the board row and the fleet lane for a
repo are today two pages apart, and the chips pattern (route-level gather,
no readiness.py change, no JSON change) is now proven cheap. Deduped
against `docs/ideas/backlog.md` + queue-state NEXT: nothing covers
board-row heartbeat chips; distinct from the retired unseen-orders badge
(that was inbox-vs-status commit heuristics). Captured in
`docs/ideas/backlog.md`.

## ⟲ Previous-session review

Slice 16 (same chain, PR #102) turned a failing standing watch into a
root-caused, live-verified repoint within one wake — investigation before
code, never-guess honored (parsing the generator's literal instead of
guessing the roster table); what it missed: its auto-draft evidence had to
be hand-corrected for a file list polluted by sibling merges — when
resolving the auto-draft, always regenerate the list from THIS branch's
diff (done again on this card; the auto-draft's tree-wide baseline is a
known limitation now noted twice).
