# 2026-07-16 — claim-bullet PR-number fallback for the claims-drift gate (ORDER 032 overnight slice)

> **Status:** `complete` — branch `claude/claim-pr-fallback-20260716`; one
> contained, reversible slice: an optional, purely additive fallback in
> the claims-drift gate for the pruned-ref blind spot.

- **📊 Model:** Claude Sonnet 5 · medium · feature build

**What this session was about:** ORDER 032 (owner's live overnight
autonomy order) — keep working the backlog slice by slice. A captured
2026-07-14 backlog idea (claims-drift-gate session): the drift gate
(`tests/test_claims_drift_gate.py`, PR #318) treats a claim whose branch
resolves to no ref as LIVE (fail-safe), so a repo that prunes branches on
merge — or any claim naming a branch that was simply never pushed — would
never flag an orphan. The idea: an optional `PR #N` token on the claim
bullet, appended once the PR opens, gives the gate a fallback:
`git log origin/main --grep='(#N)'` (the squash-merge subject convention)
survives a pruned ref, same zero-network git plumbing the gate already
uses. Picked because it needed no GitHub API (still none this session —
ASK-0017), and — checked before starting — doesn't require touching
`bootstrap.py`'s kit-owned grammar: the drift gate's branch/PR parsing is
entirely local regex in the test file itself, not part of the shared
`src/engine/grammar.py` bullet grammar the README documents for the
leading backticked token.

## What was done

- `tests/test_claims_drift_gate.py`: added `_CLAIM_PR` (optional trailing
  `PR #N` token, matched anywhere on the bullet line — not grammar-anchored
  like the leading token), `parse_claim_pr()`, and
  `resolve_via_pr_grep(cwd, main_ref, pr_number)` (`git log --grep='(#N)'
  --fixed-strings`, parens-wrapped so `#9` can never prefix-match a commit
  naming `#99`). Wired into `stale_claims()`: only consulted when
  `resolve_branch_ref` returns `None` AND the bullet carries a PR token —
  every existing code path (resolved ref, no PR token) is byte-identical
  to before.
- Extended the synthetic-repo fixture with a `claude/pruned` branch:
  squash-merged with subject `pruned feature (#99)`, then its local ref
  deleted (`git branch -D`) to genuinely exercise "ref resolves to
  nothing" rather than assert around it.
- 6 new tests: fixture sanity (ref really is gone), the grep fallback
  finds a landed squash / misses an unlanded PR number / doesn't
  prefix-match, `parse_claim_pr`'s grammar (present / absent / prose
  mention above the bullet must not leak in), and the end-to-end
  `stale_claims()` sweep now covers a pruned-ref-with-landed-PR claim
  (flagged) alongside a pruned-ref-with-unlanded-PR claim (stays live) —
  extending the existing orphan-detection test rather than adding a
  parallel one.
- `control/claims/README.md`: documented the optional token — how to
  write it, what it does, and that it's purely additive (no `bootstrap
  claim` flag renders it, no kit change needed, omitting it changes
  nothing).
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — **1636 passed** (1631 baseline + 5 new); `python3
  bootstrap.py check --strict` — all checks passed.

⚑ Self-initiated: yes — ORDER 032's backlog-slice mandate; this lane's
second-choice candidate after the catalog sha-drift pin, which needs a
live cross-repo GitHub read this session can't verify without API access.

## Landing

Same named blocker as every branch this lane has pushed tonight:
**ASK-0017**. Pushed for an interactive session or the owner to open/merge.

## 💡 Session idea

No new idea this session — built a previously-captured backlog idea.

## ⟲ Previous-session review

The storefront-freshness-pin slice (this lane, ~22:45Z) made a good call
skipping a speculative idea (the `drift_report()` renderer) in favor of
one with unconditional value today — this session applied the same test
before picking (checked the catalog sha-drift pin needs live API access
this lane doesn't have, and picked the claim-PR-fallback idea instead,
which it had already flagged as the safer next candidate in its own
heartbeat). What it didn't get to: verifying whether ASK-0017 has moved
at all across four slices now — that check belongs in the heartbeat step
that follows this card, not this build step.
