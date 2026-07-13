# 2026-07-13 — owner queue: per-step drop-off heatmap over guide_exchanges

> **Status:** `complete` — PR #294, branch `claude/dropoff-heatmap-0713`;
> the Drop-offs section on GET /testing/owner now opens with a per-task
> step heatmap strip (touched / died-here per step, cell shading by the
> died-here share) aggregated read-only over the same `guide_exchanges`
> rows PR #293 surfaces per claim.

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

## Close-out (auto-drafted 2026-07-13 — edit, don't author)

<!-- substrate:auto-draft -->

**Evidence (auto-collected — verify, then keep or correct):**

- code touched (2): `botsite/testing.py`, `botsite/testing_store.py`
- other touched (3): `botsite/templates/testing_owner.html`,
  `control/claims/2026-07-13-dropoff-heatmap.md` (deleted at close-out),
  `docs/ideas/backlog.md` (source bullet flipped `captured` → `built`,
  this session's 💡 captured). `HANDOFF.md` and `app/writeback.sqlite3`
  are untracked session machinery, not this session's work;
  `.sessions/2026-07-13-session-3.md` is another session's card — not
  touched, not committed here.
- sessions touched (1): `.sessions/2026-07-13-dropoff-heatmap.md`
- tests touched (1): `botsite/tests/test_testing_owner_step_heatmap.py`
  (6 network-free tests: aggregate across claims with differing max
  steps, dense zero-gap cells, per-task grouping/ordering, empty case,
  submitted-claim exclusion, rendered strip with counts + shading, and
  heatmap absent when no drop-offs exist)
- git: branch `claude/dropoff-heatmap-0713`, HEAD 6013c059b → d4fb5b8fb (commits made this session).
- commits this session (2): "Session card + claim: owner-queue drop-off step heatmap (born red)" · "botsite: per-step drop-off heatmap on the owner queue"
- verify: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — 1276 passed, 1 warning (+6 over main's 1270);
  `python3 bootstrap.py check --strict` — green except this card's own
  designed born-red HOLD (flipped by this commit) and the pre-existing
  never-exit-affecting `owner-action-fields` advisory on
  control/status.md (not owned here).

**Judgment (the half only the session knows — resolve every slot):**

- Decisions made: "touched" counts claims whose chat has ≥1 exchange AT
  that step (the capture's own wording: "chats touched it"), not claims
  whose max step passed it — the data only observes chatting, so the
  chatted-at reading is the honest one; steps render dense from 0 so
  gaps show as zero cells; shading = died_here/claim_count capped at
  0.7 alpha to keep cell text readable.
- Next session should know: the strip is numbers-only — step cells say
  "step 3", not what step 3 asks the tester to do; this session's 💡
  (step text labels) is the follow-up. No new routes, no CSRF surface.

⚑ Self-initiated: no — backlog promotion of the `captured` bullet
"Drop-off step heatmap on the owner queue" (`docs/ideas/backlog.md`,
2026-07-13, #293 session 💡).

## 💡 Session idea

**Step text labels on the drop-off heatmap** — the heatmap cells name
steps by number only; the guided tasks' walkthrough step texts already
live in the tester-facing task data (`shaped_tasks()` /
`task_by_id(...)` feed the guide with the step list), so joining
`step_index` against the task's step text in `_owner_page` would let
each cell's tooltip (or a per-task legend line) say WHAT the deadliest
step asks the tester to do — "step 3 · open the theme toggle" instead
of "step 3". Worth having because the heatmap's whole point is naming
the step that needs rewriting, and today the owner still has to open
the tester page to learn what the number means. Deduped against
`docs/ideas/backlog.md`: the drop-off and heatmap bullets (both now
built) cover surfacing and aggregating; nothing joins step_index back
to the walkthrough step text. Captured in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

The venture-vetting-catalog session (PR #248) did well — 22 packets
hand-curated with per-title provenance and the
`test_committed_registry_is_honest` pin that makes its 1/12/2/7 status
breakdown regression-proof; what it missed it also admitted: its own 💡
says the catalog decays the moment venture-lab moves, yet no freshness
or sha-drift signal shipped with it, and that follow-up is still
sitting in the backlog. Workflow improvement: its card's evidence
section listed unrelated untracked machinery files as "touched" — the
auto-draft needs a keep-or-correct pass like the one done here, or
cards overstate their blast radius.
