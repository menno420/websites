# 2026-07-18 — Fleet prompt-state panel: snapshot-age warning + fleet-manager outbox asks

> **Status:** `complete` — branch `claude/fleet-prompt-staleness`, PR
> **#408**. Truth-in-labeling fix for the /owner "Prompt state" panel:
> the failsafe snapshot's `captured_at` is frozen upstream (fleet-manager
> telemetry, a manager-wake artifact) — the panel reads live and is correct,
> but a bare stale timestamp reads as our bug. Adding the snapshot AGE + a
> `>24h stale, awaiting an upstream refresh` warning that attributes the freeze
> upstream; plus drafting the 4 cross-repo fleet-manager asks that fix the
> underlying data.

- **📊 Model:** Claude Opus 4.8 · high · feature build (owner-console snapshot-age warning + fleet-manager outbox asks)

**What this session is about:** the /owner console "Prompt state" panel
(`app/owner.py` `owner_board` → `prompts.console_rollup` → the drift-row model)
renders the fleet-manager `telemetry/triggers-snapshot.json` failsafe snapshot
LIVE over raw. That snapshot only refreshes on a manager-seat wake (an MCP-only
`list_triggers` dump); with the manager seat parked it froze at
`2026-07-17T16:32:25Z` (>24h). Our panel is CORRECT — it reads live and honest.
What we improve here is truth-in-labeling: make the staleness unmistakable and
clearly ATTRIBUTED upstream so it is not misread as a Websites bug, and route
the actual data fix cross-repo via our outbox. Rung: coordinator-dispatched
UX + cross-repo remediation (decide-and-flag, fully reversible — code + control
docs only).

## Plan

- **Part A (code):** compute the snapshot age from `captured_at` against an
  injectable `now` (the repo's `app.clock` discipline — never naive wall-clock),
  expose `age_hours` / `age_human` / `is_stale` on the console rollup's snapshot,
  and render in `owner.html` the age (e.g. "(30h ago)") plus, past 24h, a
  warning banner attributing the freeze upstream (mirrors fleet-manager's own
  roster-regen >24h warning). Deterministic test (pinned clock): stale renders
  the warning, fresh does not.
- **Part B (control):** append 4 cross-repo asks to `control/outbox.md`
  (lane→manager channel) for menno420/fleet-manager to action: (1) refresh the
  frozen triggers snapshot + arm the documented CCR fallback routine; (2) update
  `projects/websites/meta.md` Deployed-state table to the current v3.7 paste;
  (3) optional stub-table note for superbot-world / superbot-2.0; (4) a
  self-healing per-seat "stamp deployed prompt version at session-ender" rule.

## What was done

- **`app/prompts.py`:** `console_rollup()` now takes an injectable
  `now: datetime | None = None` (falls back to `app.clock.now()` — the repo's
  time-discipline; the #114 static guard forbids naive `datetime.now()` in
  age-measuring code, and route tests pin the clock via `clock.NOW_OVERRIDE`).
  New `_snapshot_age(captured_at, now)` parses the ISO-ish `captured_at`
  (mirrors `fleet._parse_iso`) and derives `age_hours` / `age_human` /
  `is_stale` against a new `SNAPSHOT_STALE_HOURS = 24`; the rollup enriches the
  failsafe-snapshot dict with those fields (+ `stale_hours`) only when the
  snapshot fetched OK. An unparseable/empty stamp is `captured_ok=False` — the
  raw timestamp is kept, no faked-fresh verdict. Local `_human_age` mirrors
  fleet's coarse "Nh ago"/"Nd ago" phrasing.
- **`app/templates/owner.html`:** the "failsafe snapshot: captured …" line now
  also shows the age (e.g. "(30h ago)"), and — only when `ok and is_stale` — a
  `warn` banner: "⚠ failsafe snapshot >24h stale (…) — awaiting an upstream
  fleet-manager refresh. This panel reads live; the snapshot is a manager-wake
  `list_triggers` dump frozen upstream, not a fault here." (links the frozen
  telemetry file). GET view, no CSRF change; styled with the existing owner
  `b warn` banner class. Mirrors the spirit of fleet-manager's own roster-regen
  >24h warning.
