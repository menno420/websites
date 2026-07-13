# 2026-07-11 — /fleet lane source repointed to the fleet-manager registry (cron run 2 caught the break)

> **Status:** `complete` — PR #102 (`claude/lane-source-registry`),
> squash-merge on `quality` green. (Flipped after the PR existed; a sibling
> took #101 in the gap — flip-after-open keeps paying.)

- **📊 Model:** Claude Fable 5 · worker · routine-fired build slice (continuous mode, slice 16 — 06:20Z nudge) — family from this session's own harness, per ORDER 010.

**What this session was about:** the 06:20Z send_later continuation, timed
for the healthcheck-cron verdict. **Verdict: the schedule IS ALIVE — and its
first scheduled run caught a real regression.** Run 2 (`event: schedule`)
fired 03:40:51Z (~3.4h after the 00:17Z slot — GitHub best-effort delay; the
provisional CAPABILITIES wall DOWNGRADES to a delay note) and concluded
**FAILURE** with exactly the alert the manifest smoke check was built for:
all 6 service probes 200 PASS, `fleet-manifest live parse: FAIL (parsed to
ZERO lanes — manifest reformat suspected)`. Root cause: the superbot
manifest went `historical` on 2026-07-11 — **superseded by the generated
fleet-manager roster** (fleet-manager PR #59); live `/fleet` confirmed
running on the honest fallback. This slice repoints the lane source to the
new canonical registry.

## What was done

- **Investigation** (all live, verbatim evidence in the PR body):
  `list_workflow_runs healthcheck.yml` → run 2 event=schedule created
  03:40:51Z conclusion=failure; job log tail: 6× `200 PASS` +
  `fleet-manifest live parse: FAIL (parsed to ZERO lanes)`; live manifest
  fetch → `historical` header naming the supersession; live `/fleet.json` →
  `lane_source: fallback, reason: manifest parsed to zero lanes`; the new
  roster inspected (status snapshot, NO repo column) → the machine-readable
  mapping is `LANES` in `fleet-manager scripts/gen_roster.py`;
  `superbot-games control/status.md` probed 200 (default path holds).
- **`app/fleet.py`**: `REGISTRY_REPO/PATH` (fleet-manager,
  scripts/gen_roster.py); `parse_registry` (regex-capture the `LANES`
  literal → `ast.literal_eval` — pure data, never executed; absent → `[]`
  honest; malformed → raises to the fallback path); `registry_to_lanes`
  (registry-only `repo: None` seats skipped; hub/archived dispositions kept
  with honest notes; every lane reads `control/status.md`); `resolve_lanes`
  rewritten (source `registry`, key `registry_url`); old manifest parsers
  REMOVED (`parse_manifest`, `manifest_to_lanes`, `_lane_slug`, `_strip_md`,
  `_clean_model` — dead code is drift).
- **`app/config.py`**: `FLEET_LANES` fallback refreshed 10 → 18 seats.
- **`scripts/healthcheck.py`**: smoke check repointed
  (`check_fleet_registry`) — the standing alert now guards the NEW source.
- **`app/templates/fleet.html`**: registry wording + `registry_url` links.
- **Contract pin updated consciously** (its own protocol):
  `test_fleet_json_contract.py` TOP_KEYS `manifest_url` → `registry_url`,
  in the same PR that changes the payload.
- **Tests** (225 total): manifest tests rewritten as registry tests;
  `tests/test_healthcheck_manifest.py` → `tests/test_healthcheck_registry.py`.
- **Docs**: D-0035 (supersedes the lane-source half of D-0022 in effect);
  `docs/site.md` § 3a rewritten; `docs/CAPABILITIES.md` — the 02:23Z
  provisional wall RESOLVED as capability-with-caveat (crons fire, ±hours;
  never gate on a slot).
- **Live-verified pre-merge**: `resolve_lanes` → `source: registry,
  count: 18` (venture-lab, superbot-idle, superbot-mineverse,
  product-forge, idea-engine, sim-lab, fleet-manager auto-appear — lanes
  every fleet surface was silently missing on the fallback);
  `healthcheck.py` → `fleet-registry live parse: PASS (18 lanes parsed) ·
  RESULT: all healthy`.
- Housekeeping: another stray auto-draft (`.sessions/2026-07-11-session.md`)
  moved to the scratchpad (a drafted card with unresolved fills must not
  enter the gate's fallback pool).

## Close-out (auto-drafted 2026-07-11 — edit, don't author)

<!-- substrate:auto-draft -->

**Evidence (auto-collected — verify, then keep or correct):**

- CORRECTED file list — the auto-draft diffed the whole tree since session
  start, which included SIBLING merges pulled in via main syncs (kit v1.9.0
  upgrade card, bootstrap.py, .claude/CLAUDE.md etc. are NOT this slice's
  work). THIS branch's diff against its base (verified via
  `git diff origin/main --stat` at branch time): `app/fleet.py`,
  `app/config.py`, `app/templates/fleet.html`, `scripts/healthcheck.py`,
  `tests/test_app.py`,
  `tests/test_healthcheck_manifest.py → tests/test_healthcheck_registry.py`,
  `tests/test_fleet_json_contract.py`, `docs/site.md`, `docs/decisions.md`,
  `docs/CAPABILITIES.md`, this card (+ the flip's backlog capture).
- git: branch `claude/lane-source-registry`, HEAD 17b6ab435 at draft time
  (this flip commit supersedes it).
- verify: `python3 -m pytest tests/ botsite/tests dashboard/tests -q` —
  **225 passed**; `python3 bootstrap.py check --strict` — **all checks
  passed** with this card complete.

**Judgment (the half only the session knows — resolve every slot):**

- Decisions made: D-0035 (home: `docs/site.md` § 3a + the ledger);
  parse-the-generator's-literal over guess-the-roster-table (never-guess);
  contract-pin change done in-PR per its own protocol.
- Next session should know: post-merge live check should show
  `lane_source: registry` with 18 lanes on `/fleet.json`; if fleet-manager
  moves the LANES literal, the healthcheck alert fires again by design;
  the lanes.json ask is filed to the manager (heartbeat notes + backlog).
  A sibling upgraded the kit to v1.9.0 mid-slice (took #101) — expect the
  branch-up-to-date 405 and re-verify strict under v1.9.0 before merge.

⚑ Self-initiated: no — the cron-verdict task escalated into fixing the
regression the verdict uncovered (the standing watch doing its job).

## 💡 Session idea

**Ask the manager for a generated `lanes.json`** — `/fleet` now parses a
Python literal out of the generator's source, which is honest but couples
the site to a script's internals; one `docs/lanes.json` (repo, lane,
disposition) written by the same gen_roster run would make the registry a
real API and un-couple every consumer. Worth having because the
manifest→roster migration broke this site once tonight already; a declared
data file makes the next migration a non-event. Deduped against
`docs/ideas/backlog.md` + queue-state NEXT: the meta.md convention ask is
the same family (registry data contracts) but a different file. Captured in
`docs/ideas/backlog.md` (routing half: flagged to the manager in the
heartbeat).

## ⟲ Previous-session review

Slice 15 (same chain, PR #99) generalized one incident into doctrine at the
right moment and rescued the stranded heartbeat verbatim; what it missed:
its fact-check pass graded only BACKLOG bullets and did not re-verify the
standing WATCHES — the cron watch's "verdict at 06:17Z" framing survived
slices 12–15 while the real fire had ALREADY happened at 03:40Z; a watch is
a claim about the world and decays like any bullet — re-check watches when
you re-check bullets.
