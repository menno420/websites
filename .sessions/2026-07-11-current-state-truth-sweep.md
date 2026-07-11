# 2026-07-11 — current-state.md truth sweep (rung 5 upkeep, backlog dry)

> **Status:** `complete` — PR #111, branch `claude/current-state-truth-sweep`.

- **📊 Model:** claude-fable-5 · worker · routine-fired upkeep slice (continuous mode, slice 20 — 08:57Z nudge) — family from this session's own harness, per ORDER 010.

**What this session was about:** the 08:57Z nudge with the backlog DRY —
orders re-read (ORDER 010 still newest, done), so rung 5 honest upkeep.
Drift check of `docs/current-state.md` (orientation doc #2, "what is true
right now") against main HEAD found it last truly updated at PR #67 —
four stale claims a fresh session would trust:

1. kit version stated as v1.6.0 (is v1.10.0 since #101/#105);
2. "durable owner PAT is set … owner TODO closed" (live finding 2026-07-10/11:
   token UNSET, ⚑ re-filed in docs/owner/OWNER-ACTIONS.md);
3. the PR #36 entry presents the superbot fleet-manifest as the canonical
   lane registry (superseded 2026-07-11 by the gen_roster.py registry
   migration, #102);
4. "Recently shipped" ends at #67 (17 slices behind) and "Next steps" still
   points at the queue-state NEXT list, which is exhausted — rung-3 source
   is docs/ideas/backlog.md, currently dry.

## What was done

- `docs/current-state.md` — all four claims corrected against main HEAD
  (each with the ledger's "this passage said X until DATE" honesty
  convention); one consolidated 2026-07-11 chain entry added to Recently
  shipped (#69→#109 + 2 rescues, per-slice detail deferred to `.sessions/`
  cards + `docs/site.md`); Next steps re-pointed at the backlog/inbox with
  the dry-state noted.
- **Live catch during the sweep — time-bomb test defused:**
  `tests/test_fleet_enrichment.py::test_overview_sorts_stranded_landing_above_healthy_and_counts`
  passed at 08:31Z, failed at 09:05Z on an untouched tree (verified via
  `git stash`). Root cause: `fleet.overview()` measured the fixtures'
  fixed `updated:` stamps against the REAL wall clock; at
  2026-07-11T08:45Z the plain lane crossed `FLEET_STALE_HOURS`, both lanes
  collapsed into attention rank 2, and within-rank age ordering flipped
  the sort. Fix: `app/fleet.py` `overview()` gains the same injectable
  `now=` every other age-measuring function in the module already has
  (defaults to wall clock, zero caller change); the test pins its frozen
  `NOW` with a comment recording the incident. Audited every other test
  file carrying fixed `updated:` stamps: all either pass frozen `now=` to
  pure functions or assert time-monotonic-safe properties (stale stays
  stale) — this was the only bomb.

## Close-out (auto-drafted 2026-07-11 — edit, don't author)

<!-- substrate:auto-draft -->

**Evidence (corrected — the auto-collected list was tree-wide/polluted by
sibling merges; regenerated from `git diff origin/main --stat`):**

- code touched (1): `app/fleet.py` (injectable `now=` on `overview()`)
- docs touched (1): `docs/current-state.md`
- sessions touched (1): `.sessions/2026-07-11-current-state-truth-sweep.md`
- tests touched (1): `tests/test_fleet_enrichment.py`
- (plus `docs/ideas/backlog.md` in the close-out commit — slice 💡)
- git: branch `claude/current-state-truth-sweep`, born-red card first
  commit `54454c5`, build commit `95d501d`, this close-out commit flips
  the gate.
- verify: `python3 -m pytest tests/ botsite/tests dashboard/tests -q` →
  **235 passed** (deterministically; was 1 failed pre-defuse);
  `python3 bootstrap.py check --strict` → green. Born-red: first quality
  run held red by design on the in-progress card; this flip commit
  carries the real PR number (#111).

**Judgment (the half only the session knows — resolve every slot):**

- Decisions made: no D-entry — a doc-truth correction plus a
  test-determinism fix following the module's existing `now=` convention;
  no contract, payload, or doctrine change. The `overview()` signature
  gain is additive and default-preserving.
- Next session should know: backlog still DRY; current-state.md is now
  accurate as of #111 — keep the chain entry pattern (one consolidated
  bullet per continuous-mode chain, not per slice). The next fixed-stamp
  fixture is the time-bomb risk; see the idea below.

## 💡 Session idea

**Time-discipline guard for tests** — captured in `docs/ideas/backlog.md`.
Worth having because the 08:45Z bomb sat green for days and detonated on
wall-clock time alone (nothing in any diff); a tiny suite-level guard
(grep-style check that age-measuring entry points are not called from
tests without a frozen `now=`) turns the next one into a review-time
failure instead of a 4-hourly-fire mystery.

## ⟲ Previous-session review

Slice 19 (#109 + heartbeat #110): clean — nav dropdown live-verified in
both states (closed on /fleet, open + highlighted on /orders); merge was
405-free because the branch was cut at HEAD minutes earlier. One workflow
improvement adopted from it: keep suite-scope explicit in evidence lines —
slice 19's card initially said "pytest tests/ → 235 passed" when 235 is
the FULL three-service suite (tests/ alone is 177); caught and corrected
pre-merge, and this card writes both numbers explicitly.
