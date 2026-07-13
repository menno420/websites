# 2026-07-10 — substrate-kit upgrade v1.7.0 → v1.7.1 (§4.3 release flow)

> **Status:** `complete` — upgrade applied, gates green, shipped as PR #74.

- **📊 Model:** Claude Fable 5 (coordinator-tasked distribution-wave worker)

**What this session was about:** take the vendored `bootstrap.py` from kit
v1.7.0 (PR #62) to the released **v1.7.1** through the kit's own §4.3
consumer upgrade flow, as one kit-scoped PR (mirror of superbot-next #122).

Scope note (wave directive Q-0261.3): kit-owned files only — `control/inbox.md`
and `control/status.md` untouched by this session; the lane's own next
heartbeat records the new `kit:` line.

## What was done

- **§4.3 upgrade:** both release assets placed next to the vendored copy
  (`release.json` beside `bootstrap.py.new` so the in-flow sha check engages),
  sha256 `2aa4feddf7de7e20b00f46866826985ca8fd11f40bc51ebe261bbdef3118486d`
  verified by hand AND in-flow against the pinned release (tag `v1.7.1` →
  `1cbd666`); `python3 bootstrap.py.new upgrade` → 1.7.0 → 1.7.1, inputs
  self-cleaned.
- **Single-backup (#137) verified:** the old v1.7.0 dist was ALREADY banked
  byte-identically at `.substrate/backup/bootstrap-1.7.0.py` (the pre-#137
  v1.7.0 verb banked the new dist last upgrade), so the verb reported
  `already banked` and created NO new archive — in particular no spurious
  `bootstrap-1.7.1.py`. Backup sha256 `00f4f4cd…` == pre-upgrade vendored
  `bootstrap.py`.
- **Gate regen (new kit-owned class in v1.7.1):** staged
  `.substrate/ci/substrate-gate.yml` regenerated with `--inbox-base` wired
  (line 78: `check --strict --status-only --inbox-base "$basefile"`). This
  repo has NO live `.github/workflows/substrate-gate.yml` (the gate is folded
  into the required `quality.yml`), so live regen is N/A and no pre-regen
  bank exists — correct, not a failure. No carve-out section in the report
  (expected: none).
- **Report classification** (`.substrate/upgrade-report.md`): 16
  consumer-edited · 4 unchanged · 0 diverged · 0 template-improved — zero
  manual doc merges this release.
- **Pins + tests:** `kit_version` → 1.7.1 (recorded by the upgrade); the
  D-0019 exact-pin test consciously moved 1.7.0 → 1.7.1
  (`tests/test_born_red_session_gate.py`). `bootstrap.py --version` →
  `substrate-kit 1.7.1`. Full suite `pytest tests/ botsite/tests
  dashboard/tests -q`: **165 passed**. Railway-ID guard green.
  `check --strict`: only this card's own born-red hold (cleared by this flip).

## 💡 Session idea

The staged `.substrate/ci/substrate-gate.yml` now ships the exact
`--inbox-base` step this repo's PR #62 session idea asked for — instead of
hand-writing that step into `quality.yml`, lift the kit's generated
merge-base + `--inbox-base` snippet verbatim from the staged gate (lines
~70–80) into the folded `quality.yml` gate. Same one-step enforcement win,
but the wording stays kit-canonical, so future upgrades diff cleanly against
what the kit generates rather than a hand-rolled variant.

## ⟲ Previous-session review

The v1.7.0 upgrade session (PR #62) executed the same §4.3 flow cleanly and
its card recorded the one diverged doc and the hand-merge decision — that
record made this session's zero-diverged report instantly interpretable.
What it could have done better: it left the `--inbox-base` idea as prose
only, with no pointer to where the wiring would live; this session found the
kit now generates that wiring itself. Concrete system improvement: when a
session idea names a concrete file change, add the target file + anchor line
to the idea so the next session can act on it in one hop.

## ⚑ Flags

- Self-initiated: none — coordinator-tasked wave work only.
- `control/status.md` `kit:` line intentionally NOT updated (Q-0261.3 hard
  scope); the lane's next heartbeat records `kit: v1.7.1`.
