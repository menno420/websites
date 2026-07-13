# 2026-07-13 — document TESTING_AI_* config vars in both inventories + extend the code-vs-inventory pin

> **Status:** `in-progress` — branch `claude/testing-ai-inventory`; flips to `complete`
> + PR number as the deliberate LAST code step.

- **📊 Model:** [[fill:model]]

**What this session was about:** backlog promotion rung — executes the 💡 from
`.sessions/2026-07-13-inventory-consistency-pin.md` (PR #225): `botsite/testing_ai.py`
consumes `TESTING_AI_MODEL`, `TESTING_AI_DAILY_CAP`, `TESTING_AI_GUIDE_CAP`, but
neither `app/railway.py` SERVICES nor the envhub registry documents them for
botsite — review's equivalents ARE documented, so the omission is inconsistent,
not a policy. Document the names (names + purpose + manage link only, never
values) in BOTH inventories, and where clean, grow the pin a third leg:
code-consumed names ⊆ documented names.

## What was done

- [[fill:what-was-done]]

⚑ Self-initiated: no — coordinator-assigned slice executing the captured
code-vs-inventory backlog idea.

## 💡 Session idea

[[fill:idea]]

## ⟲ Previous-session review

[[fill:previous-review]]
