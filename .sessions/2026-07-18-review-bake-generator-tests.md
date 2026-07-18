# 2026-07-18 — Review bake-generator unit tests (R6)

> **Status:** `in-progress` — branch `claude/review-bake-generator-tests`; new
> unit coverage for the review service's three untested bake generators
> (`review/gen_snapshot.py`, `review/gen_fleet.py`, `review/gen_stats.py`).
> Test-only: no generator, no `review/data/*.json`, no product code touched.
> Each new test feeds a known input fixture, drives the generator's own
> transform, and asserts the baked output's shape, keys, types, and derived
> values — modeled on the existing `test_gen_questions.py` (network-free,
> deterministic, seam-stubbed). Born red on purpose: this card holds until the
> tests land green and the flip releases it.

- **📊 Model:** [[fill: model · effort · task-class]]

**What this session is about:** the review service bakes committed JSON under
`review/data/` at build time so the network-free runtime container reads only
local files (the "never fake data" doctrine — see `gen_snapshot.py`'s module
docstring). Four generators feed that model. `gen_questions.py` already carries
a thorough unit suite (`review/tests/test_gen_questions.py`) that stubs its one
network seam and asserts the committed-file contract; the other three ship with
NO unit coverage of their transforms. A bad bake — a miscounted PR-day rollup, a
dropped registry entry, a mis-parsed Link-header PR total — could therefore ship
silently, caught by nothing. R6 closes that gap: focused, network-free unit
tests over each generator's real transform and output shape. Test-only — no
route, no template, no serialized payload, no env, no generator or data file
touched.

⚑ Self-initiated: no — coordinator-dispatched backlog slice (R6).

## Close-out

**Evidence:**

- [[fill: files touched this branch]]
- [[fill: git — branch, base commit, commit SHAs]]
- [[fill: verify — four-suite result + both bootstrap checks]]

**Judgment:**

- [[fill: decisions made]]
- [[fill: next session should know]]

## 💡 Session idea

[[fill: one genuine session idea]]

## ⟲ Previous-session review

[[fill: one-line review of the previous card]]
