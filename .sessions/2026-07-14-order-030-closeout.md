# 2026-07-14 — ORDER 030 EAP close-out: walkthrough doc + final-day finish list

> **Status:** `in-progress` — branch `claude/order-030-closeout-0714`; flips to
> `complete` + PR number as the deliberate LAST code step (a finalize pass —
> this card is born-red by design and holds quality red until that pass).

- **📊 Model:** Claude Fable 5 · worker · order close-out (walkthrough doc + finish-list items)

**What this session was about:** order rung — `control/inbox.md` **ORDER 030**
(2026-07-14T09:34:13Z, P1, fleet-manager dispatch; inbox @ `a17de3b`): EAP
final day. Item (b): land `docs/eap-closeout-walkthrough-2026-07-14.md` —
status-badged, README-linked, sections A–E (what the seat did / current state
+ verify commands / OWNER ACTIONS checklist with recommendations + VERIFY
steps / 5-minute tour / handoff notes). Items (a1) PR #334 conflict, (a2) bake
PR #330, (a4) smoke-crawl re-verify are handled by sibling passes this
session; this branch carries the walkthrough.

## What was done

- `docs/eap-closeout-walkthrough-2026-07-14.md` — the ORDER 030 (b)
  walkthrough: A. shipped-work summary (PR-cited, links the
  `docs/audits/eap-project-audit-2026-07-14.md` close-out audit for depth) ·
  B. current state + exact run/verify commands · C. owner-actions checklist
  (all 9 pending ⚑ asks from `docs/owner/OWNER-ACTIONS.md`, each with deep
  link, bolded recommendation, VERIFY step, risk marker; plus PR #324, the 7
  draft lifeboats, coordinator #281, ORDERs 020/021 cross-referenced, #334/
  #330 one-liners) · D. 5-minute verify-it-yourself tour over the four live
  URLs · E. handoff notes.
- `docs/audits/README.md` — inbound link added (reachability).
- `control/claims/2026-07-14-order-030-closeout.md` — claim file (branch ·
  scope · date), per `control/claims/README.md`.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — result recorded at the finalize pass; `python3
  bootstrap.py check --strict` — result recorded at the finalize pass.

⚑ Self-initiated: no — ORDER 030 item (b) (`control/inbox.md` @ `a17de3b`).

## 💡 Session idea

**Owner-actions renderer: generate the checklist from the ⚑ blocks** — the
walkthrough's section C hand-copies what/where/verify from the 9 six-field
⚑ blocks in `docs/owner/OWNER-ACTIONS.md`; the control-plane already parses
six-field blocks for `/queue` (`app/` owner-queue pipeline), so a small
`scripts/owner_checklist.py` (or a `/queue.md` export) could emit the same
compact checklist on demand and never drift from the source blocks. Worth
having because every close-out/briefing that hand-copies the asks is a drift
surface — one renderer keeps recommendation docs honest as asks are struck.
Deduped against `docs/ideas/backlog.md` + the queue-state NEXT list: no
checklist-export/renderer bullet exists (the backlog's owner-queue bullets
are page features, not exports). Capture in `docs/ideas/backlog.md` at the
finalize pass.

## ⟲ Previous-session review

The EAP audit session (PR #332) did well — every number measured or marked
LEAD, verbatim denials preserved, and the full 332-PR/733-run sweeps make it
citable ground truth for this walkthrough; what it missed: no per-service
test split (collect-only ran as one invocation), which section A here would
have liked to cite.
