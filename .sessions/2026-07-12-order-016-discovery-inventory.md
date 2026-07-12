# 2026-07-12 — ORDER 016 cross-repo website-plans discovery inventory

> **Status:** `in-progress` — PR branch `claude/order-016-discovery-inventory`,
> opened READY; this card is born-red by design and flips to complete last,
> after the inventory lands and is verified.

- **📊 Model:** Claude (frontier family) · build worker · order

**What this session is about:** ORDER 016 (`control/inbox.md` @ `0101b93`):
"find all website related plans across the multiple repos and execute all the
important ones." The build slices merged over the course of 2026-07-12, but
the order's done-when explicitly requires **a committed discovery inventory**
listing the website-related plans found across the repos, each important one
executed or explicitly ledgered with a reason (owner-gated / superseded /
deferred) — and `control/status.md` line 13 confirms 016 is IN PROGRESS
precisely because that committed inventory is still absent. This session
supplies it.

## What was done

- **Swept four repos via four parallel read-only workers** at pinned HEADs —
  websites@`0101b93` (local checkout: all 21 inbox ORDERs + done-states,
  docs/planning + docs/ideas + OWNER-ACTIONS, ~40 deduped session-card
  ideas, review data, PR #160's branch + all open PRs), and via GitHub MCP
  fleet-manager@`8724b29` (~20 plan findings), substrate-kit@`bf1fc80`
  (~13 findings), superbot@`85a2ec0` (~16 findings). Every finding cited as
  `repo/path@sha`.
- **Committed the inventory**: `docs/plans/discovery-inventory.md` — a
  headline section dispositioning every important plan (EXECUTED: launch
  console + arcade slices, review-site EAP refresh, prompt
  library/paste-source; PARTIAL: ORDER 020 writeback + ORDER 021
  environments hub with their exact owner gates; OWNER-GATED: /submit
  Postgres, tester payouts, custom domains, bot-control panel, old-site
  cutover, P6 console move, games selector UI, secret-reveal slice 3;
  SUPERSEDED: the superbot-era legacy website plans + the answer-bot backlog
  bullet; DEFERRED: suggestion copilot, dashboard.json contract completion,
  design-system lane, the ~19 backlog bullets), four per-repo findings
  tables, negative findings (no prior inventory existed anywhere; PR #160
  only minted the 016 number), and a not-swept honesty section aggregated
  from all four sweep reports.
- **Linked the inventory** from `docs/current-state.md` §Recently shipped
  (docs-gate reachability).
- **Verified**: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` green; `python3 bootstrap.py check --strict` red only on
  this card's designed born-red hold at commit time, fully green at flip.

⚑ Self-initiated: no — ORDER 016 (`control/inbox.md`, landed by the
coordinator seat on the owner's direct live instruction 2026-07-12). The
`status.md` `done=016` flip is deliberately left to the coordinator.

## 💡 Session idea

**Inventory staleness guard** — the quality gate (or a small bake script)
could diff `docs/plans/discovery-inventory.md`'s pinned per-repo HEAD SHAs
(websites@0101b93, fleet-manager@8724b29, substrate-kit@bf1fc80,
superbot@85a2ec0) against the live fleet HEADs and flag the inventory stale
after N days / M commits of divergence. Worth having because a point-in-time
discovery doc rots silently — the repo's existing drift machinery (deploy
drift, snapshot-aging banner, arcade URL probe) covers live surfaces but
nothing covers committed audit docs whose truth is SHA-pinned. Deduped
against `docs/ideas/backlog.md` (its drift bullets cover env-var names,
prompt registries, and arcade URLs — nothing touches audit-doc SHA pins) and
recent cards.

## ⟲ Previous-session review

The ORDER 022 drift-fixes session (newest complete card) was a model of the
verify-then-claim discipline this inventory leans on: it cold-verified the
mineverse URL before flipping the card LIVE, ran the real Railway GraphQL
schema before touching the UNVERIFIED docstrings, and its OWNER-ACTIONS
reconcile (rows K/L) is what let this inventory ledger the RAILWAY_TOKEN and
ANTHROPIC_API_KEY gates as *decided* rather than open — accurate upstream
ledgers made this sweep's dispositions cheap to verify.
