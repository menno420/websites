# 2026-07-16 — Askverify stable ask IDs: exact-ID matching

> **Status:** `in-progress` — branch `claude/askverify-stable-ids`;
> stable `ID: ASK-NNNN` lines in the OWNER-ACTIONS ledger + exact-ID
> matching in `app/askverify.py` with signature fallback.

- **📊 Model:** Claude Fable · medium · feature build (stable ask IDs across ledger + parser + matcher)

**What this session is about:** the 07-15 preflight-verdicts session's own
filed idea, promoted: askverify matches asks by keyword signatures over
their WHAT lines, so a reworded ask silently falls to honest-unmatched
(`UNMATCHED_REASON` literally names the fix). Each `⚑ OWNER-ACTION` block
in `docs/owner/OWNER-ACTIONS.md` gains one `ID: ASK-NNNN` line (assigned
once, append-only, never reused — the 9 open asks become ASK-0001..0009 in
document order). `owner_queue._parse_block` learns the line
(`item["ask_id"]`, absent-safe for legacy blocks), every askverify
REGISTRY entry carries the `ask_id` of the ledger row it verifies today
(derived by running the CURRENT signature matcher against the real ledger
before editing), and `match()` prefers exact-ID lookup — an unknown ID
falls through to the signature scan so a not-yet-registered new ask still
matches honestly; items without an ID keep the signature path unchanged.

⚑ Self-initiated: no — dispatched slice (coordinator), building on the
07-15 card's filed session idea.

## Close-out

**Evidence:**

- files touched this branch: [[fill: final file list]]
- verify: [[fill: exact pytest line + check --strict line]]
- git: [[fill: branch, base, PR number, commit chain]]

**Judgment:**

- Decisions made: [[fill: decisions]]
- Next session should know: [[fill: handoff notes]]

## 💡 Session idea

[[fill: one genuine idea]]

## ⟲ Previous-session review

[[fill: honest review of .sessions/2026-07-15-launch-preflight-verdicts.md
and the 07-16 rerun-jobs card on PR #357's branch if reachable]]
