# 2026-07-15 — Reboot truing: EAP extension ack (ORDER 031) + state truing

> **Status:** `in-progress`

- **📊 Model:** Claude Fable · worker · reboot truing (control/status.md wholesale + docs/current-state.md)

**What this session is about:** first rebooted wake after the 2026-07-14
dormancy record. Provenance: **ORDER 031**, `control/inbox.md` @ commit
`3cac461` (2026-07-15T03:36:57Z): "the v3.6 reboot prompt IS that go";
done-when = seat acknowledges on its first rebooted wake. The order extends
the EAP through **2026-07-21** and supersedes the 2026-07-14 dormancy
orders. This branch is that acknowledgement — it trues the two state
surfaces to the order's reality:

- `control/status.md` — wholesale rewrite: phase ACTIVE (EAP extended per
  ORDER 031, acked this wake), current health (main `3cac461`, suite 1414,
  strict check pass), orders ledger 001-031, routine (failsafe cron +
  pacemaker), parked/open PRs and rescue branches, open ⚑ asks, next-2-tasks
  baton, kit `v1.17.0`.
- `docs/current-state.md` — trued to main `3cac461`: suite count, open PRs
  #342/#343, EAP extension, kit version; durable claims kept.

⚑ Self-initiated: no — ORDER 031 (`control/inbox.md` @ `3cac461`), done-when
= seat acknowledges on its first rebooted wake.

## Close-out (auto-drafted 2026-07-15 — edit, don't author)

<!-- substrate:auto-draft -->

**Evidence (auto-collected — verify, then keep or correct):**

- files touched this branch: `.sessions/2026-07-15-reboot-truing.md`,
  `control/claims/claude-reboot-truing-20260715.md` (first commit);
  `control/status.md`, `docs/current-state.md` (truing commit).
- git: branch `claude/reboot-truing-20260715`, based on `main` @ `3cac461`.
- verify: run `python3 -m pytest tests/ botsite/tests dashboard/tests review/tests -q (all four service suites); python3 bootstrap.py check --strict (kit gate)` and record the result → [[fill: verify result — the engine cannot execute commands]]

**Judgment (the half only the session knows — resolve every slot):**

- Decisions made: [[fill: decisions taken this session, or none]]
- Next session should know: [[fill: the handoff pointer — where to pick up]]

## 💡 Session idea

[[fill: one idea you genuinely believe in — never filler]]

## ⟲ Previous-session review

[[fill: one genuine remark on the previous session + one workflow improvement]]