- **`tests/test_prompt_surfacing.py`:** +4 deterministic tests (pinned clock, no
  wall clock) — `console_rollup(now=…)` exposes age + `is_stale` past 24h and
  not before; the `/owner` route renders the age + the ">24h stale / awaiting an
  upstream / reads live" banner when stale and renders neither when fresh.
- **`control/outbox.md`:** appended one `## ASK` entry (lane→manager grammar,
  append-only) carrying the 4 paste-ready cross-repo asks to
  `menno420/fleet-manager` — (1) refresh the frozen `telemetry/triggers-snapshot.json`
  (frozen `2026-07-17T16:32:25Z`) + arm the documented CCR fallback routine;
  (2) update `projects/websites/meta.md` Deployed-state table to the current
  **v3.7 (2026-07-15)** paste (it records the superseded 2026-07-10 gen-2/v1
  state → the panel reads "stale"); (3) optional new-seat stub-table note for
  superbot-world / superbot-2.0 (the panel's "no parseable table" is already
  honest); (4) a self-healing per-seat "stamp deployed version at
  session-ender" rule so the panel self-maintains. Placed as `## ASK` — outside
  the `## REPORT` grammar the briefing pin (`tests/test_outbox_grammar_pin.py`)
  enforces, so the pin stays green.
- **Verified:** `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — **1886 passed, 1 warning** (exit 0; the warning is the
  pre-existing Starlette/httpx TestClient deprecation, unrelated).
  `python3 bootstrap.py check --strict` — the ONLY red is the by-design born-red
  HOLD on THIS card (no outbox/docs gate fired), released at this flip.
  Commits: `c88b7b0` (born-red card), `ae843a6` (Part A + Part B), heartbeat,
  + this flip.

⚑ Self-initiated: no — coordinator-dispatched (fleet-prompt-state remediation).

## 💡 Session idea

**Give the /prompts deployed-drift snapshot line the same age + upstream
attribution this session gave the owner console.** The public `/prompts` page's
deployed-vs-canonical table renders the identical failsafe-snapshot `captured_at`
(via `overview()` → `_build_deployed`'s `snapshot` dict) as a bare "as-of"
timestamp — the exact truth-in-labeling gap just fixed on `/owner`, still open
there. Lifting `_snapshot_age()` into the shared snapshot dict (compute it once
in `_build_deployed`, both surfaces read it) would (a) close the same
"stale-reads-as-our-bug" gap on the more-visited page and (b) collapse the two
staleness code paths — `fleet.freshness` for heartbeats and `_snapshot_age` for
the snapshot — toward one small `staleness(captured_at, threshold, now)` helper.
Worth it because the frozen-snapshot condition is upstream and will recur, so
both surfaces should attribute it, not just the gated one. Deduped against
`docs/ideas/backlog.md` (the "snapshot-aging banner" entries are the review-site
git-SHA banner, a different surface) + `docs/NEXT-TASKS.md` — not present.

## ⟲ Previous-session review

`.sessions/2026-07-18-fix-inverted-service-inventory.md` (PR #407) correctly
un-inverted the canonical/duplicate service inventory against live-Railway
ground truth and did the disciplined thing — chasing the `f027`→`fc91`
correction through all eight files AND the tests that pin them, then proposing a
committed `railway-ground-truth.json` pin so the next inversion is a red test
rather than a latent estate-retiring bug. The one loose end it flagged and left
(honestly) for a follow-up is the PROSE still carrying the old inverted canonical
— `CONSTITUTION.md`, `docs/current-state.md`, `OWNER-ACTIONS.md`, `review/ai.py`,
`botsite/testing_tasks.json`; that cleanup is now item 1 on this card's baton so
it does not rot.
