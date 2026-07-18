# 2026-07-18 — Durable ask IDs on the owner-action queue (C15)

> **Status:** `in-progress` — branch `claude/durable-ask-ids`; give every owner
> ask a durable, content-derived identifier so the gated writeback console
> (`/owner/queue`) targets a mark-complete / assistance / note by that stable id
> instead of by the ask's raw headline text. Touches `app/owner_queue.py` (the
> `ask_uid` derivation + `resolve_uid` lookup, exposed on the ask objects),
> `app/owner.py` (the writeback POST routes resolve the target ask by durable id,
> failing closed on an unknown id — never acting on the wrong ask), and
> `app/templates/owner_queue.html` (the hidden identifier the forms carry). The
> C14 auto-clear (`askverify.annotate` / `split_self_cleaned`) operates on the
> same ask objects — the id is additive and does not disturb it. The CSRF /
> same-origin floor on every state-changing POST is preserved unchanged.

- **📊 Model:** [[fill: model]]

**What this session is about:** the owner console lists each ⚑ needs-owner ask
as a card with per-ask MARK COMPLETE / REQUEST ASSISTANCE / ADD NOTE forms. Each
form has carried the ask's full **headline text** as its hidden `target`, and the
complete route re-finds the ask by exact-headline match to fail closed when the
ask is gone. Headline-as-identity is brittle: it is the ask's WHAT prose, so a
rewording upstream (or two asks that normalize alike) can point the fail-closed
re-find at the wrong ask — or at none. C15 gives each ask a durable,
deterministic id derived from STABLE identifying content (its `ID: ASK-NNNN` when
the ledger block carries one — so the id survives a WHAT rewording — else a short
hash of the normalized headline, the same identity `/queue` dedups on). The id is
identical across reorders of the ledger and stable across runs; the writeback
routes resolve the target ask by it, rejecting an unknown id safely.

⚑ Self-initiated: no — coordinator-dispatched backlog slice (C15).

## Close-out

**Evidence:**

- [[fill: files touched, coverage]]
- [[fill: git — branch, base, commits]]
- [[fill: verify — four-suite count + both bootstrap checks]]

**Judgment:**

- [[fill: decisions made]]
- [[fill: next session should know]]

## 💡 Session idea

[[fill: one genuine session idea]]

## ⟲ Previous-session review

[[fill: one-line remark on the previous card]]
