# 2026-07-11 — Bus doctrine: relay/stranded-landing line + backlog fact-check pass

> **Status:** `complete` — PR #99 (`claude/relay-doctrine-backlog-factcheck`),
> squash-merge on `quality` green. (Flipped after the PR existed.)

- **📊 Model:** Claude Fable 5 · worker · routine-fired build slice (continuous mode, slice 15 — 04:12Z nudge) — family from this session's own harness, per ORDER 010.

**What this session was about:** the 04:12Z send_later continuation. The
start ritual (open_work.py) surfaced a SECOND stranded case in one night:
the 04:03Z routine-fired session's own heartbeat pushed-unmerged behind the
documented PR-tooling wall — **rescued verbatim as PR #98** per its own
`landing:` ask, before any new work. Inbox: nothing past 010 (done). Rung 3
bundle: **(b)** the relay/stranded-landing doctrine line in
`control/README.md` (closing the capture the ORDER 010 relay incident
filed, now generalized by tonight's second case), and **(a)** the **backlog
fact-check pass** — grep every remaining `captured` bullet against the
codebase and retire the stale ones with why. ((c) board-row conveyor chips
left unclaimed for a build-focused wake; the 06:17Z cron verdict correctly
not re-checked early.)

## What was done

- **RESCUE first (PR #98, merged b09d0b1)**: the 04:03Z fire's heartbeat —
  `landing: pushed-unmerged claude/status-heartbeat-2026-07-11-0403z`, no
  PR tooling in that session (its own ToolSearch probe, matching the
  documented wall) — landed VERBATIM. Its record (fire confirmation,
  ritual-only wake, and a provenance note for the manager about an
  anomalous mid-wake system reminder it surfaced rather than suppressed)
  is preserved on main history.
- **(b) `control/README.md` § "Landing other sessions' control-only
  work"**: one writer per file governs who WRITES, not who LANDS — any
  session may open/merge a green `control/**`-only relay or stranded
  heartbeat, verbatim, never editing while landing; both same-night
  incidents cited (#94, #98).
- **(a) Fact-check pass over every remaining `captured` bullet** (habit
  line added to `docs/ideas/README.md` § Lifecycle): **"unseen orders?"
  badge → RETIRED** (superseded by `/orders` — actual outstanding-order
  computation beats the inbox-commit-newer-than-status heuristic; grep
  confirmed nothing of it was ever built); **nav overflow guard** —
  still-live (10 nav links counted in `base.html`); **board-row conveyor
  chips** — still-live (no idea counts in `app/readiness.py`); **meta.md
  state-line convention** — still-live (manager-side ask, standing).
- **Backlog:** relay-protocol → Built; fact-check-pass → Built (first
  execution IS this slice); unseen-orders → Retired with why.

## Close-out (auto-drafted 2026-07-11 — edit, don't author)

<!-- substrate:auto-draft -->

**Evidence (auto-collected — verify, then keep or correct):**

- files touched: `control/README.md`, `docs/ideas/README.md`,
  `docs/ideas/backlog.md`, this card — the auto-draft had no session-start
  anchor; list verified by hand against `git diff origin/main --stat`.
- git: branch `claude/relay-doctrine-backlog-factcheck`, HEAD 2233cdd3e at
  draft time (this flip commit supersedes it).
- verify: `python3 -m pytest tests/ botsite/tests dashboard/tests -q` —
  **224 passed**; `python3 bootstrap.py check --strict` — **all checks
  passed** with this card complete (kit v1.8.0).

**Judgment (the half only the session knows — resolve every slot):**

- Decisions made: land-verbatim as the rescue rule (never edit while
  landing — the rescuer's own overwrite supersedes normally); the
  fact-check habit's home is `docs/ideas/README.md` (the backlog's own
  lifecycle doc), not the char-budgeted instructions file.
- Next session should know: **healthcheck cron verdict at 06:17Z** — the
  next chain nudge is timed after it; remaining captured bullets are all
  confirmed-live (nav guard, board chips, meta.md ask); the 04:03Z
  session's provenance note (anomalous system reminder) is on main for the
  manager via PR #98.

⚑ Self-initiated: no — coordinator picks (a)+(b) (rung 3) + the
stranded-work rescue duty.

## 💡 Session idea

**`tooling:` capability token in the fired session's heartbeat** — the
04:03Z session discovered its PR-tooling wall mid-wake and correctly went
ritual-only, but the next tooled session only learned it by finding the
stranded branch. Worth having: the routine-fired protocol's mandated probe
should also stamp its result as a `tooling: pr-capable | ritual-only`
heartbeat token, so /fleet and the chain SEE at a glance which fires can
land work and the manager can spot a systemic tooling regression across
lanes (three ritual-only fires in a row = platform issue, not chance).
Deduped against `docs/ideas/backlog.md` + queue-state NEXT: heartbeat
enrichment covers routine/landing/rung but not tooling capability.
Captured in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

Slice 14 (same chain, PR #96) executed an order as verification-not-build
correctly and held claim-first even at P3; what it missed: after merging
the manager's relay #94 it did not ask whether the RELAY PATTERN itself
needed doctrine (this slice's (b) — one incident is an event; the second
same-night incident made it a pattern); when you handle an incident
manually, ask immediately whether the manual step is about to become a
recurring role.
