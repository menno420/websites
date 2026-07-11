# 2026-07-11 — kit upgrade v1.9.0 → v1.10.0

> **Status:** `complete` — PR #105 (`claude/kit-upgrade-v1.10.0`), merged on
> `quality` green.

- **📊 Model:** claude-fable-5 · distribution worker · kit upgrade (fleet-wide v1.10.0 wave)

**What this session was about:** Fleet-wide substrate-kit v1.10.0 distribution
wave (rung: order — coordinator-directed upgrade, same lane as the v1.8.0 #85
and v1.9.0 #101 upgrades). Payload (kit #176): `session-card-hold` locked door
on PR-added in-progress cards (never allowlistable, engages on card-only diffs
— the superbot-games #40 class), `check --simulate-added-card`, `upgrade
--apply-docs` carve-out re-emission fix (the v1.9.0 regression found on THIS
repo, #101), retroactive model-doctrine append to planted `.sessions/README.md`.

## What was done

- Asset sha256-verified before staging: `bootstrap.py` v1.10.0 =
  `ba69fc5cf21619cc85e4c733ebe3d9eda8803e678f810fcc39b94d60c2f3b5a4`
  (matches release.json `sha256` and the wave's 3-way-verified value).
- Canonical recipe: staged `bootstrap.py.new` + `release.json` in repo root →
  `python3 bootstrap.py.new upgrade --apply-docs` (engine self-verified,
  self-cleaned inputs). Tree: `bootstrap.py` KIT_VERSION `1.9.0` → `1.10.0`;
  `.substrate/state.json` + `substrate.config.json` kit_version `1.10.0`.
- Exactly ONE new backup banked: `.substrate/backup/bootstrap-1.9.0.py`
  (sha256 `55181082…` — byte-identical to the pre-upgrade dist); all six
  pre-existing banks byte-identical before/after.
- Staged gate regen (`.substrate/ci/substrate-gate.yml`) carries the
  added-card born-red HOLD lane + `--simulate-added-card` on gate-touching
  PRs; `session-card-hold` finding implemented in the vendored engine
  (appended after the allowlist pass — never allowlistable).
- `.sessions/README.md`: retroactive model-doctrine APPEND fired here
  (provenance marker `<!-- substrate-kit: model-attribution doctrine … -->`,
  pure 3-line append, all 62 host lines preserved byte-for-byte). Note: the
  hand-merged #101 doctrine already said the same thing but with bold markers
  inside the detection phrase, so the idempotence match missed it → kit-lane
  idea captured below.
- Carve-out section SURVIVED `--apply-docs` on the same invocation (the
  v1.9.0 hand-restore is no longer needed): `.substrate/upgrade-report.md`
  ends with "## Carve-out scan / carve-out scan: ran — no kit-owned live
  workflow installed, nothing to scan." — kit #176 fix verified live on the
  repo that found the bug. Backlog bullet flipped `captured → retired`.
- `automerge.required_context` still `"quality"` after the upgrade (the #101
  fix preserved). Exact-pin test bumped: `tests/test_born_red_session_gate.py`
  `kit_version == "1.10.0"`.
- First-exercise data point: the born-red hold ENGAGED live in websites CI —
  `quality` run 29144058192 red with the `HOLD (by design)` banner +
  `##[notice]` annotation on this card while in-progress (the folded
  diff-aware `--session-log` lane; the live quality.yml predates the
  `--added-card` lane, so the hold rides `--require-session-log`, not the
  `session-card-hold` finding).
- Sibling-card scan (mtime-lottery guard): every card in `.sessions/` graded
  `check --strict --session-log <card>` exit 0 — no grammar backfills needed;
  the only red was this card's own designed hold.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests -q` —
  225 passed; `python3 bootstrap.py check --strict` — exit 0 once this card
  flipped complete (HOLD-by-design while in-progress, as designed);
  `check --simulate-added-card <this card>` — "would HOLD (born-red …)",
  advisory-only, exit 0.

⚑ Self-initiated: no — coordinator-directed distribution order (Q-0261.3
wave). In-passing: backlog bullet state flip (apply-docs bug → `retired`,
fixed upstream) + one new kit-lane idea, both kit-upgrade-adjacent.

## 💡 Session idea

**Model-doctrine idempotence phrase-match should be emphasis-insensitive** —
`_merge_model_doctrine` detects an already-present doctrine by exact
substring, so websites' hand-merged copy (bold markers mid-sentence) was
missed and a near-duplicate paragraph appended. Worth having because every
adopter that hand-merged the doctrine before the retroactive pass gets the
same duplicate noise; normalizing `*`/`_` before matching kills the class.
Deduped against `docs/ideas/backlog.md` + NEXT list: no prior entry.
Captured in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

The lane-source-registry session (#102) was exemplary — cron run 2's failure
was investigated to root cause with verbatim live evidence in the PR body,
and its "flip-after-open keeps paying" note proved out again here. Missed:
its close-out left `control/status.md` `kit:` line reading v1.9.0-era state
only one heartbeat deep — after THIS merge the `kit: v1.9.0` line is stale
again (lane-owed; distribution workers never write `control/`). Workflow
improvement: the heartbeat kit-line could be derived from
`substrate.config.json` at status-write time instead of hand-typed, removing
the whole stale-kit-line class.
