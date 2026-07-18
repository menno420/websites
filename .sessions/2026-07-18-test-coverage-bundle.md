# 2026-07-18 — Bundle the pure test/guard adds (X2)

> **Status:** `complete` — branch `claude/test-coverage-bundle`; a TEST-ONLY
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
  - **C9 · pagination-truncation** — 4 tests in
    `tests/test_pr_truncation_cap.py`. They drive `readiness.repo_readiness` for
    a non-`websites` repo (no deploy board) with `github.repo_api` mocked so only
    the `/pulls` envelope carries data, and assert the surfaced truncation flag:
    exactly 100 open PRs sets `prs.capped is True` (with `open_count == 100` and
    the head PR still surfaced as `oldest`); 99 leaves `capped is False`; zero is
    not a cap (`oldest is None`); and a degraded 502 / ok-but-non-list payload
    never fabricates a cap. Pins the SURFACED flag (`readiness.py:398`), which the
    board / owner template renders as "(capped)".
  - **C11 · cache-eviction / poison guard** — 13 tests in
    `tests/test_github_cache_eviction.py`. They run the REAL `github._get`
    against an `httpx.MockTransport` (the guard lives inside `_get`, so a mocked
    `_get` would bypass the code under test) and read the module cache directly:
    successes and stable negatives (200/201/204/404/403/401) populate the cache
    and serve a `cached=True` second read without re-hitting the transport;
    transient failures (429/500/502/503, and a network error → status-0 envelope)
    leave the cache empty and re-fetch every time — the poison guard at
    `github.py:204`. `refresh=True` bypass and `clear_cache`'s drop count are
    pinned alongside. Asserts the guard's ACTUAL behaviour (which statuses are
    cached), NOT a size bound the unbounded dict does not have.
  - **R7 · advisory ↔ rendered-debt parity** — 4 tests in
    `review/tests/test_questions_advisory_debt_parity.py`. They tie
    `gen_questions.advise_unanswered`'s printed `ADVISORY:` lines to
    `story.answer_debt`'s rendered debt list (the `/questions` `q_nag`): the two
    surfaces name the SAME closed-without-answer records (answered + open excluded
    from both) and each advisory line's day count equals that record's rendered
    `debt_days` — 3 days, a singular "1 day", and the binary "closed without a
    published answer" for a record with no `closed_at`. `now` is frozen to
    2026-07-13 by wrapping the module-level `answer_debt_days` (the name
    `advise_unanswered` reads), so the aged wording is deterministic while the
    REAL functions still run.
- items SKIPPED: none. All three still-open X2 constituents already existed in
  the code and needed only a test; none required a product change. (R6, the
  fourth constituent, was already covered by #391 — not re-done.)
- files touched this branch: three new test files
  (`tests/test_pr_truncation_cap.py`, `tests/test_github_cache_eviction.py`,
  `review/tests/test_questions_advisory_debt_parity.py`) + this session card
  (`.sessions/2026-07-18-test-coverage-bundle.md`) + the heartbeat
  (`control/status.md`). No product code, serialized JSON, env, or workflow.
- git: branch `claude/test-coverage-bundle` from `origin/main` @ `ede6221`
  (#394); commits `e083418` (born-red card), `db1335d` (the 21 tests), `095717e`
  (heartbeat status), + this flip.
- verify: `python3 -m pytest tests/ botsite/tests dashboard/tests review/tests -q`
  — **1828 passed, 1 warning** (exit 0; 1807 + 21 new: C9 ×4, C11 ×13, R7 ×4).
  `python3 bootstrap.py check --strict` and `--require-session-log` — both exit
  0; the only red the DESIGNED born-red hold on this card, released at this flip.
  The one advisory warning is the pre-existing Starlette/httpx TestClient
  deprecation, not this work.

**Judgment:**

- Decisions made: (1) C9 asserts the SURFACED `prs.capped` flag in
  `readiness.py` rather than the un-flagged `per_page=100` cap in
  `github.run_jobs` — the run-jobs path deliberately adds no truncation flag (its
  docstring says a >100-job run would need pagination it does not add), so there
  is no surfaced behaviour there to pin; the PR cap is the one truncation the
  board actually signals, so that is where the honesty test belongs. (2) C11
  asserts the poison guard's ACTUAL behaviour — WHICH statuses are cached — and
  deliberately does NOT assert an eviction/size bound: the cache is an unbounded
  per-URL dict with no LRU, so a "bounded" assertion would test invented
  behaviour; the real, load-bearing invariant is "transient failures never
  poison the TTL", and that is what the tests lock. (3) R7 froze `now` by
  wrapping the module-level `answer_debt_days` the bake calls, rather than
  stubbing it — the real day-count arithmetic still runs, only its clock is
  pinned, so the parity test exercises the true function on both surfaces at one
  instant. (4) Every test drives the real code path (the real `_get` over a mock
  transport, the real `repo_readiness`, the real `advise_unanswered` +
  `answer_debt`) rather than re-implementing the behaviour in the test — a
  coverage add is only worth landing if a real regression trips it.
- Next session should know: X2 is now fully discharged (R6 #391 + C9/C11/R7
  here). The NEXT-TASKS baton's high-value slices are largely exhausted; the
  remaining named item is B6 (config-drift flags on the dashboard `/env`
  surface), which NEEDS a design call — a names-only committed manifest vs the
  live env the dashboard cannot read — before it is buildable. Blocked-not-mine:
  O-020/O-021 (owner creds), R10 (workflow-touch). The EAP goes read-only
  2026-07-21.

## 💡 Session idea

**A "surfaced-flag has a test" lint for the honesty booleans.** X2 existed
because three honesty signals the code computes — `prs.capped`, the cache poison
guard, the answer-debt nag — shipped with no test naming them, and only a
backlog audit noticed. The recurring class is a boolean the UI renders (a
"(capped)" marker, an "unavailable" glyph, a debt nag) whose FALSE-path or
compute logic no test exercises, so it can silently invert. A lightweight
meta-test could grep the templates for the honesty-flag keys they read
(`.capped`, `.known`, `.n`/`debt_days`, the `red-by-design` states) and assert
each key name appears as an asserted attribute somewhere under `tests/` /
`review/tests/` — a cheap "every rendered honesty flag is pinned by at least one
test" tripwire. Distinct from the NAV/route-completeness idea on the previous
card (that checks pages are REACHABLE); this checks the boolean SIGNALS a page
renders are TESTED. It would have flagged all three X2 gaps before a human did.

## ⟲ Previous-session review

`.sessions/2026-07-18-review-questions-nav.md` (R1) surfaced the built
`/questions` page in the review NAV — a first-class page that worked but was
invisible for want of one manifest entry. X2 is the same instinct one layer
down: `/questions` also computes an answer-debt nag that was rendered but
untested, so R7 here pins exactly that surface R1 just made reachable — R1 made
the page discoverable to reviewers, R7 makes its debt signal un-regressable in
CI. Both replace "trust the surface" with a test that asserts the property
directly.
