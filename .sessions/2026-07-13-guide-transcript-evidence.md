# 2026-07-13 — guide chat transcript as exit-review evidence

> **Status:** `in-progress`

- **📊 Model:** Claude Fable 5 · worker · feature-slice

**What this session is about:** building the backlog capture "Guide chat
transcript as exit-review evidence" (`docs/ideas/backlog.md` ~186-198,
sourced from the ORDER 018 PR3 session card's 💡). The guided-walkthrough
side panel generates a per-step Q&A between tester and AI guide, but it
evaporates when the tab closes — the exit reviewer grades the final
answers blind to how the tester actually engaged, and the owner never
sees it. This session persists the TEXT transcript only (bounded per
claim by the existing guide-message cap; screen frames stay
in-memory-only per the test-pinned privacy contract) and attaches it to
the submission as untrusted evidence: fed to the AI exit-review grade +
re-grade, shown on the owner queue, shown back to the tester on their
status page, and included in the JSON export backup valve.

## Scope

- `botsite/testing_store.py` — new `guide_exchanges` table + accessors,
  export coverage.
- `botsite/testing.py` — persist successful chat exchanges; thread the
  transcript into `_submission_ctx`, `_owner_page`, and the exit-review
  calls. The frame route stays write-free.
- `botsite/testing_ai.py` — optional untrusted transcript block in
  `grade_submission` / `regrade_with_followups`.
- Templates: owner queue + tester status page render the transcript;
  guide page discloses that typed chat is saved as evidence.
- `botsite/tests/test_testing_guide.py` — happy path + edges.

Results are filled at close-out.
