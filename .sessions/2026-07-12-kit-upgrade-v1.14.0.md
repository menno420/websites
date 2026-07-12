# 2026-07-12 — kit upgrade v1.13.0 → v1.14.0

> **Status:** `complete` — PR #171 (`claude/kit-upgrade-v1.14.0`), lands by
> merge commit on `quality` green.

- **📊 Model:** Fable 5 · kit-upgrade

**What this session was about:** Fleet-wide substrate-kit v1.14.0 distribution
wave (rung: order — coordinator-directed upgrade, same lane as the v1.13.0
#164 / v1.12.1 #155 / v1.12.0 #146 upgrades). Payload: venue-scoped
capability ledger (kit-owned seed fence + posture decision rule) and the
owner-assist output standard (risk classes, structured choices, paste-ready
values).

## What was done

- Synced to origin/main `f27d4c6`; vendored `bootstrap.py` header confirmed
  v1.13.0 before starting; `control/claims/` held no conflicting claim.
- Asset sha256 three-way verified before staging: `bootstrap.py` v1.14.0 =
  `47c1b8b954be2f587d88f7ed5923870883deab88a8fa7fbf2bb755decc2ee581`
  (779,399 bytes; == release.json `sha256` == kit clone
  `dist/bootstrap.py`, release tag v1.14.0 = kit commit `2fabf3e`).
- Canonical recipe: staged `bootstrap.py.new` + `release.json` in repo root →
  `python3 bootstrap.py.new upgrade` (engine self-cleaned both inputs) →
  `python3 bootstrap.py upgrade --apply-docs` (mandatory second pass). All
  stamps now `1.14.0`.
- Exactly ONE new backup banked: `.substrate/backup/bootstrap-1.13.0.py`
  (sha256 `982b26…0959` — byte-for-byte match against the v1.13.0 release
  digest recorded on the #164 card; chain-of-custody habit now three links).
- **Carve-out scan — verbatim:** `- carve-out scan: ran — no kit-owned live
  workflow installed, nothing to scan.` (Same correct N/A form as #164.)
- **Doc classes:** consumer-edited: 12 · diverged: 5 · template-improved: 1 ·
  unchanged: 5. `--apply-docs` applied `docs/SKILLS.md` (template@new, hash
  re-recorded). The FIVE diverged docs (template deltas preserved verbatim in
  `.substrate/upgrade-report.md`, lane-owed manual merges, NOT failures):
  `CONSTITUTION.md`, `docs/collaboration-model.md`, `docs/question-router.md`,
  `docs/CAPABILITIES.md`, `control/README.md` — all five deltas are the
  v1.14.0 owner-assist standard + venue-scoped capability seed.
- **capability-seed outcome — verbatim:** `capability-seed:
  docs/CAPABILITIES.md carries no kit-owned seed fence and its seed section
  does not match the old template — hand-adopt once: replace your
  discovery-rule + Capabilities/Walls seed sections with the fenced block
  (BEGIN/END markers) from the new template, keeping your append log below
  it; afterwards upgrades refresh the fence automatically.` Left lane-owed
  per the playbook ("hand-adopt once" = never force in the distribution PR).
- `.claude/CLAUDE.md`: engine-classified `unchanged — template identical
  across versions` (expected possible template update did not materialize;
  engine classification is truth) — nothing applied, live file untouched.
- Exact-pin test bumped: `tests/test_born_red_session_gate.py`
  `kit_version == "1.14.0"` (+ chain line in the docstring). Repo-wide pin
  grep (`grep -rn "1\.13\.0" --exclude=bootstrap.py --exclude-dir=.substrate
  --exclude-dir=.git --exclude-dir=.sessions`) found only
  `docs/current-state.md`: live kit line bumped to v1.14.0 (#171 appended to
  the stepwise chain); the line-236 hit is a dated historical recap — left.
- Verified: `python3 -m pytest tests/ -q` — 213 passed (incl. the bumped
  pin); `python3 bootstrap.py check --strict` — sole red on the born-red
  head was the designed session-card hold (`HOLD (by design)`); no SKILLS.md
  `[reachable]` orphan this cycle (the #164 hand-merged wiring held). One
  NEW advisory (never exit-affecting): `[owner-action-risk-class]
  control/status.md: 2 ⚑ OWNER-ACTION block(s) carry no risk-class token` —
  lane-owed (control files are out of scope for a distribution session).

⚑ Self-initiated: no — coordinator-directed distribution order (v1.14.0
wave). In-passing: current-state kit-line bump, per #164/#155/#146
precedent (kit-upgrade-adjacent).

## 💡 Session idea

**Kit: ship a `bootstrap.py adopt-seed` command that performs the
capability-seed "hand-adopt once" splice mechanically.** This repo (and
every consumer whose `docs/CAPABILITIES.md` predates the fence) got the
same report instruction: replace the discovery-rule + seed sections with
the fenced block, keep the append log below. That is a deterministic splice
— the engine already has the new fenced block AND knows where the append
log starts — yet each repo's lane must hand-perform it identically, with
identical risk of dropping a local finding. One command turns a
five-repo-wave × manual-merge into five one-liners, and the fence then
self-refreshes forever after. Fleet-level (kit engine), so routed to the
coordinator via this card + run report rather than `docs/ideas/backlog.md`.

## ⟲ Previous-session review

The v1.13.0 upgrade session (#164) did well twice over: recording the banked
dist's sha256 on its card let this session verify `bootstrap-1.13.0.py`
byte-for-byte against an independent record (the chain-of-custody habit is
now three links and has paid off every time), and its hand-merged SKILLS.md
wiring held — this cycle's strict gate raised no `[reachable]` orphan, so
the manual merge it derived was durable, not a patch. What it could have
done better: its card gave doc-class *counts* but named only some of the
classified docs, so a reader had to open the archived report to know which
docs were lane-owed. Concrete workflow improvement, applied above: name
every diverged doc on the card itself — the card is the surface the lane
owner actually reads.
