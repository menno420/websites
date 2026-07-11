# 2026-07-11 — substrate-kit upgrade v1.7.1 → v1.8.0 (§4.3 release flow)

> **Status:** `in-progress` — applying the v1.8.0 release upgrade as one kit-scoped PR.

- **📊 Model:** claude-fable-5 (coordinator-tasked distribution worker)

**What this session is about:** take the vendored `bootstrap.py` from kit
v1.7.1 (PR #74) to the released **v1.8.0** through the kit's own §4.3
consumer upgrade flow, as one kit-scoped PR (mirror of the superbot-next
upgrade earlier this session).

Scope note (distribution directive): kit-owned files only — `control/inbox.md`
and `control/status.md` untouched by this session; the lane's own next
heartbeat records the new `kit:` line.

## What was done

- **§4.3 upgrade:** both release assets placed next to the vendored copy
  (`release.json` beside `bootstrap.py.new` so the in-flow sha check engages),
  sha256 `28c5dcb64b713dde8d64a513a9a1aa860b4a07bf17d832686f0009932dc89b9b`
  verified by hand AND in-flow against the pinned release (tag `v1.8.0` →
  `63c6b39`); `python3 bootstrap.py.new upgrade` → 1.7.1 → 1.8.0, inputs
  self-cleaned.
- **Backup verified:** exactly ONE new archive, `.substrate/backup/
  bootstrap-1.7.1.py` (the old v1.7.1 dist), no collision lines in the
  report — the #156 hash-verified banking behaved as designed.
- **v1.8.0 payload landed:** `control/claims/README.md` planted (unified
  work-claim convention, §6.4); `scripts/env-setup.sh` KEPT (host wrapper
  already existed — skip-if-exists honored, classed `diverged`/manual-review
  because it predates hash recording; reviewed, contract-conformant:
  always-exit-0, no secrets — no change needed); auto-merge enabler STAGED
  ONLY at `.substrate/ci/auto-merge-enabler.yml` (this repo has no live
  kit-owned workflow by design — the gate is folded into the required
  `quality.yml` — so no live install, correct).
- **Carve-out scan explicit-when-clean (#156 fix) verified:** the report
  carries `## Carve-out scan` → "carve-out scan: ran — no kit-owned live
  workflow installed, nothing to scan."
- **Manual merge (report-prescribed):** `control/README.md` classed
  `diverged`; applied the four template additions at the host anchors —
  the "Claiming work (not an ORDER)" claims section and three "Grammar
  source of truth" pointers — preserving all host edits (D-0028
  machine-readable-enrichment section untouched).
- **Pins + tests:** `kit_version` → 1.8.0 (recorded by the upgrade); the
  D-0019 exact-pin test consciously moved 1.7.1 → 1.8.0
  (`tests/test_born_red_session_gate.py`). `bootstrap.py --version` →
  `substrate-kit 1.8.0`. Full CI-mirror suite `pytest tests/ botsite/tests
  dashboard/tests -q`: **197 passed**. Railway-ID guard green.
  `check --strict`: all checks passed (before this card's own born-red hold).

## 💡 Session idea

`substrate.config.json` now carries the kit-written `automerge` block
(`branch_patterns: ["claude/*"]`, `required_context: substrate-gate`), but
this repo's actual required check is `quality`, not `substrate-gate` (the
gate is folded into `quality.yml` by design). Set
`automerge.required_context` to `quality` so that if the staged enabler is
ever wired live, its refuse-to-arm guard counts the real required context
instead of one that never reports here.

## ⟲ Previous-session review

The v1.7.1 upgrade session (PR #74) recorded the zero-new-backup expectation
and the staged-gate-only shape precisely, which made this session's
one-new-backup + staged-enabler verification a two-minute diff against a
written baseline instead of a rediscovery. What it could have done better:
its session idea (lift the kit's `--inbox-base` snippet into `quality.yml`)
still has no owner/lane pickup — concrete system improvement: session ideas
that name a target file should also name the lane expected to act, otherwise
they age silently in the card archive.

## ⚑ Flags

- Self-initiated: none — coordinator-tasked distribution work only.
- `control/status.md` `kit:` line intentionally NOT updated (hard scope);
  the lane's next heartbeat records `kit: v1.8.0 · check: green ·
  engaged: yes`.
- Kit-written `automerge.required_context: substrate-gate` mismatch with
  this repo's real required check `quality` — flagged above as the session
  idea; harmless while the enabler stays staged-only.
