# 2026-07-18 — Planning pass: groomed next-cycle queue + doc hygiene

> **Status:** `in-progress`

- **📊 Model:** [[fill: model · effort · task-class — resolved at flip]]

**What this session is about:** Planning pass — groom the next-cycle executable
queue as a landed plan doc; fold in doc hygiene and fix the orphaned-claim red.

The curated seat backlog (`docs/NEXT-TASKS.md`) is essentially drained: ~9 of the
ranked items already shipped (verified against the tree), leaving one real feature
slice (B6 dashboard `/env` config-drift flags) plus doc hygiene as the executable
frontier. Substantive new growth now depends on owner product decisions or
hub-venue infra. This session lands a groomed queue doc
(`docs/plans/next-cycle-2026-07-18.md`), prunes the shipped items out of
`docs/NEXT-TASKS.md`, refreshes `docs/current-state.md` to HEAD `07b4bb9` (#421),
and clears the orphaned `nav-reachability-guard` claim that reds
`tests/test_claims_drift_gate.py::test_no_claim_outlives_its_merged_branch` on main
(its branch already merged as #421). Born red on this `in-progress` card; flips to
`complete` on green.

⚑ Self-initiated: no — coordinator-dispatched (planning + hygiene pass).

## Close-out

**Evidence:**

- files touched this branch:
  - `control/claims/next-cycle-plan.md` — this planning pass's claim (born-red card + work).
  - `.sessions/2026-07-18-next-cycle-plan.md` — this card.
  - `docs/plans/next-cycle-2026-07-18.md` — the groomed next-cycle queue (landed plan doc).
  - `docs/NEXT-TASKS.md` — pruned the ~9 verified-shipped items into a "Verified
    shipped (as of #421)" section; B6 left as the sole open seat item; pointer to
    the groomed queue added near the top.
  - `docs/current-state.md` — header SHA bumped `ecbe2bf (#383)` → `07b4bb9 (#421)`;
    #416/#418/#419/#420/#421 added to the recently-shipped log.
  - `control/claims/nav-reachability-guard.md` — DELETED (orphaned claim; its branch
    `claude/nav-reachability-guard` already merged as #421 — fixes the claims-drift red).
  - `control/status.md` — baton refreshed to the next-cycle queue top (B6).
- verify: `python3 -m pytest tests/ botsite/tests dashboard/tests review/tests -q`
  — [[fill: verify result — pytest summary line]]; `python3 bootstrap.py check --strict`
  — [[fill: bootstrap check result]].
- git: branch `claude/next-cycle-plan`; commits [[fill: commit trail — resolved at flip]].

**Judgment:**

- Decisions made: land the groomed queue as a committed plan doc rather than only
  editing NEXT-TASKS in place, so future sessions boot from one dated, HEAD-stamped
  queue; prune shipped items into an evidence-cited "Verified shipped" section rather
  than deleting them, preserving the audit trail; delete the orphaned claim to clear
  the pre-existing claims-drift red in the same pass.
- Next session should pick up: [[fill: Next-session pointer — resolved at flip]].

## 💡 Session idea

[[fill: session idea — resolved at flip]]

## ⟲ Previous-session review

[[fill: previous-session remark — resolved at flip]]
