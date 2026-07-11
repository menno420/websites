# 2026-07-11 — kit upgrade v1.10.1 → v1.11.0

> **Status:** `complete` — PR #129 (`claude/kit-upgrade-v1.11.0`), merged on
> `quality` green.

- **📊 Model:** claude-fable-5 · distribution worker · kit upgrade (fleet-wide v1.11.0 wave)

**What this session was about:** Fleet-wide substrate-kit v1.11.0 distribution
wave (rung: order — coordinator-directed upgrade, Q-0261.3 lane, same as the
v1.10.1 #113 / v1.10.0 #105 / v1.9.0 #101 upgrades). Payload: HANDOFF
composer (boot-generated `HANDOFF.md` orientation trail), planted CLAUDE.md
template's HANDOFF read-first line, staged-gate action pins
(checkout@v5 / setup-python@v6), guard-fires 10-minute dedupe.

## What was done

- Asset sha256-verified before staging: `bootstrap.py` v1.11.0 =
  `c339bd6a2eb3a139dd0106d5fd3873eb2d067f79723fccb5781d4e72a74a8d29`
  (673,937 bytes; == release.json `sha256`; pre-upgrade dist confirmed the
  expected v1.10.1 `fbe83ce3…` first).
- Canonical recipe: staged `bootstrap.py.new` + `release.json` in repo root →
  `python3 bootstrap.py.new upgrade` (engine self-verified, self-cleaned
  inputs). `substrate.config.json` + `.substrate/state.json` kit_version
  `1.11.0`.
- HANDOFF payload verified: staged `.substrate/claude/CLAUDE.md` gains the
  read-first `HANDOFF.md` orientation line (item 2); live `.claude/CLAUDE.md`
  untouched (not in the diff). Composer in the vendored dist (28 `HANDOFF`
  hits; pointer constants `HANDOFF_POINTER_FILENAME` / `_POINTER_MARKER` /
  `_EXCERPT_CAP` / `_NEEDLE`). `HANDOFF.md` is boot-generated + untracked,
  NOT gitignored (`git check-ignore HANDOFF.md` exits 1) — none committed.
- Exactly ONE new backup banked: `.substrate/backup/bootstrap-1.10.1.py`
  (sha256 `fbe83ce3…` — byte-identical to the pre-upgrade dist); all eight
  pre-existing banks byte-identical before/after.
- Staged gate regen (`.substrate/ci/substrate-gate.yml`): `actions/checkout@v5`
  + `actions/setup-python@v6`.
- guard-fires 10-min dedupe verified live: two back-to-back
  `check --strict` runs — first wrote 1 fire to `.substrate/guard-fires.jsonl`,
  second appended 0 duplicates.
- Carve-out section present in `.substrate/upgrade-report.md`: "carve-out
  scan: ran — no kit-owned live workflow installed, nothing to scan"
  (expected — websites' born-red hold rides the folded `quality` lane).
- `.sessions/README.md` byte-identical across the upgrade (sha256
  `ec29b1a1…` before == after) — the v1.10.1 emphasis-blind doctrine check
  holds; no near-duplicate append.
- Exact-pin test bumped: `tests/test_born_red_session_gate.py`
  `kit_version == "1.11.0"` (+ chain line in the docstring).
  `docs/current-state.md` kit lines updated (v1.11.0, #129 appended to the
  stepwise chain).
- NOT done here (lane-owed, one-writer rule): `control/status.md` `kit:`
  heartbeat line still says v1.10.1 — the heartbeat lane bumps it.
- Verified: `python3 -m pytest tests/ -q` — 187 passed;
  `botsite/tests dashboard/tests` — 58 passed (245 total);
  `python3 bootstrap.py check --strict` — exit 0 once this card flipped
  complete (HOLD-by-design while in-progress, as designed).

⚑ Self-initiated: no — coordinator-directed distribution order (Q-0261.3
v1.11.0 wave). In-passing: current-state kit-line bump + backlog idea
capture — kit-upgrade-adjacent, per #113 precedent.

## 💡 Session idea

**Apply the HANDOFF read-first line to the live `.claude/CLAUDE.md` via
`upgrade --apply-docs`** — the v1.11.0 upgrade report classes the live
working agreement as "consumer-untouched + template improved — safe to
apply", so one flag-run adopts the staged orientation change (read
`HANDOFF.md` before re-deriving history) into the file agents actually
boot from. Worth having because the HANDOFF composer only pays off once
sessions are *told* to read `HANDOFF.md` — today the live orientation list
still routes agents straight to `current-state.md`. Deduped against
`docs/ideas/backlog.md` + the queue-state NEXT list: no prior entry.
Captured in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

The quality-every-card-gate port (#120) did well: it promoted the #113
session idea to the live lane the same day, closing the `tail -1`
multi-card shadowing before any PR exploited it — this session's born-red
card is graded by that very loop. Missed: team memory outside the repo
(the distribution lane's briefing) still described quality.yml as
`tail -1`-shaped; a one-line "live lane now every-card (#120)" note in
`docs/current-state.md`'s kit passage would keep cross-repo briefings from
going stale.
