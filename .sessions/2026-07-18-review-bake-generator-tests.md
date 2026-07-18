# 2026-07-18 — Review bake-generator unit tests (R6)

> **Status:** `complete` — branch `claude/review-bake-generator-tests`; new
> unit coverage for the review service's three untested bake generators
> (`review/gen_snapshot.py`, `review/gen_fleet.py`, `review/gen_stats.py`),
> added as `review/tests/test_gen_snapshot.py`, `test_gen_fleet.py`, and
> `test_gen_stats.py`. Test-only: no generator, no `review/data/*.json`, no
> product code touched. Each test feeds a known input fixture, drives the
> generator's own transform, and asserts the baked output's shape, keys, types,
> and derived values — modeled on the existing `test_gen_questions.py`
> (network-free, deterministic, seam-stubbed). 29 tests added.

- **📊 Model:** Claude Opus · high · test writing (bake-generator tests)

**What this session is about:** the review service bakes committed JSON under
`review/data/` at build time so the network-free runtime container reads only
local files (the "never fake data" doctrine — see `gen_snapshot.py`'s module
docstring). Four generators feed that model. `gen_questions.py` already carries
a thorough unit suite (`review/tests/test_gen_questions.py`) that stubs its one
network seam and asserts the committed-file contract; the other three shipped
with NO unit coverage of their transforms. A bad bake — a miscounted PR-day
rollup, a dropped registry entry, a mis-parsed Link-header PR total — could
therefore ship silently, caught by nothing. R6 closes that gap: focused,
network-free unit tests over each generator's real transform and output shape.
Test-only — no route, no template, no serialized payload, no env, no generator
or data file touched.

⚑ Self-initiated: no — coordinator-dispatched backlog slice (R6).

## Close-out

**Evidence:**

- files touched this branch: `review/tests/test_gen_snapshot.py`,
  `review/tests/test_gen_fleet.py`, `review/tests/test_gen_stats.py` (three new
  test modules, 29 tests total), plus this session card and `control/status.md`.
  Coverage per generator:
  - **gen_snapshot** (10 tests): `_utc_date` offset→UTC-day normalization
    (incl. rollovers both directions); `commit_and_pr_days` per-day commit +
    unique-merged-PR rollups with newest-first PR dedup and separator-less-line
    skip, plus the empty-history all-zero case; `session_cards_per_day` dated-card
    counting with README/no-prefix skips (REPO_ROOT stubbed to a tmp `.sessions`),
    plus the empty case; `test_functions_at` per-file `git grep -c` tally and the
    CalledProcessError→0 honest-fail path; and a full `main()` bake asserting the
    snapshot's days/totals shape (git seams stubbed, date fixed in the past so the
    `partial`/today branch never time-bombs).
  - **gen_fleet** (11 tests): `parse_registry` LANES-literal extraction with
    non-dict-entry filtering, and the absent/malformed/non-Python-literal → `[]`
    cases; `parse_heartbeat` known-key grammar with continuation lines and
    colon-in-value, the unknown-leading-field drop, `FIELD_CAP` truncation marker,
    and the private-lane free-text scrub; the registry-only (`repo: None`)
    `bake_lane` branch (network-free); `bake_seats` pure seat↔lane join over the
    8-seat `SEATS` structure with honest missing-repo gaps and private-lane member
    exclusion; and `main()` fail-soft — both the keep-old-committed-file branch
    and the honest-empty-first-bake branch (the `_fetch` seam stubbed).
  - **gen_stats** (8 tests): `total_prs` Link-header last-page parse, the
    no-Link body-length fallback (1 and 0), and the API-error propagation;
    `repo_stats` normal two-call record shape, metadata-failure honesty, and the
    PR-count-failure-without-dropping-the-repo (`total_prs_reason`) path; and
    `main()` fail-soft — unreadable-fleet skip, no-repo-backed-lanes skip,
    all-failed no-write, and the normal write (`_api`/`repo_stats` stubbed,
    `GITHUB_TOKEN` deleted for a deterministic auth label).
