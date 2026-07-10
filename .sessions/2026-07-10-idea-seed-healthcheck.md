# 2026-07-10 — overnight idea seed: scheduled healthcheck (gen-2 night prep, part 2)

> **Status:** `complete`

- **📊 Model:** claude-fable-5 · high · docs-only idea capture (single-push; the
  grand-review session, owner-directed seeding)

## Scope

Owner-directed backlog seeding for overnight/gen-2 sessions (queue-state's NEXT items
stay first — ORDER 005 before anything). One capture: turn tonight's manual liveness
probe (all three services 200/PASS at 01:02Z) into a standing Actions-cron verification.

## 💡 Session idea

(The capture IS this session's idea — filed as a first-class idea file per the seeding
directive.)

## ⟲ Previous-session review

The wind-down sessions (#46–#48) handed over honestly, flagging the liveness gap they
couldn't probe from a docs-only scope; the flag worked — it routed tonight's probe. The
improvement is exactly this seed: make the probe self-arming so no flag is needed.
