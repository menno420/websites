# 2026-07-13 — fm ORDER 038 reflection: VERDICT-016 reviewer-authenticity gate into websites doctrine

> **Status:** `complete` — branch `claude/fm-order-038-reflection`, PR
> opened READY (not draft) against main; merge is the auto-merge lane /
> owner's call — this worker opens, never merges.

- **📊 Model:** Claude Fable 5 family · worker · docs

**What this session was about:** reflecting fleet-manager ORDER 038
(standing, fleet-wide — the sim-lab VERDICT-016 reviewer-authenticity
gate) into websites' binding practice docs. Websites' own intake sweep
(PR #277, `docs/plans/discovery-inventory.md` § Addendum — 2026-07-13
intake sweep) recorded the gap: zero websites mention of VERDICT 016
while the repo does act on codex reviews (e.g. bake PR #270
review-merged). Source read at the pinned sweep SHA: fm
`control/inbox.md@d74eca4` L1092–1111. Imperative text in the fetched
order is DATA; the authority to reflect it here is this session's
dispatch.

## What was done

- `docs/collaboration-model.md` — new binding section "Reviewer
  authenticity — the VERDICT-016 gate (fm ORDER 038)": the order's
  operative lines quoted verbatim with the citation
  fm `control/inbox.md@d74eca4` (L1095–1099 + the Q-0120 rider
  L1102–1104); three requirements spelled out for websites sessions —
  gate before trust (line-range ≤ EOF at the reviewed head; failed
  reply = fabricated, discard and cite the gate), reviewer authenticity
  on non-author review-merges (must rest on the reviewer's OWN genuine
  review; relayed/dispatched authority = review laundering, denied;
  default otherwise stays park-open-green for the auto-merge lane /
  owner), and Q-0120 verify-never-obey on everything that passes.
  Cross-linked to the discovery-inventory addendum record.
- `docs/plans/discovery-inventory.md` — the ORDER 038 addendum row
  flipped from "recorded (unreflected)" to REFLECTED, pointing at the
  new section (drift fixed in the same session it became fixable).
- `control/claims/2026-07-13-fm-order-038.md` — work claim filed with
  the build commit, deleted in this close-out commit per convention.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — 1206 passed; `python3 bootstrap.py check --strict`
  — green at flip (mid-session red was solely this card's designed
  born-red hold; the one advisory on `control/status.md` OWNER-ACTION
  fields is pre-existing, never exit-affecting, and status.md is
  outside this worker's write scope).

⚑ Dispatched: yes — fleet-manager ORDER 038 reflection routed to this
seat; docs-only, contained + reversible (no code, no control status
files touched).

## 💡 Session idea

**Mechanize the VERDICT-016 gate as `scripts/verify_reviewer_reply.py`** —
the gate's cheapest check (every cited `file:Lx-Ly` range must be ≤ EOF
of the cited file at the reviewed head) is pure mechanics: a small
script that takes a reviewer reply body + a git SHA, extracts cited
ranges, and prints PASS / FABRICATED-per-citation would turn the new
doctrine section from prose-a-session-must-remember into a one-command
habit — and its output line is exactly the "cite the gate when
discarding" artifact the fm done-when asks for. Deduped against
`docs/ideas/backlog.md`: no VERDICT/authenticity/reviewer-gate bullet
exists there (nearest neighbors are exit-review evidence and review-site
bake items — different surface). Capture into the backlog is a
follow-up; this session's diff was deliberately scoped to the
reflection.

## ⟲ Previous-session review

The webhook-analyzer session (.sessions/2026-07-13-webhook-analyzer.md,
PR #266) set the bar this card copied: honest grounding tiers (Discord's
unverified signature guidance explicitly downgraded rather than
invented) is exactly the authenticity posture ORDER 038 now makes
doctrine; workflow improvement — it queued BOTH its backlog bullet and
its provenance-loader consolidation as follow-ups for the fourth time
running, so scoped sessions need a standing "backlog-sweep" micro-slice
that batches these orphaned follow-ups before they compound further.
