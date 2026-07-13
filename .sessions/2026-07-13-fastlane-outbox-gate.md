# 2026-07-13 — outbox grammar gate on the CI control fast lane

> **Status:** `in-progress` — branch `claude/fastlane-outbox-gate-0713`;
> flips to `complete` + PR number as the deliberate LAST code step.

- **📊 Model:** Claude Fable 5 · worker · order-slice

**What this session was about:** ORDER 027 item 7 (`control/inbox.md`,
P1 EAP final-night worklist) — "Outbox grammar gate on the control fast
lane". `quality.yml`'s control fast lane short-circuits GREEN on a
control/**-only diff, so `tests/test_outbox_grammar_pin.py` (PR #289)
never runs on exactly the PRs that write `control/outbox.md`; a typo'd
REPORT heading merges green and only reddens the NEXT non-control PR.
Same class as incident PR #307: heartbeat-only PRs skip
`tests/test_own_heartbeat.py`. Add a targeted fast-lane gate for both.

## What was done

- (in progress — filled at close-out)

⚑ Self-initiated: no — ORDER 027 item 7 (`[improve]`, backlog bullet
"Outbox grammar gate in the CI control fast lane",
`docs/ideas/backlog.md`).

## 💡 Session idea

(to be captured at close-out, deduped against `docs/ideas/backlog.md`.)

## ⟲ Previous-session review

(to be written at close-out.)
