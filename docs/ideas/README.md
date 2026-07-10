# websites — idea backlog & lifecycle

> **Status:** `ideas`
>
> Capture ideas here so they live in the repo, not in chat. Nothing here is
> approved until it graduates. A **conveyor, not a graveyard**: every idea ends
> built, planned onto a queue, or explicitly retired — never orphaned.

## Where ideas live

- **The list is [`backlog.md`](backlog.md)** — one bullet per idea, each with a
  state, a one-line why, and its source citation.
- A substantial idea additionally gets **one file** in this directory
  (`<slug>-<date>.md`) with the fuller shape; the backlog bullet links it.
- **One home per idea**: either a bullet alone or bullet + file — never two
  competing writeups.

## Lifecycle

```
captured  -> the idea is in backlog.md with a why + source
planned   -> it has a small plan (or a queue-state NEXT slot) naming the first increment
built     -> merged; move the bullet to "Built" with the PR/ledger pointer
retired   -> deliberately not doing it; keep the bullet + one line of why
```

The work ladder (`docs/project/project-instructions.md` § Never idle) makes
this backlog rung 3: when the inbox and the queue-state NEXT list are dry,
promote the highest-value buildable idea — idea → small plan → build the first
increment the same wake.

## Dedup rule

Before adding an idea, grep `backlog.md` + this directory + the newest
queue-state NEXT list for the same concept (and its 1–2 nearest synonyms). A
duplicate strengthens the existing bullet (add your source) instead of adding a
new one. Forced filler is worse than none: the one-idea-per-session ender
accepts an honest "nothing genuine today, because X".
