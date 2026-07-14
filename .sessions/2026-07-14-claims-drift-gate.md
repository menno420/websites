# 2026-07-14 — claims-drift gate: fail quality on claims for merged branches

> **Status:** `complete` — PR #318, branch `claude/claims-drift-gate-0714`;
> quality now FAILS when a `control/claims/*.md` references a branch that
> already merged into main (the orphaned-claim drift class the 2026-07-13
> fleet cleanup audit caught by hand), the proven-stale railway-placeholders
> claim is swept, and the control-plane gets the favicon the #311 cold pass
> gave the other three services.

- **📊 Model:** Claude Fable 5 · worker · gate-build + drift-sweep

**What this session was about:** backlog promotion — the fleet cleanup
audit (`docs/audits/2026-07-13-fleet-cleanup-audit.md`, suggestion 2 /
finding 1) proposed a cheap CI check that fails `quality` when a
`control/claims/*.md` file references a branch that has already merged
into main (the orphaned-claim drift class its finding 1 caught by hand:
`control/claims/2026-07-13-railway-placeholders.md` outliving merged
PR #275). This session builds that gate as a pytest, wires the control
fast lane to run it when a claims file is in a control-only diff, and
sweeps the proven-stale claim.

## What was done

- `tests/test_claims_drift_gate.py` — the committed-tree pin plus detector
  proofs, pure git plumbing, zero network. Terminality lanes: (1) true
  merge / fast-forward via `git merge-base --is-ancestor`; (2) squash merge
  (this repo's normal landing path) via combined-diff `git patch-id
  --stable` matched against each commit on `merge-base..main` (capped 500).
  Everything indeterminate is fail-safe LIVE — unparseable/scope-only
  tokens, never-pushed or pruned refs, patch-id drift; `README.md` skipped.
  Synthetic-repo tests prove all four lanes so the pin can't rot into
  pass-everything.
- `.github/workflows/quality.yml` — a control-only diff touching
  `control/claims/**` now runs exactly this pin via the PR #314 `pin_tests`
  mechanism, so claims landing/releasing on the fast lane are graded too.
- `control/claims/2026-07-13-railway-placeholders.md` — deleted. ORDER 026
  completed via PR #275 (merged 2026-07-13T10:57:44Z, squash `cedca1e`);
  the new gate flagged exactly this file before deletion — a live
  validation of the detector against real history.
- `app/static/favicon.svg` + icon link in `app/templates/base.html` +
  `tests/test_app.py::test_favicon_is_linked_and_served` — the #311
  cold-pass favicon pattern ported to the one service that pass skipped.
- This session's own claim (`control/claims/2026-07-14-claims-drift-gate.md`)
  created per convention, graded LIVE by the gate while in flight, and
  released in this close-out commit (claims README step 4).
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — 1365 passed, 1 warning (baseline 1358 + 6 gate tests
  + 1 favicon test); `python3 bootstrap.py check --strict` — all checks
  passed after this flip.

⚑ Self-initiated: no — audit suggestion 2 promotion
(`docs/audits/2026-07-13-fleet-cleanup-audit.md`).

## 💡 Session idea

**Claim bullet carries its PR number once opened — closes the drift gate's
pruned-ref blind spot** — the gate deliberately treats a claim whose branch
resolves to NO ref as live (fail-safe), so if this repo ever starts pruning
branches on merge, an orphaned claim becomes undetectable. An optional
`PR #N` token in the claim bullet (added when the PR opens) would let the
gate fall back to `git log origin/main --grep='(#N)'` — the squash subject
survives the pruned ref, same zero-network plumbing. Worth having because
the gate's one documented indeterminate lane is exactly the state
GitHub's "delete branch on merge" setting would make the COMMON case.
Deduped against `docs/ideas/backlog.md` + the queue-state NEXT list: the
claim-related bullets there cover order-claim latency, stalled-claim aging
on /orders, and sweep-hold files — nothing touches claim grammar or
terminality detection. Captured in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

The venture-vetting-catalog session (PR #248) did well — 22 titles curated
with each status derived from its packet's own blockquote (nothing
invented) and pinned by a registry-honesty test; what it missed: its own 💡
admits the catalog decays the moment venture-lab moves, and the sha-drift
nag that would catch that stayed a backlog bullet, so the honesty pin
guards structure but not freshness.
