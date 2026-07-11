# 2026-07-11 — kit upgrade v1.12.0 → v1.12.1

> **Status:** `complete` — PR #155 (`claude/kit-upgrade-v1.12.1`), lands by
> merge commit on `quality` green.

- **📊 Model:** fable-5 · distribution worker · kit upgrade (fleet-wide v1.12.1 wave)

**What this session was about:** Fleet-wide substrate-kit v1.12.1 distribution
wave (rung: order — coordinator-directed upgrade, same lane as the v1.12.0
#146 / v1.11.0 #129 / v1.10.1 #113 upgrades). Payload: the substrate-gate
false-green fix.

## What was done

- Synced to origin/main `0545906`; both tree stamps confirmed v1.12.0 before
  starting (`substrate.config.json:47`, `bootstrap.py:90 KIT_VERSION`).
- Asset sha256-verified before staging: `bootstrap.py` v1.12.1 =
  `1055ca2cfd32a83e3dab7a978b05fbec2a82932a3375de0b1034f2519c16e4aa`
  (704,108 bytes; == release.json `sha256`).
- Canonical recipe: staged `bootstrap.py.new` + `release.json` in repo root →
  `python3 bootstrap.py.new upgrade` (engine self-cleaned both inputs). All
  three stamps now `1.12.1` (bootstrap.py KIT_VERSION,
  `.substrate/state.json`, `substrate.config.json`).
- **Carve-out scan — verbatim:** `- carve-out scan: ran — no kit-owned live
  workflow installed, nothing to scan.` Correct N/A form (websites' born-red
  hold rides the folded `quality` lane; no live substrate-gate by design).
  Only the staged `.substrate/ci/substrate-gate.yml` regenerated.
- Exactly ONE new backup banked: `.substrate/backup/bootstrap-1.12.0.py`
  (sha256 `77c00b81…5f8` — matches the v1.12.0 release digest #146 recorded).
- **No template deltas this release:** every planted doc classed
  consumer-edited/template-unchanged or identical — nothing to apply, nothing
  diverged. (Note: the fresh upgrade-report overwrote the v1.12.0 report that
  held the preserved boot-set-trim deltas; the backlog bullet now points at
  `git show 31cfd9f:.substrate/upgrade-report.md` instead.)
- Exact-pin test bumped: `tests/test_born_red_session_gate.py`
  `kit_version == "1.12.1"` (+ chain line in the docstring). Repo-wide grep
  (excluding bootstrap.py / `.substrate/` / historical cards) found no other
  functional `1.12.0` pins — the `control/status.md` `kit:` heartbeat line is
  lane-owed and left untouched (hard scope).
- `docs/current-state.md` kit lines updated (v1.12.1, #155 appended to the
  stepwise chain).
- Verified: `python3 -m pytest tests/ -q` — 202 passed (incl. the bumped
  pin); `python3 bootstrap.py check --strict` — sole red on the born-red head
  was the designed session-card hold (`HOLD (by design)`), green expected on
  this flip commit.

⚑ Self-initiated: no — coordinator-directed distribution order (v1.12.1
wave). In-passing: current-state kit-line bump + backlog pointer repair (the
overwritten Template-deltas section, see above) — kit-upgrade-adjacent, per
#113/#129/#146 precedent.

## 💡 Session idea

**Pin the current-state kit line to `substrate.config.json` with a test.**
The "vendored `bootstrap.py` is kit vX.Y.Z" line in `docs/current-state.md`
is hand-edited every upgrade and has drifted before (it said v1.6.0 until
2026-07-11 while the tree was five releases ahead); a small suite test that
extracts that version token and asserts it equals `substrate.config.json`
`kit_version` makes the drift impossible. Worth having because the ledger is
step 3 of the boot set — a wrong kit line there misleads every session that
reads it before the config. Deduped against `docs/ideas/backlog.md`: no
prior entry (the exact-pin test covers only the config, not the ledger).
Captured in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

The v1.12.0 upgrade session (#146) did well: its card recorded the release
digest of the dist it banked, which let this session verify the new
`bootstrap-1.12.0.py` bank byte-for-byte against an independent record. What
it missed: it left its preserved Template-deltas diffs only in
`.substrate/upgrade-report.md` — a file the very next upgrade overwrites by
design — so the backlog idea depending on them briefly pointed at deleted
content. Concrete workflow improvement: when a card/backlog entry depends on
upgrade-report content, cite it by git pin (`git show <merge-sha>:…`), never
by live path — applied to the bullet this session.
