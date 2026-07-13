# 2026-07-13 — guide chat transcript as exit-review evidence

> **Status:** `complete` — PR #292, branch `claude/guide-transcript-evidence-0713`;
> successful guide-chat exchanges (text only, bounded by the existing
> per-claim guide cap) now persist in a new `guide_exchanges` table and
> attach to the submission as untrusted evidence — grader + re-grade
> prompts, owner queue, tester status page, and the JSON export all
> carry it; the frame path stays write-free per the privacy contract.

- **📊 Model:** Claude Fable 5 · worker · feature-slice

**What this session was about:** building the backlog capture "Guide chat
transcript as exit-review evidence" (`docs/ideas/backlog.md` lines
186-198, sourced from the ORDER 018 PR3 session card's 💡). The
guided-walkthrough side panel generates a per-step Q&A between tester
and AI guide, but it evaporated when the tab closed — the exit reviewer
graded the final answers blind to how the tester actually engaged, and
the owner never saw coached-vs-independent answers.

## Results

- `botsite/testing_store.py` — new `guide_exchanges` table (claim_id,
  step_index, message, reply, created_at) + `add_guide_exchange` /
  `guide_transcript_for_claim` (oldest-first); `export_all` gains a
  `guide_exchanges` key so the backup valve carries the evidence.
- `botsite/testing.py` — `/s/{token}/guide/chat` persists the exchange
  only AFTER the cap-checked AI reply succeeds (per-claim guide cap
  bounds row count; degraded/capped replies never stored; no new env
  vars, no new routes — the chat route already carries same-origin +
  rate-limit guards). `_submission_ctx` and `_owner_page` thread the
  transcript to the pages; `_run_exit_review` and the follow-ups
  re-grade pass it to the grader. The frame route stays write-free
  (test-pinned in-memory-only privacy contract — nothing derived from a
  shared screen lands in the transcript, not even the guide's text
  reply).
- `botsite/testing_ai.py` — optional `guide_transcript` kwarg on
  `grade_submission` / `regrade_with_followups`, rendered as an
  `<untrusted_guide_chat_transcript>` block framed strictly as
  engagement evidence (both sides untrusted).
- Templates: `testing_guide.html` discloses the persistence next to the
  chat box; `testing_owner.html` shows a collapsed transcript per
  submission labeled untrusted; `testing_submission.html` shows the
  tester their own stored copy.
- Tests: 7 new in `botsite/tests/test_testing_guide.py` — persistence +
  visibility on all four surfaces, grade & re-grade prompt framing,
  non-guided prompts stay clean, degraded chat never stored, cap bounds
  storage, frame path writes no transcript row, disclosure copy.
- backlog: the source bullet flipped `captured` → `built` (PR #292);
  this session's 💡 captured as a new bullet.
- git: branch `claude/guide-transcript-evidence-0713` off 2ceab15 →
  d149f4d (claim + born-red card) → 30d0f6b (feature + tests) → this
  close-out flip. PR #292 (ready, not draft; auto-merge left to the
  enabler).
- verify: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` → 1262 passed, 1 warning (baseline 1255 + 7 new);
  `python3 bootstrap.py check --strict` → green except this card's own
  designed born-red HOLD (flipped by this commit) and the pre-existing
  never-exit-affecting `owner-action-fields` advisory on
  control/status.md (not owned here).
- Decisions made: persist only SUCCESSFUL chat exchanges (bounded by the
  existing guide cap — no new storage knob, and degraded copy carries no
  coaching worth grading); keep the frame path byte-for-byte write-free
  rather than persisting its text replies (a reply describing a shared
  screen leaks screen content by proxy); disclose persistence in the
  chat panel rather than burying it.
- Next session should know: transcripts of claims that chat but never
  submit are stored yet invisible (owner queue iterates submissions) —
  captured as this card's 💡; PR #292 awaits the auto-merge enabler.

⚑ Coordinator-assigned slice (backlog capture → built).

## 💡 Session idea

**Abandoned guided sessions surfaced on the owner queue** — a claim that
chats with the guide but never submits now leaves transcript rows the
owner can never see: the owner queue iterates submissions, so drop-off
evidence (where testers engaged, got confused, and gave up) is stored
but invisible. A small owner-queue section listing claimed-but-never-
submitted claims that have guide-chat activity (count + last exchange
time, transcript behind the same collapsed details) would turn silent
abandonment into product feedback — the walkthrough step where chats
cluster before a claim dies is exactly the step that needs rewriting.
Deduped against `docs/ideas/backlog.md` + the queue-state NEXT list:
nothing covers abandoned/unsubmitted claims or drop-off signals; the
transcript bullet this session built covers submissions only.

## ⟲ Previous-session review

The venture-vetting-catalog session (PR #248) earned its "honest
catalog" name — deriving each of the 22 statuses from the packet's own
Status/Verdict text and pinning the 1/12/2/7 breakdown in a
committed-registry test was the right defense for hand-curated data;
what it left soft is the pin it flagged itself: freshness lives only as
a backlog bullet, so the page's honesty still decays silently the
moment venture-lab moves past `2c039e3`.
