# 2026-07-13 — close the #275 env-lead item: SITE_PASSWORD drift + ANTHROPIC_API_KEY walled (ORDER 027 item 4)

> **Status:** `in-progress` — branch `claude/env-leads-close-0713`; flips to
> `complete` + PR number as the deliberate LAST code step.

- **📊 Model:** Claude (Fable/Claude 5 family) · worker · docs-truing slice

**What this session was about:** ORDER 027 item 4 (`control/inbox.md` —
"Read-path check of the two #275 env leads"). The read-path check itself
already landed pre-order in PR #282 (squash `096202c`): dashboard reads no
`SITE_PASSWORD` (set-but-unused Railway drift, `docs/dashboard.md:127`) and
the botsite-copy `ANTHROPIC_API_KEY` is "not measured — walled"
(`docs/botsite.md:108`). This session verifies that prior art still holds at
HEAD and closes the loop in the ledgers that still carried the leads as
"unverified / queued next session".

## What was done

- Verified at HEAD (`296bf79`): `rg SITE_PASSWORD dashboard/` — zero
  matches; real readers `app/config.py:93` (→ `app/owner.py`) and
  `botsite/testing.py:191`; Railway wall entries quoted, not re-probed
  (`docs/CAPABILITIES.md` 2026-07-13 — fresh wall, <14 days).
- `docs/current-state.md` — the "two environment leads … unverified"
  bullet marked RESOLVED with citations (PR #282, `docs/dashboard.md:127`,
  `docs/botsite.md:108`, CAPABILITIES wall, row K); the next-session baton
  line trued to "CLOSED".
- `docs/owner/OWNER-ACTIONS.md` — row K's ground-truth flag closed with the
  same citations; new ⚑ six-field ask added (delete the unused
  `SITE_PASSWORD` variable from the dashboard Railway service — RISK ✅,
  reversible, the var is read by nothing).
- `control/claims/2026-07-13-env-leads-close.md` — claim taken, deleted in
  the final flip commit.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — [[fill: count]]; `python3 bootstrap.py check --strict`
  — [[fill: verdict]].

⚑ Self-initiated: no — ORDER 027 item 4 (`control/inbox.md`, fm ORDER 045
relay, EAP final-night worklist).

## 💡 Session idea

[[fill: one idea you genuinely believe in — never filler]]

## ⟲ Previous-session review

[[fill: one genuine remark on the previous session + one workflow improvement]]
