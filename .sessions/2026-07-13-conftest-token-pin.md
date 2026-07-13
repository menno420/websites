# 2026-07-13 — tests: suite-level ambient-token pin in tests/conftest.py (ORDER 027 item 5)

> **Status:** `complete` — PR #309, branch `claude/conftest-token-pin-0713`;
> a new `tests/conftest.py` autouse fixture pins every control-plane test
> to the unset token rung (`config.GITHUB_TOKEN`/`config.RAILWAY_TOKEN`
> forced to `""`, both env vars deleted), making the
> unpinned-reason-assertion flake class structurally impossible; lands via
> the auto-merge enabler on green.

- **📊 Model:** Claude 5 family · worker · ORDER-027-item-5 slice (test infra)

**What this session was about:** ORDER 027 item 5 (`control/inbox.md` —
"Suite-level token pin in `tests/conftest.py` — autouse sentinel for
`GITHUB_TOKEN`/`RAILWAY_TOKEN`, kills the unpinned-reason-assertion flake
class", `docs/ideas/backlog.md:33@31b5d00`). The protection against the
both-rungs bug #250 flagged was per-test discipline since PR #251; this
session made it structural: a test's meaning can never again change with
whether the runner exports a token (this dev container proxy-injects a
`GITHUB_TOKEN`; CI may not).

## What was done

- `tests/conftest.py` (new) — one autouse function-scoped fixture,
  `_pin_ambient_tokens`: `setattr(config, "GITHUB_TOKEN", "")` +
  `setattr(config, "RAILWAY_TOKEN", "")` pin the import-time snapshot;
  `delenv` on both names pins call-time env reads (`app/writeback.py`
  reads `GITHUB_TOKEN` per attempt). Deliberately a **private
  `pytest.MonkeyPatch()` instance**, not the shared function `monkeypatch`
  fixture: `test_env_parse_hardening.test_import_survives_hostile_env`
  calls `monkeypatch.undo()` mid-test, which would otherwise strip the
  suite pin with the test's own patches. Test-level patches apply after
  setup, so rung-specific tests keep opting in exactly as before and win.
- Pinned state = the **unset rung** (not a non-empty sentinel) because it
  matches CI, matches the documented production default for
  `RAILWAY_TOKEN`, and is what every existing not-configured assertion
  already expects.
- Scope check across the other three suites: botsite/dashboard reference
  neither token in code or tests; review's only runtime read
  (`review/gen_questions.py`) is stubbed at the `fetch_issues` seam in its
  tests — the flake class lives in `tests/` only, so the pin does too.
- Proven to bite: a throwaway probe file run with both tokens exported
  confirmed the pin active in-test, test-level overrides winning, and the
  pin restored after an overriding test (8 passed, probe deleted).
- `docs/ideas/backlog.md` — the source bullet flipped `captured` → `built`
  (PR #309).
- Verified BOTH ways, identical results: `GITHUB_TOKEN="dummy-pin-test"
  RAILWAY_TOKEN="dummy-pin-test" python3 -m pytest tests/ botsite/tests
  dashboard/tests review/tests -q` — 1342 passed, 1 warning; `env -u
  GITHUB_TOKEN -u RAILWAY_TOKEN python3 -m pytest …` — 1342 passed,
  1 warning; `python3 bootstrap.py check --strict` — green except this
  card's own designed born-red HOLD (flipped by this commit) and the
  pre-existing never-exit-affecting `owner-action-fields` advisory on
  control/status.md (not owned here).
- Decisions made: unset-rung sentinel over a non-empty one; private
  MonkeyPatch instance over the shared fixture; `tests/`-only scope with
  the other suites' token-freeness verified rather than pinned blindly.
- Next session should know: the pin covers `GITHUB_TOKEN`/`RAILWAY_TOKEN`
  only — any NEW ambient env read added to app/ (or a test asserting on
  `SITE_PASSWORD`/`ANTHROPIC_API_KEY` state without pinning) re-opens the
  same class for that variable; see this card's 💡 for the structural
  answer.

⚑ Self-initiated: no — dispatched ORDER 027 item 5 (`[improve]`), building
the 💡 left by `.sessions/2026-07-13-tighten-ladder-pins.md` (PR #251).

## 💡 Session idea

**Suite-pin completeness gate — derive the ambient-env reads that shape
request-time behavior and assert conftest coverage** — the new pin covers
exactly two variables, but the CLASS is "any env var whose ambient value
changes what an unpinned test exercises": `config.SITE_PASSWORD` (503
fail-closed vs authed rungs) and `owner_assist.ENV_API_KEY` sit one
unpinned assertion away from the same both-rungs flake. The
`tests/test_env_poison_pin.py` AST sweep already derives every env-var
NAME the services read; a sibling pin could assert that each app/-read
name is either pinned in `tests/conftest.py` or on a justified per-entry
allowlist ("tests always set it explicitly"), failing BY NAME when a new
ambient read lands unpinned. Worth having because this session's fix is
enumerated, not derived — the next env-dependent feature reintroduces the
flake class for a variable the conftest has never heard of. Deduped
against `docs/ideas/backlog.md`: the poison-pin bullet covers
import-survival poisoning (a different failure class), the token bullets
cover PAGE behavior; nothing gates conftest pin completeness.

## ⟲ Previous-session review

The venture-vetting-catalog session (PR #248) did well — it curated all 22
vetting packets into honest status groups with nothing invented, and its
`test_committed_registry_is_honest` pin (unique slugs, the 1/12/2/7
breakdown, every source @ `2c039e3`) means the registry can't drift
silently in-repo; what it missed: the honesty is frozen at that upstream
sha — its own sha-drift-pin idea is still only a backlog bullet, so the
catalog decays invisibly as venture-lab moves. Workflow improvement: when
a session's core risk is named in its own 💡, the dispatcher should treat
that bullet as the default follow-up slice instead of letting it age in
the backlog.
