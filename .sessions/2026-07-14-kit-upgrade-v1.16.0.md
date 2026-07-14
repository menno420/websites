# 2026-07-14 — kit upgrade v1.15.0 → v1.16.0 (distribution wave)

> **Status:** `complete` — PR #338, branch `claude/kit-upgrade-v1.16.0`;
> flipped as the deliberate LAST code step.

- **📊 Model:** Claude Fable 5 · medium · mechanical refactor

**What this session was about:** substrate-kit v1.16.0 distribution wave —
upgrade this adopter's tree from v1.15.0 to v1.16.0 via the canonical
two-command recipe (verified release asset → `bootstrap.py.new upgrade` →
`bootstrap.py upgrade --apply-docs`), bump the exact-pin kit-version test,
verify strict + all four service suites. Order source: kit distribution wave
dispatch (coordinator-directed).

## What was done

- Release asset three-way sha256-verified (download == release.json ==
  expected `bba34e2102cbaf09394f39992f0501ea5cfd542d90301ef67e31a0854ca59170`,
  980,026 B), then the mandatory two commands: `python3 bootstrap.py.new
  upgrade` + `python3 bootstrap.py upgrade --apply-docs` (report carries the
  `## Applied (--apply-docs)` section: `docs/SKILLS.md`, `docs/ROUTINES.md`,
  `control/claims/README.md`). Exactly one new bank
  `.substrate/backup/bootstrap-1.15.0.py` (sha256 `25d22af9…650e` == the
  v1.15.0 asset); pre-existing banks untouched.
- New v1.16.0 plant `docs/reading-path.md` landed with three unfilled slots
  (strict-red `[unrendered-banner]` + `[reachable]` orphan). ⚑ Decided-and-
  flagged: answered `fleet_status_command` / `fleet_dark_repos` /
  `fleet_siblings` with grounded standing-doctrine values (fleet-manager
  generated `docs/roster.md` as the one-command orient; `pokemon-mod-lab`
  the sole private/dark repo per superbot Q-0272; sibling map from roster
  generation #48) + `render --live`, and wired a minimal reading-path
  pointer hunk into the diverged `docs/AGENT_ORIENTATION.md` (kept under the
  7000-word orientation budget — 6998/7000 after trim; the rest of the
  AGENT_ORIENTATION/CONSTITUTION/collaboration-model/CAPABILITIES template
  deltas stay lane-owed in `.substrate/upgrade-report.md`).
- Exact-pin test bumped 1.15.0 → 1.16.0
  (`tests/test_born_red_session_gate.py`, docstring + assert).
- Rails (Q-0261.3): `.github/workflows/**` (quality.yml,
  host-automerge-extras.yml, auto-merge-enabler.yml) untouched —
  enabler "kept (kit-owned, already current)"; `control/status.md`
  untouched (heartbeat `kit:` bump lane-owed); `.substrate/guard-fires.jsonl`
  gitignored here, not committed.
- Lane-owed (noted, not chased): capability-seed NOT refreshed (edited
  fence — standing websites hand-adopt-once); seat-digest NOT regenerated
  (hand-edited class); 4 diverged-doc template deltas in the upgrade report.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — 1414 passed; `python3 bootstrap.py check --strict` —
  green except this card's own designed in-progress hold (cleared by this
  flip).

⚑ Self-initiated: no — kit distribution wave dispatch (coordinator-directed).
⚑ Decide-and-flag: the three reading-path interview slots (two marked
user-lane) were answered by the wave worker from citable fleet doctrine to
clear the mandatory strict gate — reword freely, the render is one
`bootstrap.py answer` + `render --live` away.

## 💡 Session idea

**Truth-check `docs/reading-path.md` § sibling map against the fleet-manager
roster** — the new plant's fleet facts are frozen at interview-answer time
and will drift as lanes are added/retired; an advisory checker (or gen-style
refresh) comparing the map against the generated `fleet-manager
docs/roster.md` would flag drift. Worth having because a stale "who is who"
map misroutes every future cross-repo session, and this repo already owns
the roster-parse pattern (review/fleetdata cron). Deduped against
`docs/ideas/backlog.md` (the orientation-budget readout idea at ~L1585 and
the lanes.json roster-parse bullet are adjacent but distinct). Captured in
`docs/ideas/backlog.md`.

## ⟲ Previous-session review

The testing-import-valve session (PR #320) shipped the export valve's
missing half cleanly with honest legacy-field handling — well scoped; what
it missed is what most cards here miss: its `📊 Model:` effort/task-class
segments don't match the PL-004 taxonomy (now surfaced by v1.16.0's
model-line advisories on 10 cards) — worth a one-pass card sweep or a
template nudge so the PL-004 dataset stops recording verbatim off-taxonomy
segments.
