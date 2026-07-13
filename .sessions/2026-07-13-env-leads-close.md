# 2026-07-13 — close the #275 env-lead item: SITE_PASSWORD drift + ANTHROPIC_API_KEY walled (ORDER 027 item 4)

> **Status:** `complete` — PR #313, branch `claude/env-leads-close-0713`;
> both #275 env leads marked RESOLVED in the ledgers with PR #282 citations,
> plus a new ⚑ ask to delete the unused dashboard SITE_PASSWORD variable.

- **📊 Model:** Claude (Fable/Claude 5 family) · worker · docs-truing slice

**What this session was about:** ORDER 027 item 4 (`control/inbox.md` —
"Read-path check of the two #275 env leads"). The read-path check itself
already landed pre-order in PR #282 (squash `096202c`): dashboard reads no
`SITE_PASSWORD` (set-but-unused Railway drift, `docs/dashboard.md:127`) and
the botsite-copy `ANTHROPIC_API_KEY` is "not measured — walled"
(`docs/botsite.md:108`). This session verified that prior art still holds at
HEAD (`296bf79`) and closed the loop in the ledgers that still carried the
leads as "unverified / queued next session".

## What was done

- Verified at HEAD: `rg SITE_PASSWORD dashboard/` — zero matches; real
  readers `app/config.py:93` (→ `app/owner.py`) and `botsite/testing.py:191`;
  Railway wall entries quoted, not re-probed (`docs/CAPABILITIES.md`
  2026-07-13 — fresh wall, <14 days).
- `docs/current-state.md` — the "two environment leads … unverified"
  bullet marked RESOLVED with citations; next-session baton trued to
  CLOSED; trimmed to stay inside the 7000-word orientation budget (landed
  at 6999 after four trim cycles — see this card's 💡).
- `docs/owner/OWNER-ACTIONS.md` — row K's ground-truth flag closed with the
  same citations; new ⚑ six-field ask added (delete the unused
  `SITE_PASSWORD` variable from the dashboard Railway service — RISK ✅,
  reversible, the var is read by nothing).
- `control/claims/2026-07-13-env-leads-close.md` — claim taken second
  commit, deleted in this final flip commit.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — 1345 passed, 1 warning; `python3 bootstrap.py check
  --strict` — green once the orientation budget was trimmed back under the
  cap (the only remaining finding before this flip was this card's own
  designed born-red HOLD).

⚑ Self-initiated: no — ORDER 027 item 4 (`control/inbox.md`, fm ORDER 045
relay, EAP final-night worklist).

## 💡 Session idea

**Orientation-budget headroom readout in `bootstrap.py check`** — always
print the boot-read set's word total and remaining headroom even when the
check passes (today the 7000-word budget is invisible until breached: this
session edited `docs/current-state.md` blind, breached at 7065, and needed
four trim/re-run cycles to land 1 word under the cap). Worth having because
every docs-truing session grows current-state.md and only discovers the wall
after writing — a standing "6999/7000" line turns trim work from iteration
into arithmetic. Kit-side (`bootstrap.py` is generated), so this is also a
substrate-kit worthiness relay per the working agreement. Deduped against
`docs/ideas/backlog.md` + the queue-state NEXT list: no
orientation-budget/headroom bullet exists anywhere. Captured in
`docs/ideas/backlog.md`.

## ⟲ Previous-session review

The venture-vetting-catalog session (PR #248) did well — 22 hand-curated
packets landed with a `test_committed_registry_is_honest` pin so the status
breakdown can't silently rot; what it missed: its own sha-drift worry
(everything pinned @ `2c039e3`) went to the backlog instead of shipping as
a cheap CI nag, so the catalog decays exactly the way its 💡 predicts.
