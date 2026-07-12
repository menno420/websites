# 2026-07-12 — substrate-kit upgrade v1.14.0 → v1.15.0 (distribution)

> **Status:** `complete` — branch `claude/kit-upgrade-v1.15.0`, PR #199.

- **📊 Model:** fable-5 · distribution worker · kit-upgrade

**What this session was about:** distribute substrate-kit v1.15.0 to this repo —
verify the release asset (sha256 three-way), run the two-command upgrade flow,
record carve-outs, bump the exact-pin kit-version test, verify all four service
suites + the strict kit gate. Distribution-only: no lane work, no control/inbox
or control/status edits.

## What was done

- Verified release asset three-way: sha256
  `25d22af9d9d81b2a7dc6d8d500234b6aa0f3f1c6a0400284ce2381baaeac650e`
  (828,825 bytes) = release.json `sha256` = kit dist @ `eaf4f23` (tag v1.15.0).
- Ran `python3 bootstrap.py.new upgrade` then
  `python3 bootstrap.py upgrade --apply-docs`; `bootstrap.py` now v1.15.0,
  1.14.0 banked at `.substrate/backup/bootstrap-1.14.0.py` (byte-verified),
  pre-existing banks untouched.
- Planted `docs/ROUTINES.md` + `docs/seat-digest.md`; applied `docs/SKILLS.md`
  (template-improved).
- Cleared the `[reachable] ROUTINES.md` orphan red by hand-merging ONLY the
  minimal wiring hunk from the report's template delta into the diverged
  `docs/AGENT_ORIENTATION.md` (planted-doc list + trigger-route paragraph).
- Enabler regen carve-out acted on per the tool's instruction: kit-owned
  `.github/workflows/auto-merge-enabler.yml` regenerated; host jobs
  (`arm-on-open`, `sweep`) moved verbatim to
  `.github/workflows/host-automerge-extras.yml` (pre-regen bank `c43c1c30`).
- Bumped the exact kit-version pin in `tests/test_born_red_session_gate.py`
  to `1.15.0`.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — 658 passed, 1 warning; `python3 bootstrap.py check
  --strict` — green apart from this card's designed born-red hold and the
  pre-existing lane-owed `owner-action-fields` advisory.
- Lane-owed (recorded in PR #199, not done here): heartbeat `kit:` bump,
  4 remaining diverged-doc manual merges, CAPABILITIES.md seed-fence
  hand-adopt-once, kit-enabler vs host-extras reconciliation.

⚑ Self-initiated: no — coordinator-assigned fleet-wide v1.15.0 distribution.
The host-extras workflow split was tool-instructed by the upgrade itself
("commit that before shipping this upgrade/adopt PR"), carried verbatim from
the bank — contained and reversible (delete the file to undo).

## 💡 Session idea

**Upgrade-report machine-readable carve-out block** — have `bootstrap.py
upgrade` also emit the carve-out list as JSON (`.substrate/upgrade-report.json`)
so distribution workers and the fleet registry can diff carve-outs across
releases mechanically instead of parsing the markdown report. Worth having
because the carve-out list is the load-bearing artifact every upgrade PR body
copies verbatim, and a schema'd copy removes the transcription step entirely.
Deduped against `docs/ideas/backlog.md` (no upgrade-report entry there) — kit-repo
idea, routed via this card since distribution sessions don't write the kit backlog.

## ⟲ Previous-session review

The previous session (2026-07-12 verify/stand-down) left an accurate
current-state pointer and a clean anchor, which made this upgrade's preflight
trivial; what it missed doesn't affect this lane — nothing to flag beyond its
own already-recorded "check merged PRs at boot" idea.
