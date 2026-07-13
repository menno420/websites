# 2026-07-13 — botsite: per-step question digest — surface WHAT testers asked at a hotspot, not just how many

> **Status:** `complete` — PR #304, branch `claude/step-question-digest-0713`;
> the owner queue's heatmap and finisher-hotspot strips now carry a
> collapsed per-step digest of the actual tester questions
> (`guided_step_questions()`: persisted `guide_exchanges` message text
> grouped by (task, step) across ALL claims, newest 5 per cell), so
> "step 3 · 4 asked" expands into the four questions themselves; lands
> via the auto-merge enabler on green.

- **📊 Model:** Claude Fable · worker · dispatched backlog-promotion slice

**What this session was about:** backlog promotion ("Per-step question
digest — surface WHAT testers asked at a hotspot, not just how many",
captured 2026-07-13 from the finisher-hotspots session 💡,
`docs/ideas/backlog.md`). The heatmap and finisher hotspots
(PRs #294/#298/#303) rank WHERE guide chats cluster, but the owner still
opens each drop-off's per-claim transcript one by one to learn WHAT
confused people — and finishers' transcripts on hotspot tasks render
nowhere at all (PR #292 attaches them to submissions, not to the strip).
This session groups the persisted `guide_exchanges` tester messages by
(task, step) across ALL claims and renders the actual questions (message
text only, untrusted-input framing, capped + collapsed) behind each
hotspot cell.

## What was done

- `botsite/testing_store.py` — new `guided_step_questions()`: the
  persisted `guide_exchanges` MESSAGE text (tester side only — the
  guide's replies never enter the digest) keyed
  `task_id → step_index → {total, questions}`, scope every claim with
  chat activity regardless of outcome (drop-offs AND finishers — a
  hint-needing step reads the same whatever became of the asker). Each
  cell keeps the newest `QUESTION_DIGEST_CAP` (5) texts newest-first so
  one chatty claim can't scroll the strip, plus the running `total`.
- `botsite/testing.py` `_owner_page` — joins the digest onto BOTH strips'
  cells (`question_total` + `questions`, truncated by the new
  `_digest_question_text` at `QUESTION_DIGEST_TEXT_MAX` 160 chars, the
  `_heatmap_step_text` idiom); padded never-reached cells stay
  question-free. Read-only, no new route, no new env reads (no CSRF
  surface).
- `botsite/templates/testing_owner.html` — `step_question_digest` macro:
  one collapsed `<details>` per asked-at step rendered directly under the
  heatmap row and the finisher-hotspot row, summary
  "step N · M tester question(s) [· newest 5 shown] (untrusted tester
  input)", questions autoescaped by Jinja2. The digest summary uses the
  cells' `·` separator, not `—`, so #294's "step 2 —" bare-number
  tooltip pin stays intact.
- `botsite/tests/test_testing_owner_question_digest.py` — +11 tests
  (grouping across outcomes with replies excluded; newest-5 cap +
  total; empty/chatless cases; per-task separation; rendered digest
  behind heatmap AND hotspot cells; `<script>` message renders escaped,
  never as markup; rendered cap keeps the two oldest questions out of
  the digest while the transcript block keeps them; 160-char truncation
  with the transcript untruncated; question-free cells grow no
  `<details>`; pure-helper truncation bounds).
- `docs/current-state.md` — header suite figure trued 1325 → 1336
  (one-word change, #298/#303 precedent).
- `docs/ideas/backlog.md` — source bullet flipped `captured` → `built`
  (PR #304); this session's 💡 captured as a new bullet.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — **1336 passed, 1 warning** (+11 over main's 1325);
  `python3 bootstrap.py check --strict` — green except this card's own
  designed born-red HOLD (flipped by this commit) and the pre-existing
  never-exit-affecting `owner-action-fields` advisory on
  control/status.md (not owned here).
- Decisions made: the digest pools finisher and drop-off questions in the
  SAME cell (the backlog's "across ALL claims") instead of splitting by
  outcome — the strip cell above already carries the outcome split
  (touched/died vs finished), and the rewrite input the owner needs is
  the union; the cap lives in the store (grouping semantics) while the
  160-char display truncation lives in the route (presentation), same
  layering as the step-text join.
- Next session should know: claim file deleted here; the digest's
  semantics doc lives in the `guided_step_questions()` docstring;
  PR #304 rides the auto-merge enabler.

⚑ Self-initiated: no — backlog promotion, `docs/ideas/backlog.md`
"Per-step question digest", source
`.sessions/2026-07-13-finisher-hotspots.md` 💡.

## 💡 Session idea

**Guide-question step provenance — pin what the step SAID when the
question was asked** — `guide_exchanges` rows pin only `step_index`, so
the digest (PR #304) and both strips (#294/#298/#303) attribute every
persisted question to whatever text CURRENTLY sits at that index: the
moment a walkthrough script inserts, removes, or reorders a step,
history is silently re-attributed to the wrong step and a hotspot can
point the owner at a step nobody actually asked about. Persisting a
small step snapshot with each exchange (the step's title, or a hash of
it — the title already joins into tooltips via `_heatmap_step_text`)
would let the strips flag "asked against an older version of this step"
instead of misattributing. Worth having because the digest's whole pitch
is turning counts into trustworthy rewrite input — and the first script
rewrite the hotspots trigger is exactly the event that corrupts the
attribution. Deduped against `docs/ideas/backlog.md`: the heatmap,
survival-contrast, finisher-hotspots, and digest bullets all consume
`step_index` as-is; the step-text bullet (built, #294) joins the CURRENT
title for display only; nothing versions or snapshots step identity.
Captured in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

The finisher-hotspots session (PR #303) did well — it protected #298's
tested "tasks appear only with drop-offs" pin by building a separate
aggregate instead of folding rows in, used the info tint so nothing
implies death where nobody died, and captured this very slice as its 💡;
what it missed is that its cells and tooltips say "N asked" while
counting claims-not-exchanges, so an owner reading "asked" as a question
count undercounts chatty testers — the digest's per-cell `total` now
states the actual message count beside them.
