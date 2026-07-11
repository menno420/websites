# 2026-07-11 — kit upgrade v1.11.0 → v1.12.0

> **Status:** `complete` — PR #146 (`claude/kit-upgrade-v1.12.0`), lands by
> merge commit on `quality` green.

- **📊 Model:** claude-fable-5 · distribution worker · kit upgrade (fleet-wide v1.12.0 wave)

**What this session was about:** Fleet-wide substrate-kit v1.12.0 distribution
wave (rung: order — coordinator-directed upgrade, Q-0261.3 lane, same as the
v1.11.0 #129 / v1.10.1 #113 / v1.10.0 #105 upgrades). Payload: substantive
auto-draft arrival (reflog commit-subject evidence + carried-forward
pointer), planted-orientation boot-set trim (CLAUDE.md / AGENT_ORIENTATION /
CONSTITUTION templates), untouched-auto-draft advisory in the bare strict
lane only, and the carve-out scanner three-way compare (kit #210 — first
live exercise this wave).

## What was done

- Synced to origin/main `ebef8bd` (unchanged since the wave briefing); all
  three tree stamps confirmed v1.11.0 before starting.
- Asset sha256-verified before staging: `bootstrap.py` v1.12.0 =
  `77c00b811429e1b526ccc7e0dcf597435c11048e16a67edba6050f516ad5e1f8`
  (689,586 bytes; == release.json `sha256`, own digest `617dca35…600`;
  pre-upgrade dist confirmed the expected v1.11.0 `c339bd6a…d29` first).
- Canonical recipe: staged `bootstrap.py.new` + `release.json` in repo root →
  `python3 bootstrap.py.new upgrade` (engine self-verified "sha256 + version
  against release.json", self-cleaned both inputs). All three stamps now
  `1.12.0` (bootstrap.py KIT_VERSION, `.substrate/state.json`,
  `substrate.config.json`).
- **Carve-out scan (three-way compare, first live exercise) — verbatim:**
  `- carve-out scan: ran — no kit-owned live workflow installed, nothing to
  scan.` Correct N/A form (websites' born-red hold rides the folded
  `quality` lane; no live substrate-gate by design). No phantom carve-outs,
  no pre-regen bank.
- Exactly ONE new backup banked: `.substrate/backup/bootstrap-1.11.0.py`
  (sha256 `c339bd6a…d29` — byte-identical to the pre-upgrade dist); all nine
  pre-existing banks byte-identical before/after (`sha256sum -c` OK).
- Boot-set trim applied to the live working agreement via
  `upgrade --apply-docs`: the report classes `.claude/CLAUDE.md` as
  "consumer-untouched + template improved — safe to apply" (git history
  agrees: last touch was the v1.9.0 upgrade itself). This executes the #129
  session idea (`docs/ideas/backlog.md`, now `built`). Diff-reviewed against
  the staged `.substrate/claude/CLAUDE.md` render before applying: the
  orientation list now reads working agreement → `HANDOFF.md` →
  `current-state.md`, with CAPABILITIES / AGENT_ORIENTATION routed on need.
- CONSTITUTION.md + docs/AGENT_ORIENTATION.md classed **diverged** (both the
  template and the doc moved) — NOT auto-applied; template deltas preserved
  in `.substrate/upgrade-report.md` § Template deltas for manual merge (see
  💡 below).
- Exact-pin test bumped: `tests/test_born_red_session_gate.py`
  `kit_version == "1.12.0"` (+ chain line in the docstring). Repo-wide grep
  found no other functional `1.11.0` pins outside `.substrate/` /
  historical session logs.
- `docs/current-state.md` kit lines updated (v1.12.0, #146 appended to the
  stepwise chain).
- NOT done here (hard scope Q-0261.3): `control/inbox.md` and
  `control/status.md` untouched — the `kit:` heartbeat bump is lane-owed.
- Verified: `python3 -m pytest tests/ -q` — 197 passed (incl. the bumped
  pin); `python3 bootstrap.py check --strict` — exit 0 once this card
  flipped complete (HOLD-by-design while in-progress, confirmed live on the
  born-red head 5b5f079: `[session-card-hold] … designed hold, not a
  defect`).

⚑ Self-initiated: no — coordinator-directed distribution order (Q-0261.3
v1.12.0 wave). In-passing: current-state kit-line bump + backlog idea state
flip (`captured` → `built`, the apply-docs idea this upgrade executed) —
kit-upgrade-adjacent, per #113/#129 precedent.

## 💡 Session idea

**Hand-merge the preserved boot-set-trim deltas into the two diverged
planted docs (CONSTITUTION.md, docs/AGENT_ORIENTATION.md).** The v1.12.0
upgrade could not auto-apply payload item 2 to them (both the template and
the docs moved), so the trim landed only in `.claude/CLAUDE.md`; the exact
diffs sit in `.substrate/upgrade-report.md` § Template deltas. A websites
session should apply them by hand and diff-review: AGENT_ORIENTATION still
carries the duplicate start-list + duplicate verify block the new template
deletes ("one list, one home"), and CONSTITUTION still enumerates the full
PL register the new template condenses to a cite-the-register pointer.
Worth having because the trim's premise — one boot list, one home — fails
while two of the three planted orientation docs contradict it. Deduped
against `docs/ideas/backlog.md` + this card: no prior entry (the built
apply-docs idea covered only the consumer-untouched file). Captured in
`docs/ideas/backlog.md`.

## ⟲ Previous-session review

The v1.11.0 upgrade session (#129) did well: its 💡 idea was captured
precisely enough to be executable in one flag-run — this session ran
`upgrade --apply-docs` against its exact classification quote and the
staged render diff matched its prediction. What it surfaced to improve:
the cross-repo wave briefing described websites' live `.claude/CLAUDE.md`
as "host-owned, hand-merged — the upgrade must not touch it", contradicting
#129's own report class ("consumer-untouched — safe to apply") that its
card had already recorded. Concrete workflow improvement: distribution
briefings should quote the adopter's latest upgrade-report doc classes
verbatim instead of characterizing planted-doc ownership from lane memory —
the report is machine truth, the memory drifted within one wave.
