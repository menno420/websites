# Records true-up for final close

- **Status:** complete
- **📊 Model:** opus-4.8 · medium · docs-only
- **💡 Idea:** Records that point at a single closeout doc for the full picture stay small and current; the true-up job is to make each read-path record accurate to the final tip and route the reader to PROJECT-CLOSEOUT.md rather than re-narrate everything.
- **⟲ Previous-session review:** #472 (project-closeout) merged clean after the task-class was corrected to a valid PL-004 class and the flip dropped its claim in-commit; carrying named-path staging + the --added-card verify here.

## What
True up the read-path records to the final repo tip: refresh docs/current-state.md's header facts, reconcile docs/owner/OWNER-ACTIONS.md, and annotate docs/NEXT-TASKS.md + docs/plans/* to point at PROJECT-CLOSEOUT.md's Continuation section.

## Verify
- `unset DATABASE_URL; python3 bootstrap.py check --strict --added-card .sessions/2026-07-21-records-true-up.md`
