# 2026-07-13 — tests: pin token state in the two ladder-adjacent reason tests (#250 follow-up)

> **Status:** `complete` — PR #251, branch `claude/tighten-ladder-pins`;
> the two pre-existing reason tests that passed on BOTH rungs of the
> degradation ladder now pin `config.GITHUB_TOKEN` and assert each rung's
> exact honest-reason wording; lands via the auto-merge enabler on green.

- **📊 Model:** Claude Fable 5 · worker · ORDER-022-item-2 slice (test tightening)

**What this session was about:** the 💡 note left by the classifier session
(`.sessions/2026-07-13-contents-listing-classifier.md`, PR #250): two
pre-existing degradation-ladder tests assert failure-reason text WITHOUT
pinning `config.GITHUB_TOKEN`, so the same test exercises DIFFERENT rungs of
the ladder (token-set → bare fetch reason, token-unset → composed
not-configured wording) depending on the runner's ambient environment — and
passes on BOTH, meaning neither rung's honest-reason wording is actually
pinned. The two flagged pins: `tests/test_prompts.py`
(`test_drift_unknown_when_listing_unavailable_never_false_green`) and
`tests/test_app.py` (`test_ideas_listing_error_surfaces`). Rung fired:
ORDER 022 item 2 ("actually well made" quality floor) — a dispatched
follow-up slice, not self-initiated.

## What was done

- `tests/test_prompts.py` — the drift-unknown test now pins
  `GITHUB_TOKEN="tok"` and asserts `out["reason"] ==
  "ConnectError: unreachable"` (was: substring `in`, which the token-unset
  composed text also satisfied). The token-unset rung of the same
  never-false-green intent is asserted distinctly by the new
  `test_drift_unavailable_token_unset_rung_never_false_green`: exact
  composed "GITHUB_TOKEN is not set on this service and the fleet-manager
  `projects/` listing failed (fetch: ConnectError: unreachable)" wording
  plus the no-false-green /prompts render.
- `tests/test_app.py` — `test_ideas_listing_error_surfaces` now pins
  `GITHUB_TOKEN="tok"` and asserts `out["listing_error"] == "rate limited"`
  (was: substring `in`); the token-unset rung was already pinned exactly by
  `test_ideas_listing_error_names_missing_token`.
- Proven to bite: flipping either pinned token state fails the
  exact-wording assertion with the other rung's text (3 simulated
  regressions, 3 failures, then reverted).
- Sweep of all four suites for other classify_listing / ladder-reason /
  token-dependent-wording tests: `tests/test_classify_listing.py`,
  `tests/test_projects.py`, `tests/test_reviews.py`, `tests/test_envhub.py`
  (GITHUB_TOKEN + RAILWAY_TOKEN), queue/environments tests in
  `tests/test_app.py`, `tests/test_owner_writeback.py` — every rung-specific
  assertion already pinned; the remaining reason assertions
  (fleet/journal/activity/prompts per-artifact) are token-independent
  wording. botsite/dashboard/review suites: zero token/classifier
  references. Test-only diff.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — 1090 passed, 1 warning (+1 over main's 1089);
  `python3 bootstrap.py check --strict` — green except this card's own
  designed born-red HOLD (flipped by this commit) and the pre-existing
  never-exit-affecting `owner-action-fields` advisory on control/status.md
  (not owned here).

⚑ Self-initiated: no (dispatched ORDER 022 item 2 follow-up slice from
PR #250's session idea).

## 💡 Session idea

**Suite-level token pin in `tests/conftest.py` — make ambient-env
independence structural, not per-test discipline** — there is no
`tests/conftest.py`; an autouse fixture there pinning
`config.GITHUB_TOKEN` (and `RAILWAY_TOKEN`) to a known sentinel for every
test would make the whole latent-flake class impossible: an unpinned test
could never again silently depend on whether the runner's environment
exports a token (this dev container proxy-injects one; CI may not), while
rung-specific tests keep monkeypatching explicitly exactly as they do now.
Worth having because this session's sweep shows the current protection is
per-test discipline — the next unpinned reason assertion reintroduces the
bug #250 flagged. Deduped against `docs/ideas/backlog.md` + the
queue-state NEXT list: token bullets there are all about PAGE behavior
when the token is unset; nothing covers suite-level env pinning. Captured
in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

The contents-listing-classifier session (PR #250) did well — it unified
four hand-rolled ladders behind one classifier with the 404 disposition as
an explicit parameter and left a precise, immediately-actionable 💡 naming
the exact two unpinned tests and the mechanism by which they pass on both
rungs; what it missed is that it was already editing both of those files
in the same PR and could have pinned them then instead of shipping the
flake note for a follow-up slice.
