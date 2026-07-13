# 2026-07-13 — railway reason bound: route Railway GraphQL error reasons through short_reason()

> **Status:** `in-progress` — branch `claude/railway-reason-bound`; flips to `complete`
> + PR number as the deliberate LAST code step.

- **📊 Model:** Claude Fable · worker · hardening-slice

**What this session is about:** finishing the alignment the #240 card
itself filed as a follow-up: PR #240 bounded every GitHub-envelope error
reason at the source (`app/github.py` `short_reason()` — 140-char cap,
single line, markup bodies → generic phrase), but `app/railway.py` still
mints its OWN GraphQL error strings with only a `[:300]` truncation and
no markup stripping, so a Railway failure can paint up to 300 chars of
raw upstream error text — including HTML — onto the owner
envhub/envdrift/environments pages. This session routes ALL error-reason
minting in `app/railway.py` through the same `short_reason()` helper,
with tests. Coordinator-assigned slice under ORDER 022 (night-run
quality floor).

## Checklist

- [ ] Claim landed (`control/claims/railway-reason-bound.md`) + born-red card (this commit)
- [ ] PR opened ready (not draft), auto-merge left to the enabler workflow
- [ ] `app/railway.py`: GraphQL errors-array path bounded via `short_reason`
- [ ] `app/railway.py`: HTTP-status / non-JSON-body path bounded via `short_reason`
- [ ] `app/railway.py`: httpx exception path bounded via `short_reason`
- [ ] Tests: HTML body / huge body / multiline / short-passthrough + rendered owner-page test
- [ ] All four suites green + `bootstrap.py check --strict` (only this card's designed hold)
- [ ] Merge origin/main, flip this card, drop the claim (last commit)

## What was done

- (filled at flip)

⚑ Self-initiated: no — coordinator-assigned slice under ORDER 022
(quality floor), follow-up named by the #240 session card.

## 💡 Session idea

(filled at flip)

## ⟲ Previous-session review

(filled at flip)
