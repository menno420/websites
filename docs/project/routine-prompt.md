# websites — wake routine prompt (paste-ready)

> **Status:** `reference`

Paste the block below as the wake routine's prompt in the claude.ai Routines
screen — or keep the existing trigger's shorter delegating prompt; this is the
full self-contained version. Source of truth is THIS file — re-paste after
edits.

## Current text (v2, 2026-07-10 — continuous mode, Q-0265; the one to paste)

Supersedes v1's "one real slice per wake, no excessive work" pacing per owner
directive Q-0265 (superbot router, 2026-07-10; folded by the fleet manager per
the part-4 brief §2b rider).

```
WAKE (websites lane, continuous mode — Q-0265): sync menno420/websites to origin/main HEAD and read control/inbox.md at HEAD. Then WORK IN A LOOP up the ladder (docs/project/project-instructions.md § Never idle): open ORDER → queue-state NEXT → docs/ideas/backlog.md (promote the best idea and build its first increment) → ⚑ Self-initiated improvement → honest "backlog dry" upkeep. Each slice is its own branch + born-red card + PR ready + squash-merge on green `quality`; when a slice lands and useful work remains, take the NEXT slice in the same session — the throttle is removed, not the ceremony. Before ending the turn: if useful work remains and your toolset has send_later, arm it ~15 minutes out ("continue the websites work loop") and say so on the card; if the tool is absent, record that verbatim — this cron is then your pacemaker. Truth rules unchanged: trust the setup-script probe; never record "pushed" without git ls-remote proof; a patch to the owner is the last resort and needs the verbatim probe error. Substantial or sim-worthy ideas don't terminate locally: file them in docs/ideas/ (the Idea Engine harvests by link) and flag sim-worthy questions to the manager in your heartbeat (Q-0264). Session enders: one genuine new idea (dedup first; none beats filler), one-line previous-wake review, family-level 📊 Model line. Overwrite control/status.md as the deliberate last step. Backpressure, not the clock, is the brake; free-window posture through 2026-07-14 is MORE work, not less (Q-0265).
```

## v1 (2026-07-10 — SUPERSEDED by v2 above, kept verbatim for history)

```
4-HOURLY WAKE (websites lane): sync menno420/websites to origin/main HEAD and read control/inbox.md at HEAD. Then ONE bounded pass up the work ladder (docs/project/project-instructions.md § Never idle): open ORDER → queue-state NEXT list → docs/ideas/backlog.md (promote the highest-value buildable idea and build its FIRST increment this wake) → self-initiated contained+reversible improvement (flag ⚑ Self-initiated on the card) → only if all rungs are empty, docs/test upkeep plus an honest "backlog dry" heartbeat line. Ship a real merged increment: branch + born-red session card + PR ready + squash-merge on green `quality`. Trust the setup script's capability probe; never record "pushed" without git ls-remote proof — if landing tools are dead this session, commit locally, record the branch + exact verified state on the card AND in control/status.md, and leave landing to the next tooled session (a patch to the owner is the last resort and needs the verbatim probe error). Session enders: one genuine new idea into docs/ideas/ (dedup first; none is better than filler), a one-line previous-wake review, and the family-level 📊 Model line on the card. Overwrite control/status.md as the deliberate last step. One real slice per wake, no excessive work — the ladder guarantees there is always a next slice. If this trigger turns out to be one-shot rather than recurring, re-arm it for +240 minutes before ending the turn.
```
