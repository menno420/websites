# 2026-07-10 — Routine prompt doc (third file of the Project package)

> **Status:** `complete`

- **📊 Model:** Fable (family-level per convention)

## What happened

- Added `docs/project/routine-prompt.md` — the paste-ready, self-contained
  wake-routine prompt for the claude.ai **Routines** screen, completing the
  Project package (setup-script.sh + project-instructions.md +
  routine-prompt.md). Repo file is the source of truth; re-paste after edits.
  The existing trigger's shorter delegating prompt remains a valid alternative.
- Listed the third file in `docs/project/README.md` (full-path backtick ref so
  the kit's reachability check sees it).
- Verified: `python3 -m pytest tests/ -q` → 85 passed;
  `python3 bootstrap.py check --strict` → clean (after fixing the orphan
  finding by using the full `docs/project/...` path in the README bullet).

## 💡 Session idea

**Console-copy drift stamps in `docs/project/README.md`** — add a
`pasted: <date> @ <short-sha>` line per console-copied file (setup script,
Custom Instructions, routine prompt), updated whenever the owner re-pastes.
Why it's worth having: the package's whole failure mode is silent drift
between the repo source-of-truth and the console copies; a stamp makes
"repo file changed since last paste — re-paste needed" mechanically
detectable by any wake, instead of relying on someone remembering.
(Dedup: backlog has heartbeat/status enrichment ideas but nothing about
console-copy drift.)

## ⟲ Previous-session review

The never-idle-work-ladder session (#61) did the high-leverage thing —
rung-ordered instructions plus a seeded backlog so "nothing to do" stopped
being possible — and cited sources per idea, which made dedup here trivial.
What it missed: the routine prompt that *invokes* the ladder still lived only
inside the trigger config, unversioned — exactly the console-copy drift class
the package exists to prevent; this session closes that gap. Workflow
improvement: when creating a package of paste-ready console texts, enumerate
every console field it must cover in one pass (setup script, instructions,
routine prompt, anything else) so the package ships complete instead of
accreting one file per session.
