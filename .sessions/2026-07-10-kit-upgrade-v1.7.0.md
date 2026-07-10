# 2026-07-10 — substrate-kit upgrade v1.6.0 → v1.7.0 (§4.3 release flow)

> **Status:** `complete` — upgrade applied, gates green, shipped as PR #62.

- **📊 Model:** claude-fable-5 (coordinator-tasked distribution-wave worker)

**What this session was about:** take the vendored `bootstrap.py` from kit
v1.6.0 (D-0026, PR #45) to the released **v1.7.0** through the kit's own §4.3
consumer upgrade flow, as one kit-scoped PR.

Scope note (wave directive Q-0261.3): kit-owned files only — `control/inbox.md`
and `control/status.md` untouched by this session; the lane's own next
heartbeat records the new `kit:` line.

## What was done

- **§4.3 upgrade:** both release assets downloaded next to the vendored copy
  (the v1.6.0 session's lesson — `release.json` beside `bootstrap.py.new` so
  the in-flow sha check engages), sha256
  `00f4f4cd39351b17389b9abab3be88fcb0c9f4dee9ad8f1639ad1fc67fdb5238` verified
  by hand AND in-flow against the pinned release (tag `93c7bdb`);
  `python3 bootstrap.py.new upgrade --apply-docs` → 1.6.0 → 1.7.0, old dist
  banked (`.substrate/backup/`, `last-upgrade.json` correct), inputs
  self-cleaned.
- **Report classification** (`.substrate/upgrade-report.md`): 15
  consumer-edited (kept) · 4 unchanged · **1 diverged** — `control/README.md`,
  whose additive template delta (the `adopt --lane` one-command note for
  shared repos) was hand-merged per the D-0026 precedent. `--apply-docs` had
  nothing to rewrite: every improved template this release was on a
  consumer-edited doc here.
- **Staged artifacts regenerated** (always-regenerate class), including the
  staged `.substrate/ci/substrate-gate.yml`. The LIVE gate logic folded into
  `.github/workflows/quality.yml` is untouched — at v1.7.0 the installed gate
  is still never-clobber (kit PR #130 kit-ownership ships in the NEXT
  release; expected, not chased).
- **Pins + tests:** `kit_version` → 1.7.0 (recorded by the upgrade); the
  D-0019 exact-pin test consciously moved 1.6.0 → 1.7.0
  (`tests/test_born_red_session_gate.py`). `bootstrap.py --version` →
  `substrate-kit 1.7.0`. Full suite `pytest tests/ botsite/tests
  dashboard/tests -q`: **143 passed**. `check --strict`: only this card's own
  born-red hold (cleared by this flip).
- **New in v1.7.0 for this repo** (all advisory/additive, no hard reds):
  inbox append-only checker (`--inbox-base`, CI opt-in), claim advisory,
  OWNER-ACTION↔CAPABILITIES xref advisory, `adopt --lane`, post-hoc
  `--apply-docs`.

## 💡 Session idea

`quality.yml` could pass the new v1.7.0 `--inbox-base` flag to
`bootstrap.py check` on pull_request events (write the merge-base copy of
`control/inbox.md` to a temp file first): the append-only + ORDER-grammar
checker is already vendored but dormant without it, and this repo's inbox IS
its order bus — one workflow step turns an existing invariant ("inbox is
append-only, manager-written") from convention into an enforced gate.

## ⟲ Previous-session review

The never-idle-work-ladder session (PR #61) closed the "what should an idle
wake do" gap cleanly — seeded backlog plus an explicit ladder in the Project
instructions, exactly the standing-orders shape the gen-2 lane needed. What it
left implicit is freshness: the ladder tells a wake what to do but not how to
notice its own inputs are stale (its seeded ideas will age). Concrete system
improvement: the ladder's first rung could be "re-read `docs/ideas/README.md`
and drop any idea already shipped" — a self-grooming step so the ladder never
dispenses stale work; cheap to add next time that file is touched.
