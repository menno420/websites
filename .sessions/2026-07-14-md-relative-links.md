# 2026-07-14 — rewrite relative links in rendered remote markdown + fleet-wide /favicon.ico

> **Status:** `in-progress` — branch `claude/md-relative-links-0714`; flips to `complete`
> + PR number as the deliberate LAST code step.

- **📊 Model:** Claude Fable 5 · worker · backlog promotion + fleet gap fix

**What this session was about:** backlog promotion — the `docs/ideas/backlog.md`
bullet "Rewrite relative links inside rendered remote markdown to their GitHub
source (or de-linkify them)" (captured 2026-07-14 by the smoke-crawl session,
PR #321). The control-plane renders other repos' markdown verbatim in
`<div class="md">` (heartbeats on /fleet, the fleet-manager ledger on /reviews,
environment docs on /environments), and relative links inside that content
resolve against this origin and 404 — the first smoke-crawl run flagged 20 of
them live. Fixing it lets `scripts/smoke_crawl.py` delete its documented
`.md`-container exclusion. Plus the second PR #321 follow-up finding: the
fleet-wide `/favicon.ico` 404 on raw JSON/XML views — add the route to all
four services.

## What was done

- (in progress)

⚑ Self-initiated: no — backlog promotion (the smoke-crawl session's 💡 bullet
in `docs/ideas/backlog.md`) + the PR #321 follow-up favicon finding.

## 💡 Session idea

(to be filled at close-out)

## ⟲ Previous-session review

(to be filled at close-out)
