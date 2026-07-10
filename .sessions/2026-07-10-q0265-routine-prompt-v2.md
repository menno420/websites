# 2026-07-10 — routine-prompt v2 (Q-0265 continuous mode) + Q-0264 ladder escalation line

> **Status:** `in-progress`

📊 Model: claude-fable-5

## Declared at open (born-red)

Doctrine-fold worker dispatched by the fleet-manager coordinator (Q-0265
MANAGER-ONLY rider, superbot part-4 brief §2b). This PR:

1. `docs/project/routine-prompt.md` → **v2**: continuous-mode wake text (work
   loop up the ladder, ~15-min `send_later` continuation chain as pacemaker,
   this cron as failsafe/pacemaker fallback, backpressure brake, Q-0264
   idea-escalation, free-window posture) — supersedes v1's "one real slice per
   wake, no excessive work"; v1 kept below as history.
2. `docs/project/project-instructions.md`: Q-0264 escalation sentence at the
   end of ladder rung 3 (Idea Engine harvests `docs/ideas/` by link; sim-worthy
   ideas flagged to the manager via the heartbeat), file kept under 7,000 chars.

## Close-out

Landed as declared: routine-prompt.md restructured to Current text (v2,
continuous mode) + v1 kept verbatim as history; project-instructions.md rung 3
carries the Q-0264 escalation sentence (grounding comment trimmed to keep the
paste-file under 7,000 chars — 6,999 after edit). Owner action unchanged from
the file's convention: re-paste both into the claude.ai console (routine prompt
+ Custom Instructions) — source of truth is the repo file.

💡 Session idea: `docs/project/` paste-files now have a hard 7,000-char console
budget enforced only by hand-counting — a tiny `tests/` check asserting
`len(file) < 7000` for each paste-file would catch a budget-blowing edit at CI
time instead of at paste time. Dedup: not in `docs/ideas/backlog.md`.

⟲ Previous-session review: the routine-prompt-doc session (#63) rightly made
this file the single source of truth with a re-paste convention, which is
exactly what made this v2 upgrade a one-file edit — but it did not version the
prompt text; this PR adds the v1/v2 history convention so future prompt changes
keep their provenance.
