# 2026-07-13 — review: closed-but-unanswered nag on the questions ledger

> **Status:** `complete` — PR #299, branch `claude/questions-answer-nag-0713`;
> the /questions ledger's broken promise (a `[program-review]` issue closed
> without a published answer rendering "closed / pending" forever) now nags
> in two places: one `ADVISORY:` line per record on every questions-bake run
> and a warn banner on `/questions` naming the offenders; lands via the
> auto-merge enabler on green.

- **📊 Model:** Claude 5 family · worker · backlog-slice

**What this session was about:** the backlog bullet "Closed-but-unanswered
nag for the questions ledger" (`docs/ideas/backlog.md`, captured 2026-07-13
by the review-questions-bake-sync session 💡). The bake sync (PR #297)
flips a ledger record's `status` to `closed` from the live issue state, but
answer links stay hand-written — so automating intake made it POSSIBLE to
close a question without answering it on record, silently breaking the
ledger's promise ("the evidence-backed answer publishes in the next review
edition AND lands here"). Chosen as a review/-service increment because the
last six slices all touched the botsite testing heatmap.

## What was done

- `review/story.py` — `unanswered_closed(records)`: the flagged list over
  the existing `question_status` / `question_answer_state` filter
  semantics (closed + pending), pure read, never fabricated.
- `review/app.py` `/questions` passes `q_nag` to the template;
  `review/templates/questions.html` renders a `rv-aged` warn banner
  ("N question(s) closed without a published answer") naming and linking
  each offending record above the ledger table.
- `review/gen_questions.py` — standalone `unanswered_closed` +
  `advise_unanswered` (module stays stdlib-only/import-free); one
  `ADVISORY: closed without a published answer: <url>` line per record on
  EVERY run with a readable ledger — merged, no-change, and fetch-failed
  paths alike; module docstring documents the advisory contract.
- Tests +6 (`review/tests/test_gen_questions.py` advisory semantics /
  bake-print / fetch-failed / all-answered-quiet;
  `review/tests/test_questionnaire.py` page banner present with the right
  record named, absent when every closed question is answered, helper
  semantics incl. defaulted-open records).
- `docs/ideas/backlog.md`: source bullet flipped `captured` → `built`
  (PR #299); this session's 💡 captured as a new bullet.
- Verified before push: `python3 -m pytest tests/ botsite/tests
  dashboard/tests review/tests -q` — 1304 passed, 1 warning (+6 over
  main's 1298); `python3 bootstrap.py check --strict` — green except this
  card's own designed born-red HOLD (flipped by this commit) and the
  pre-existing never-exit-affecting `owner-action-fields` advisory on
  control/status.md (not owned here).

## 💡 Session idea

**Stamp `closed_at` on ledger records at bake time — turn the nag into an
answer-debt age** — `gen_questions.issue_record` reads the issue's state
but discards its `closed_at` timestamp, so the new nag is binary: "closed
without a published answer" reads the same whether the question closed an
hour ago (answer plausibly in flight) or two weeks ago (promise genuinely
broken). Recording `closed_at` on the record when the sync flips a status
to closed (one field, same single REST call, hand-written fields untouched)
would let the advisory and the /questions banner say "closed N days without
an answer" and let the ledger sort by answer debt. Worth having because a
nag with an age ranks itself — the oldest broken promise is the one the
next session should pay first, and today the advisory can't tell it from
this morning's. Deduped against `docs/ideas/backlog.md`: the bake-sync and
closed-but-unanswered bullets (both `built`) cover intake and the binary
flag; the owner-gated answer-bot bullet generates answers; nothing carries
closure timestamps or measures answer lag. Captured in
`docs/ideas/backlog.md`.

## ⟲ Previous-session review

The venture-vetting-catalog session (PR #248) did well — 22 packets
hand-curated with each status derived from its packet's own Status/Verdict
text and an honest test pin (unique slugs, the exact 1/12/2/7 breakdown,
every source @ `2c039e3`), so the page cannot silently drift from what was
actually curated; what it missed: the whole catalog decays the moment
venture-lab moves, and its own sha-drift-pin idea was left as a backlog
bullet rather than shipping the one-line pinned-sha check in-slice — a
hand-curated registry's freshness watch is cheapest to build while the
curation context is still loaded. Workflow improvement: when a slice
creates a pinned-source artifact, land the drift nag in the same PR (this
session's own nag-shaped slice exists precisely because #297 didn't).