- git: branch `claude/review-bake-generator-tests` from `origin/main` @ `3cfc349`
  (#390); commits `becffb0` (born-red card), `92729ab` (the three test modules),
  `224935d` (heartbeat status), + this flip.
- verify: `python3 -m pytest tests/ botsite/tests dashboard/tests review/tests
  -q` — **1792 passed, 1 warning** (exit 0; 1763 + 29 new); `python3 bootstrap.py
  check --strict` and `--require-session-log` (the CI form) — the only red during
  the session was the DESIGNED born-red hold on this card, released at this flip.
  No serialized JSON payload / env / contract changed — the tests read the
  generators' transforms through stubbed seams, so no contract-pin moved and no
  new env read was added.

**Judgment:**

- Decisions made: (1) MIRROR `test_gen_questions.py`'s discipline — stub the one
  network/IO seam per generator (`_git`, `_fetch`, `_api`) and drive the real
  transform, rather than re-implementing expected output; every expectation is
  derived from the generator's own code, never an invented invariant. (2) Add
  three separate modules (one per generator) instead of one omnibus file, matching
  the review suite's one-module-per-subject layout (`test_fleet.py`,
  `test_editions.py`, `test_gen_questions.py`). (3) Freeze every date in the PAST
  relative to any wall clock (the snapshot `main()` test uses 2026-07-13) so the
  `today`/`partial` and any age-sensitive branch is deterministic forever — the
  08:45Z time-bomb lesson the fleet suite already codifies. (4) Cover each
  generator's honest-fail / fail-soft path explicitly (git-grep→0, registry-fetch
  fail keep-old vs honest-empty, all-repos-failed no-write) — those are the
  branches a silent-bad-bake would ride through, so they are the point of R6.
  (5) Test-only: no generator, no `review/data/*.json`, no payload/env — nothing
  to contract-pin.
- Next session should know: the three new modules assert generator internals via
  module-level seams (`_git`/`_fetch`/`_api`) and constants (`REPO_ROOT`/
  `OUT_PATH`/`FLEET_PATH`/`FIELD_CAP`/`PRIVATE_LANES`/`SEATS`) — a rename or
  signature change to any of those will (correctly) red the matching test, which
  is the coverage working. `gen_fleet.head_probe` (git-transport) and the live
  REST-fetch success paths are intentionally left to the fail-soft branches; a
  future slice wanting end-to-end bake coverage would need a fake git remote /
  HTTP server, out of scope for R6's transform-shape mandate.

## 💡 Session idea

**A `review-bake --check` dry-run mode that bakes to a temp dir and diffs against
the committed `review/data/*.json` without writing.** Each generator's `main()`
already isolates its transform from its single write; a shared `--check` flag
(threaded through the four generators, or a thin `review/bake_all.py` wrapper)
would let CI run every bake against live sources and FAIL if the committed JSON
is stale versus what a fresh bake would produce — turning "did someone forget to
re-run the bake after the source moved?" from an invisible staleness (today only
the site's as-of banner tells, after deploy) into a red check. It reuses the seams
these R6 tests just exercised (the transforms are already pure of their writes),
and it complements, rather than duplicates, the unit coverage: the units prove the
transform is correct, `--check` proves the committed artifact is current.

## ⟲ Previous-session review

`.sessions/2026-07-18-arcade-schema-guard.md` (A4) added a read-only per-entry
schema guard over the committed `arcade.json`, importing every invariant from
`botsite.arcade` so the guard cannot drift from shipped code — the same
reflect-real-code, never-invent-an-invariant discipline this R6 work follows on
the bake-INPUT side: A4 guards what a generator's output must look like once
committed; R6 guards that the generator PRODUCES the right shape in the first
place, together closing the bake pipeline from transform to committed artifact.
