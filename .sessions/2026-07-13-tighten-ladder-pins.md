# 2026-07-13 — tests: pin token state in the two ladder-adjacent reason tests (#250 follow-up)

> **Status:** `in-progress` — branch `claude/tighten-ladder-pins`; flips to `complete`
> + PR number as the deliberate LAST code step.

- **📊 Model:** Claude Fable 5 · worker · ORDER-022-item-2 slice (test tightening)

**What this session was about:** the 💡 note left by the classifier session
(`.sessions/2026-07-13-contents-listing-classifier.md`, PR #250): two
pre-existing degradation-ladder tests assert failure-reason text WITHOUT
pinning `config.GITHUB_TOKEN`, so the same test exercises DIFFERENT rungs of
the ladder (token-set → unavailable wording, token-unset → composed
not-configured wording) depending on the runner's ambient environment — and
passes on BOTH, meaning neither rung's honest-reason wording is actually
pinned. The two flagged pins: `tests/test_prompts.py` (~line 375, the drift
"unknown" reason test) and `tests/test_app.py` (~line 957, the ideas
`listing_error` test). This slice pins the token state explicitly in each
(per the suites' existing monkeypatch idiom) and asserts the specific
per-rung wording, splitting/parametrizing where the intent covers both
rungs. Rung fired: ORDER 022 item 2 ("actually well made" quality floor) —
a dispatched follow-up slice, not self-initiated.

## What was done

- (to be filled at flip)

⚑ Self-initiated: no (dispatched ORDER 022 item 2 follow-up slice from
PR #250's session idea).

## 💡 Session idea

- (to be filled at flip)

## ⟲ Previous-session review

- (to be filled at flip)
