# 2026-07-10 — Never-idle work ladder + ideas backlog seed

> **Status:** `complete` — PR #61 (`claude/never-idle-work-ladder`), squash-merge on `quality` green.

- **📊 Model:** Claude Fable 5 · coordinator-dispatched upgrade job

**What this session was about:** close the perpetual-work-generation gap in
`docs/project/project-instructions.md` (PR #60 covered mechanics — orientation,
landing, routine-fired protocol, capabilities, heartbeat — but told a wake
NOTHING about what to do when `control/inbox.md` is dry and the queue-state
NEXT list is exhausted). The trigger prompt already delegates to the
instructions file, so fixing the instructions fixes every future fire; the
trigger itself was deliberately not touched.

## What was done

- **`docs/project/project-instructions.md`** — new `## Never idle — the work
  ladder` section after the routine-fired protocol: each wake picks the FIRST
  rung with work and ships ONE increment — (1) open ORDER at inbox HEAD,
  (2) queue-state NEXT list, (3) `docs/ideas/backlog.md` promotion (idea →
  small plan → first increment THIS wake), (4) self-generated contained +
  reversible improvement flagged `⚑ Self-initiated:`, (5) upkeep + an honest
  "backlog dry" heartbeat line (a routing signal to the manager). Two
  mandatory enders any wake/any rung: one genuine new idea per session
  (dedup first; honest "nothing" beats filler) and a one-line
  previous-session review. Never end a wake with nothing shipped unless
  blocked — then the heartbeat names the blocker. Grounding footer updated;
  file tightened to 6,991 chars (was 5,415; budget ~7,000).
- **`docs/ideas/backlog.md`** (new) — the single backlog list, seeded with 11
  captured/planned ideas already in the repo's record (card template w/ Model
  line + ender checklist; heartbeat enrichment incl. routine-state +
  landing-state lines; /fleet manifest-parse badge; PR #9
  `claude/rework-dashboard` salvage re-check; scheduled healthcheck cron;
  `?repo=` activity filter; kit-version rollup; unseen-orders badge;
  `/queue.json` round-trip; `wait-deploy.py`; ladder-rung telemetry), each
  with a one-line why + source citation, plus Built/Retired sections.
- **`docs/ideas/README.md`** — lifecycle normalized to `captured → planned →
  built → retired`, one-home-per-idea convention (bullet, or bullet + file),
  dedup rule; backlog listing moved to `backlog.md` (single home).
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests -q` —
  143 passed; `python3 bootstrap.py check --strict` green once this card
  flipped complete.

⚑ Self-initiated: no — coordinator-dispatched (owner intent: the Project keeps
working on any useful idea it can generate; never idle while useful work
exists).

## 💡 Session idea

**Ladder-rung telemetry in the heartbeat** — one `rung:` token per wake
recording which work-ladder rung fired (order / queue / backlog / self /
upkeep-dry). Worth having because the manager currently learns a lane's
backlog is dry only from a prose line in one heartbeat; a machine-readable
rung turns it into a trend (`/fleet` can badge lanes coasting on upkeep) and
shows whether a lane lives off orders or self-generated work. Deduped against
`docs/ideas/` + queue-state NEXT: heartbeat enrichment covers
orders/sha/routine/landing but not rung. Captured in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

The previous session (PR #60, Project env package) did the hard part well —
root-causing the 16:01Z landing failure with verbatim evidence and shipping a
paste-ready instructions file grounded line-by-line in repo sources. What it
missed is exactly this session's job: the instructions it wrote answer "how do
I land work" exhaustively but never "what work do I do when nothing is
queued" — a perpetual-motion Project needs the generation loop in the same
file as the mechanics. Workflow improvement: when writing doctrine meant to
run unattended, walk it through the emptiest possible wake (no order, no
queue, no idea) and check the text still produces an action.
