# 2026-07-11 — substrate-kit upgrade v1.8.0 → v1.9.0 (§4.3 release flow)

> **Status:** `complete` — upgrade applied, gates green, shipped as PR #101.

- **📊 Model:** Claude Fable 5 · coordinator-tasked distribution worker · kit-upgrade

**What this session was about:** take the vendored `bootstrap.py` from kit
v1.8.0 (PR #85) to the released **v1.9.0** (kit tag `v1.9.0` → `2a779b5`,
release run 29139623697) through the kit's own §4.3 consumer upgrade flow,
as one kit-scoped PR — order rung: coordinator-directed distribution wave
(owner directive Q-0261.3), mirroring the superbot-next upgrade (its PR
#150) earlier this wave.

Scope note (distribution directive): kit-owned files only — `control/inbox.md`
and `control/status.md` untouched by this session; the lane's own next
heartbeat records the new `kit:` line.

## What was done

- **§4.3 upgrade:** verified assets staged as `bootstrap.py.new` +
  `release.json` (sha256 `55181082c796657c8e5e14750d248cea2df9e69a9aa896dd
  8a8c7f1adfb9cc90` verified by hand AND in-flow — engine printed
  `verified: sha256 + version against release.json`); `python3
  bootstrap.py.new upgrade` → 1.8.0 → 1.9.0, inputs self-cleaned.
- **Backup verified:** exactly ONE new archive `.substrate/backup/
  bootstrap-1.8.0.py` (sha256 `28c5dcb6…` — byte-equal to the pre-upgrade
  dist); all five pre-existing banks byte-identical before/after.
- **v1.9.0 plants:** `.ignore` + `.gitattributes` fresh-planted (2
  search-hygiene entries each under the append-only provenance marker);
  staged gate regen under `.substrate/ci/` (this repo has no live kit-owned
  workflow by design — gate folded into required `quality.yml`).
- **First exercises captured:** (1) plant-time `automerge.required_context`
  validation (kit #168) FIRED, naming the real contexts
  (`'substrate-gate' matches no job … contexts found: 'healthcheck',
  'quality'`) — per its prescription, `substrate.config.json` →
  `automerge.required_context` set to `quality` (the repo's actual required
  check; closes the v1.8.0 session's flagged mismatch). (2) The born-red
  `check: HOLD (by design)` notice fired locally AND in the live `quality`
  gate (run 29140551971), incl. a `##[notice]` Actions annotation.
- **`upgrade --apply-docs`:** took the one template-improved,
  consumer-untouched doc (`.claude/CLAUDE.md`, new "Kit machinery — search
  hygiene" section). KIT BUG found: the apply pass rewrote
  `.substrate/upgrade-report.md` WITHOUT the carve-out section the main
  pass wrote — hand-restored verbatim with a provenance comment; flagged to
  the kit lane via `docs/ideas/backlog.md`.
- **`.sessions/README.md` kept** (genuine host content, correctly not
  regenerated); the v1.9.0 model-attribution ground-truth clauses
  (self-report is attribution ground truth; never copy from external
  surfaces) merged by hand into the ender checklist.
- **Pins + tests:** exact-pin test consciously moved 1.8.0 → 1.9.0
  (`tests/test_born_red_session_gate.py::test_config_names_kit_v1`);
  `bootstrap.py --version` → `substrate-kit 1.9.0`.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests -q` —
  **224 passed**; `python3 bootstrap.py check --strict` — red only on this
  card's own designed born-red hold, green on flip; Railway-ID guard green.

⚑ Self-initiated: no — coordinator-tasked distribution work; the
`required_context` fix was prescribed by the kit's own plant-time advisory
(decide-and-flag, one line, reversible).

## 💡 Session idea

**Kit fix: `upgrade --apply-docs` must preserve the carve-out section when
it rewrites the upgrade report** — the post-hoc apply pass regenerates
`.substrate/upgrade-report.md` with only the docs table + Applied section,
silently dropping the #156-mandated carve-out audit record. Worth having
because every adopter that takes apply-docs post-hoc loses the shipped
record of what the carve-out scan found — the exact audit trail #156
existed to make explicit. Deduped against `docs/ideas/backlog.md` + NEXT:
no prior mention. Captured in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

The v1.8.0 upgrade session (PR #85) flagged the `required_context:
substrate-gate` ≠ `quality` mismatch as its session idea but only recorded
it in its card, not in `docs/ideas/backlog.md` — it aged invisibly until
the kit's new advisory re-surfaced it this session (now fixed). Improvement
it points at: a card-only 💡 is a leak; the ender checklist's "captured in
backlog.md" line is there for exactly this reason — this session wrote the
bullet.
