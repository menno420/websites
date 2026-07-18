# 2026-07-18 — Bundle the pure test/guard adds (X2)

> **Status:** `in-progress` — branch `claude/test-coverage-bundle`; a TEST-ONLY
> coverage bundle that raises the safety floor by pinning existing-but-untested
> behaviour. Three behaviours already ship in the code but had no dedicated
> test, so a regression in any of them would pass CI silently: **C9** the open-PR
> truncation flag (`readiness.repo_readiness` `prs.capped`, the "(capped)"
> marker on the board / owner page), **C11** the TTL-cache poison guard
> (`app/github.py:204` — successes and stable negatives are cached, transient
> 429/5xx/network failures never are), and **R7** the tie between the bake's
> closed-without-answer `ADVISORY:` log lines and the answer-debt nag RENDERED on
> `/questions` (`review/story.answer_debt`), so the two surfaces can never
> silently disagree. No product code, serialized payload, env, or workflow is
> touched — X2 only ADDS tests for behaviour that already exists.

- **📊 Model:** Claude Opus · high · test writing

**What this session is about:** X2 is the cross-cutting quick win in
`docs/NEXT-TASKS.md` — bundle the remaining pure test/guard adds into one green,
zero-product-risk PR. Its constituent items are C9 (pagination-truncation
tests), C11 (cache-eviction / unboundedness test), R6 (the three review bake
generators — ALREADY landed as #391), and R7 (advisory-line assertion for
`gen_questions` closed-without-answer). R6 is done, so this session covers the
still-open three: C9, C11, R7. Each is a behaviour the code already exercises
in production but that no test names — the exact "silent cap / silent poison /
silently-lying surface" class the items were written to close. Every test is
network-free and deterministic, derived from the REAL implementation (not
invented behaviour), and lives in an existing test dir (`tests/`,
`review/tests/`).

⚑ Self-initiated: no — coordinator-dispatched backlog slice (X2).

## Close-out

**Evidence:**

- items covered (3 of the 3 still-open X2 constituents; R6 already landed #391):
  - **C9 · pagination-truncation** — [[fill: N tests]] in
    `tests/test_pr_truncation_cap.py`. [[fill: what they assert about
    readiness.repo_readiness prs.capped / open_count at exactly 100 vs under]]
  - **C11 · cache-eviction / poison guard** — [[fill: N tests]] in
    `tests/test_github_cache_eviction.py`. [[fill: what they assert about which
    statuses are cached vs the transient statuses that must never poison the
    TTL cache]]
  - **R7 · advisory ↔ rendered-debt parity** — [[fill: N tests]] in
    `review/tests/test_questions_advisory_debt_parity.py`. [[fill: what they
    assert tying gen_questions.advise_unanswered output to story.answer_debt]]
- items SKIPPED: [[fill: none, or which + why — e.g. a candidate that would need
  a product change]]
- files touched this branch: [[fill: the three new test files + this card +
  control/status.md]]
- git: branch `claude/test-coverage-bundle` from `origin/main` @ [[fill: base
  sha]]; commits [[fill: born-red card, tests, heartbeat, this flip]].
- verify: [[fill: verbatim final lines — four-suite pass count, both bootstrap
  checks exit 0; the only red the DESIGNED born-red hold on this card, released
  at this flip]].

**Judgment:**

- Decisions made: [[fill: the real-behaviour anchoring calls — e.g. C9 asserts
  the SURFACED prs.capped flag (readiness.py) not the un-flagged run_jobs cap;
  C11 asserts the poison guard's ACTUAL behaviour, not a bound the unbounded
  dict does not have; R7 freezes `now` to make the aged-debt wording
  deterministic while still exercising the real functions]].
- Next session should know: [[fill: what remains on the X2 / NEXT-TASKS baton]].
