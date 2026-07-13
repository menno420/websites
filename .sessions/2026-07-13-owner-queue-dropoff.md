# 2026-07-13 — owner queue: drop-offs section (abandoned guided sessions)

> **Status:** `complete` — PR #293, branch `claude/owner-queue-dropoff-0713`;
> claimed-but-never-submitted claims with guide-chat activity now render as a
> read-only "Drop-offs" section on GET /testing/owner (exchange count, last
> exchange time, transcript behind the same collapsed details as #292).

- **📊 Model:** Claude Fable 5 · worker · backlog-promotion

**What this session was about:** backlog promotion — the `captured` bullet
"Abandoned guided sessions surfaced on the owner queue" in
`docs/ideas/backlog.md` (2026-07-13, from the #292 guide-transcript-evidence
session 💡). A tester who chats with the AI guide but never submits leaves
persisted `guide_exchanges` rows (PR #292) the owner can never see, because
the owner queue at GET /testing/owner iterates submissions only. This session
adds a small read-only "Drop-offs" owner-queue section listing
claimed-but-never-submitted claims that have guide-chat activity — exchange
count + last exchange time, full transcript behind the same collapsed
`<details>` the submissions view uses.

## What was done

- `botsite/testing_store.py` — new read-only accessor
  `abandoned_guided_claims()`: `claims` × `guide_exchanges` join filtered to
  status='claimed', no `submissions` row (NOT EXISTS), ≥1 exchange; returns
  the claim fields + `exchange_count` + `last_exchange_at`, newest activity
  first (ties broken by claim id desc).
- `botsite/testing.py` `_owner_page` — builds a `dropoffs` ctx list (accessor
  row + transcript via `guide_transcript_for_claim`). No new routes, no new
  env vars, no state changes — the GET page stays read-only, so no new CSRF
  surface.
- `botsite/templates/testing_owner.html` — "Drop-offs — chatted with the
  guide, never submitted (N)" section between Submissions and Claims, reusing
  the existing card/badge markup and the #292 collapsed `<details>`
  transcript block; quiet "No drop-offs" hint as the empty state.
- `botsite/tests/test_testing_owner_dropoffs.py` — 8 network-free tests:
  accessor fields/count/last-exchange, ordering (controlled clock), submitted
  and chat-free claims excluded (store + page), the rendered section with
  count and transcript text, and the belt-and-braces NOT EXISTS guard. The
  /testing/owner no-auth 401 pin already lives in `test_testing.py`.
- `docs/ideas/backlog.md` — the source bullet flipped `captured` → `built`
  (PR #293); this session's 💡 captured as a new bullet.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — 1270 passed, 1 warning (+8 over main's 1262);
  `python3 bootstrap.py check --strict` — green except this card's own
  designed born-red HOLD (flipped by this commit) and the pre-existing
  never-exit-affecting `owner-action-fields` advisory on control/status.md
  (not owned here).

⚑ Self-initiated: no — backlog promotion of the `captured` bullet
"Abandoned guided sessions surfaced on the owner queue"
(`docs/ideas/backlog.md`, 2026-07-13, #292 session 💡).

## 💡 Session idea

**Drop-off step heatmap on the owner queue** — a tiny per-task aggregate over
the same `guide_exchanges` rows: for each step_index, how many abandoned
claims' chats touched it and how many died there (their last exchange),
rendered as a one-line count strip per task. Worth having because per-claim
transcripts are anecdotes — the capture's own point was "the walkthrough step
where chats cluster before a claim dies is exactly the step that needs
rewriting", and the per-step aggregate is that rankable number. Deduped
against `docs/ideas/backlog.md` + the queue-state NEXT list: the drop-off
bullet (now built) surfaces claims, not step aggregates; nothing aggregates
guide-chat activity per step. Captured in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

The venture-vetting-catalog session (PR #248) did well — 22 packets curated
with per-title provenance and an honesty pin (`test_committed_registry_is_honest`)
that makes the 1/12/2/7 breakdown regression-proof; what it missed: its own
💡 admits the page decays the moment venture-lab moves, and no freshness or
sha-drift signal shipped alongside the catalog it protects.
