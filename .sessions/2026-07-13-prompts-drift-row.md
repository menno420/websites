# 2026-07-13 — /prompts: deployed-vs-canonical drift row (ORDER 022 item 3)

> **Status:** `in-progress` — branch `claude/prompts-drift-row`; flips to
> `complete` + PR number as the deliberate LAST code step.

- **📊 Model:** Claude Fable 5 · worker (order execution) · feature-build

**What this session was about:** ORDER 022 item 3 — /prompts
deployed-vs-canonical drift row. Add a per-seat drift row comparing the
canonical registry prompt vs the recorded deployed state, with an honest
"not recorded" where deployment isn't tracked. Rung: order — ORDER 022
item 3.

## What was done

- (in progress — claim + born-red card landed as the branch's first commit;
  implementation follows on this branch)
- Verified: pending — `python3 -m pytest tests/ botsite/tests
  dashboard/tests review/tests -q` + `python3 bootstrap.py check --strict`
  run before the close-out flip.

⚑ Self-initiated: no — ORDER 022 item 3.

## 💡 Session idea

(pending — captured with its "worth having because" line and deduped
against `docs/ideas/backlog.md` before the close-out flip; honest
"nothing" if no idea earns its keep.)

## ⟲ Previous-session review

(pending — written at close-out.)
