# 2026-07-11 — Board-row fleet chip + tooling: capability token (backlog promotions)

> **Status:** `complete` — PR #107 (`claude/fleet-chip-tooling-token`),
> squash-merge on `quality` green. (Flipped after the PR existed.)

- **📊 Model:** Claude Fable 5 · worker · routine-fired build slice (continuous mode, slice 18 — 07:39Z nudge) — family from this session's own harness, per ORDER 010.

**What this session was about:** the 07:39Z send_later continuation. Start
ritual clean (no orders past 010; heartbeat at HEAD is this chain's 07:13Z —
the ~08:00Z fire has not happened; open_work shows only the four known gen-1
leftovers; sibling #105 upgraded the kit to v1.10.0 mid-window). Work-ladder
rung 3, both coordinator picks bundled: **(a)** the **board-row fleet chip**
— each board repo row shows its lane's heartbeat age/stale state on the
owner's habit path (fetching ONLY the four board repos' status files over
the TTL cache — deliberately NOT the full 18-lane `fleet.overview()`
fan-out); **(b)** the **`tooling:` capability token** — a fired session
stamps its probe result (`pr-capable | ritual-only`) in the heartbeat so a
PR-tooling wall like the 04:03Z fire's is visible without branch
archaeology (the `rung:`-line pattern: KNOWN_KEYS leak-guard + README line
+ /fleet row).

## What was done

- **(a) `fleet.heartbeat_freshness(repo)`** (new): fetch ONE repo's
  `control/status.md` (TTL-cached), parse `updated:`, return the freshness
  dict — or `None` when the heartbeat is unreadable OR its stamp does not
  parse (no chip beats a guessed age). Board route gathers it for
  `config.REPOS` alongside the existing chips (route-level composition;
  `readiness.py` + `/api/readiness.json` untouched); `board.html` renders
  "lane heartbeat: <age> [· stale]" deep-linked to `/fleet`.
- **(b) `tooling:` token**: `control/README.md` optional-line doc;
  `fleet.KNOWN_KEYS` (leak-guard — the routine:-into-blockers class);
  `/fleet` row rendering the value and flagging `ritual-only` with a
  "cannot land work" badge. This repo's heartbeat writes
  `tooling: pr-capable` from this wake's close-out.
- **`tests/test_fleet_chip_tooling.py`** (+5, suites 228 → 233):
  heartbeat_freshness ok / missing-None / unparseable-stamp-None; board
  chip renders exactly once for the one mocked heartbeat + deep-links
  /fleet; no chip when all unreadable (board still 200); tooling
  KNOWN_KEYS no-leak; /fleet ritual-only warning render.
- **Backlog:** both bullets → Built. No decision-ledger entry — additive
  page nicety + an optional protocol line documented at its README home.

## Close-out (auto-drafted 2026-07-11 — edit, don't author)

<!-- substrate:auto-draft -->

**Evidence (auto-collected — verify, then keep or correct):**

- CORRECTED file list — the auto-draft's tree-wide baseline again included
  sibling/prior-slice merges (kit v1.9.0/v1.10.0 files, slice-16/17 files,
  control/status.md — NOT this slice's work; known limitation, noted on
  three cards now). THIS branch's diff against its base (verified via
  `git diff origin/main --stat`): `app/fleet.py` (`heartbeat_freshness`,
  KNOWN_KEYS `tooling`), `app/main.py` (board route),
  `app/templates/board.html`, `app/templates/fleet.html`,
  `control/README.md`, `tests/test_fleet_chip_tooling.py` (new),
  `docs/ideas/backlog.md`, this card.
- git: branch `claude/fleet-chip-tooling-token`, HEAD 4df1d98e3 at draft
  time (this flip commit supersedes it).
- verify: `python3 -m pytest tests/ botsite/tests dashboard/tests -q` —
  **233 passed**; `python3 bootstrap.py check --strict` — **all checks
  passed** with this card complete (kit v1.10.0).

**Judgment (the half only the session knows — resolve every slot):**

- Decisions made: per-repo freshness fetch over the 18-lane fan-out (the
  board's latency budget); None-over-guess for unparseable stamps;
  ritual-only flagged as "cannot land work" (the operational meaning, not
  just the token).
- Next session should know: the heartbeat now carries `tooling:` — fired
  sessions should stamp their probe result (the 08:00Z fire's heartbeat is
  the first natural test); nav overflow guard remains reserved for that
  fire; the captured backlog is nearly drained — remaining: nav guard +
  two manager-side asks (lanes.json, meta.md convention) + this slice's 💡.

⚑ Self-initiated: no — backlog promotions (rung 3), coordinator picks
(a)+(b).

## 💡 Session idea

**Backlog low-water signal in the heartbeat** — the captured/planned
backlog is nearly empty for the first time since the never-idle ladder
landed; the ladder's rung 5 says say "backlog dry" honestly, but there is
no machine token for ALMOST-dry. Worth having: when the captured+planned
count drops below ~3, the heartbeat notes carry `backlog: low (N left)` so
the manager routes new work BEFORE a lane hits upkeep-dry — routing latency
beats idle wakes. Deduped against `docs/ideas/backlog.md` + queue-state
NEXT: rung telemetry records which rung fired, not backlog depth; nothing
covers the low-water signal. Captured in `docs/ideas/backlog.md` (and this
wake's heartbeat already writes the first `backlog: low` note — dogfood).

## ⟲ Previous-session review

Slice 17 (same chain, PR #104) proved the route-level composition pattern
and pinned /api/readiness.json untouched by test — the right paranoia;
what it missed: its first test run used a bare TestClient against a route
that needs lifespan clients, costing a debug loop the test_app client
fixture had already solved — check how the EXISTING tests of a route
initialize the app before writing new ones (this slice reused the pattern
first try).
