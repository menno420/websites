# 2026-07-18 — Planning pass: groomed next-cycle queue + doc hygiene

> **Status:** `complete`

- **📊 Model:** Opus · high · idea/planning

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
  - `control/claims/next-cycle-plan.md` — this pass's own claim, DELETED at this
    flip (claims README step 4: delete your own claim at session close) so it never
    outlives its merged branch and re-reds the claims-drift gate on main.
- verify: `python3 -m pytest tests/ botsite/tests dashboard/tests review/tests -q`
  — **1928 passed**, 0 failed (exit 0); `python3 bootstrap.py check --strict` green
  at this flip (the designed born-red hold on this card released on completion).
- git: branch `claude/next-cycle-plan`; commits `dfff7ea` (born-red card + claim),
  `5f4ac5f` (groomed queue + NEXT-TASKS prune + current-state refresh + orphaned-claim
  drop), `521e67c` (baton → B6), + this flip (card complete + own-claim delete).

**Judgment:**

- Decisions made: land the groomed queue as a committed plan doc rather than only
  editing NEXT-TASKS in place, so future sessions boot from one dated, HEAD-stamped
  queue; prune shipped items into an evidence-cited "Verified shipped" section rather
  than deleting them, preserving the audit trail; delete the orphaned claim to clear
  the pre-existing claims-drift red in the same pass.
- Next session should pick up: **B6 — dashboard `/env` config-drift flags** (M ·
  seat · no gate) — the sole open seat-buildable feature; groomed detail in
  `docs/plans/next-cycle-2026-07-18.md` §1.

## 💡 Session idea

`docs/NEXT-TASKS.md` should carry a lightweight **self-verifying test** so shipped
items can't silently linger as "open": a guard that cross-checks each still-"open"
ranked item against a shipped-evidence marker (the very evidence files this pass
cited) and reds when an open item's evidence already exists in the tree. It would
turn this manual prune into a standing invariant — the file could never again
mislead a future session into re-proposing shipped work.

## ⟲ Previous-session review

The `.sessions/2026-07-18-release-drift-banner.md` card (ORDER 033) closed
**complete and clean** — it flipped on a fully green four-suite run with its
born-red hold released exactly at the flip, and its close-out cited every touched
file with a decisions/next-session judgment. A well-formed exemplar of the born-red
protocol this pass follows; the one nit worth carrying is that its `📊 Model:` line
uses free-text effort/task-class segments the PL-004 checker flags as advisory —
this card uses the checker's taught form (`Opus · high · idea/planning`) instead.
