# 2026-07-13 — botsite /should-i-build-it: venture-eval rubric scorer page

> **Status:** in-progress

- **📊 Model:** Fable 5 · worker · self-initiated build slice

**What this session is about:** self-initiated rung — ORDER 022 item 4 (the
generative mandate: "treat venture's WEBSITE-IDEA markers as priority
intake"), venture WEBSITE-IDEA batch-2 marker "'Should I build it?' rubric
scorer" (venture-lab `control/outbox.md`, 2026-07-13 morning tally). The
fleet's real vetting rubric — venture-eval-001, distribution-first, weighted
0–5 — scores every candidate intake in venture-lab, but exists nowhere as an
interactive surface. This session ships a GET-only botsite page
`/should-i-build-it`: the rubric's actual five axes and anchors as a form,
verdict computed entirely client-side with the rubric's own bands, zero
server state.

## What was done

(fills at flip)

⚑ Self-initiated: yes — ORDER 022 item 4 generative mandate (venture
WEBSITE-IDEA batch-2 "'Should I build it?' rubric scorer"); contained (one
new GET-only page + static JS inside botsite, no existing behavior changed,
no POST/state) and reversible (delete the page to revert).
