# 2026-07-13 — owner queue: per-step drop-off heatmap over guide_exchanges

> **Status:** `in-progress`

- **📊 Model:** Claude (Fable family) · worker · backlog-promotion

**What this session is about:** backlog promotion — the `captured` bullet
"Drop-off step heatmap on the owner queue" in `docs/ideas/backlog.md`
(2026-07-13, from the #293 owner-queue-dropoff session 💡). PR #293 surfaces
each abandoned claim's guide transcript individually, but the signal the
capture named — "the walkthrough step where chats cluster before a claim dies
is exactly the step that needs rewriting" — still requires reading every
transcript. This session adds a tiny per-task, per-step aggregate over the
same `guide_exchanges` rows, rendered as a compact heatmap strip inside the
existing Drop-offs section on GET /testing/owner.

## Plan

- `botsite/testing_store.py`: new read-only accessor `guided_step_dropoff()`
  — same scope as `abandoned_guided_claims()` (status 'claimed', no
  submission row, ≥1 exchange); per task and per step_index: how many claims'
  chats touched that step and how many died there (their max step_index).
- `botsite/testing.py` `_owner_page`: feed the aggregate into the template
  context. No new routes, no state changes — the page stays read-only.
- `botsite/templates/testing_owner.html`: per-task one-line strip in the
  Drop-offs section — step number, touched count, died-here count, cell
  shading scaled by the died-here share. Server-rendered Jinja2 only.
- `botsite/tests/`: accessor tests (multiple claims, differing max steps,
  empty case, scope exclusions) + route rendering test.
- Verify: full four-suite pytest + `bootstrap.py check --strict`; PR ready
  (non-draft), auto-merge armed by the repo's enabler workflow.
