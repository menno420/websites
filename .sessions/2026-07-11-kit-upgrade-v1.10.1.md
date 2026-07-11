# 2026-07-11 — kit upgrade v1.10.0 → v1.10.1

> **Status:** `complete` — PR #113 (`claude/kit-upgrade-v1.10.1`), merged on
> `quality` green.

- **📊 Model:** claude-fable-5 · distribution worker · kit upgrade (fleet-wide v1.10.1 wave)

**What this session was about:** Fleet-wide substrate-kit v1.10.1 distribution
wave (rung: order — coordinator-directed upgrade, Q-0261.3 lane, same as the
v1.9.0 #101 and v1.10.0 #105 upgrades). Patch payload (kit #187): session-gate
`tail -1` multi-card shadowing fix (every card in a PR's session-card diff is
graded; added in-progress → HOLD; modified siblings advisory), and the
`_MODEL_DOCTRINE_PHRASE` emphasis-blind presence check — the near-duplicate
doctrine append found on THIS repo (#105 session idea) is the fix's origin.

## What was done

- Asset sha256-verified before staging: `bootstrap.py` v1.10.1 =
  `fbe83ce35d1fb3b544ac58fc60ee2609eaa6c69c13d77883e9fdc5da6bbad158`
  (3-way verified: release.json `sha256` == bootstrap.py.sha256 asset ==
  local sha256; pre-upgrade dist confirmed the expected v1.10.0
  `ba69fc5c…` first).
- Canonical recipe: staged `bootstrap.py.new` + `release.json` in repo root →
  `python3 bootstrap.py.new upgrade` (engine self-verified, self-cleaned
  inputs). Tree: `bootstrap.py` KIT_VERSION `1.10.0` → `1.10.1`;
  `.substrate/state.json` + `substrate.config.json` kit_version `1.10.1`.
- Exactly ONE new backup banked: `.substrate/backup/bootstrap-1.10.0.py`
  (sha256 `ba69fc5c…` — byte-identical to the pre-upgrade dist); all seven
  pre-existing banks byte-identical before/after.
- Staged gate regen (`.substrate/ci/substrate-gate.yml`) carries the
  multi-card grading: every ADDED card graded per-card (in-progress → HOLD;
  any holding card holds the whole step), modified siblings advisory-only,
  modified-only diffs through the locked door per card, gate-touching PRs
  keep the full locked door + `--simulate-added-card` per added card.
- **Emphasis-blind doctrine check verified live on the repo that found the
  bug:** `.sessions/README.md` byte-identical across the upgrade (sha256
  `ec29b1a1…` before == after) — the hand-merged bold-marker doctrine is now
  recognized as present, NO new near-duplicate append. The existing #105-era
  appended block remains in place (the upgrade refrains from re-appending;
  it does not retro-deduplicate). Backlog bullet flipped
  `captured → retired`.
- Carve-out section present in `.substrate/upgrade-report.md`: "carve-out
  scan: ran — no kit-owned live workflow installed, nothing to scan"
  (expected — websites has no live substrate-gate.yml by design; the
  born-red hold rides the folded diff-aware `quality` lane).
- Exact-pin test bumped: `tests/test_born_red_session_gate.py`
  `kit_version == "1.10.1"`. `docs/current-state.md` kit lines updated
  (v1.10.1, #113 appended to the stepwise chain).
- Sibling-card scan (mtime-lottery guard): every other card in `.sessions/`
  graded `check --strict --session-log <card>` exit 0 — no backfills needed;
  the only red was this card's own designed hold.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests -q` —
  235 passed; `python3 bootstrap.py check --strict` — exit 0 once this card
  flipped complete (HOLD-by-design while in-progress, as designed);
  `check --simulate-added-card <this card>` — "would HOLD (born-red …)",
  advisory-only, exit 0.

⚑ Self-initiated: no — coordinator-directed distribution order (Q-0261.3
v1.10.1 wave). In-passing: backlog bullet state flip (emphasis-insensitive
doctrine match → `retired`, fixed upstream in #187) — kit-upgrade-adjacent.

## 💡 Session idea

**Live `quality.yml` still uses the `tail -1` single-card picker** — the
folded diff-aware lane in `.github/workflows/quality.yml` derives the PR's
card with `… | tail -1`, the exact multi-card shadowing shape v1.10.1 fixed
in the staged gate; a PR adding this born-red card AND modifying a
later-sorting sibling would grade only the sibling and ship the in-progress
card green. Worth having because the staged-gate fix doesn't protect
websites until the host-owned folded lane adopts the same every-card loop.
Deduped against `docs/ideas/backlog.md` + the queue-state NEXT list: no
prior entry. Captured in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

The rung-5 truth sweep (#111) did well: it caught the kit version stated as
v1.6.0 in `current-state.md` and fixed a time-bomb test rather than
deferring it. Missed: the same sweep left the `control/status.md` line-4
health text pinned to a specific main HEAD (`ddbbf27`) that staled within
hours — deriving heartbeat facts (HEAD, kit version) at write time from
`git`/`substrate.config.json` instead of hand-typing them would retire that
drift class.
