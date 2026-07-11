# 💡 Merge holds announced in a file at HEAD, not in session messages

- **Captured:** 2026-07-11, archive-prep capture session.
- **State:** `captured` (also bulleted in `backlog.md`).

## The idea

When a repo-wide merge hold is declared (e.g. protecting an owner-click PR's
green state), announce it in a file **at origin/main HEAD** — one
`control/claims/HOLD-<scope>.md` claim file created when the hold starts and
deleted when it lifts (or, weaker, a `hold:` line on the heartbeat). The
holder writes it; every other session's mandatory session-start pull sees it
mechanically before merging anything.

## Why it's worth having (measured failure, not vibes)

The 2026-07-11 hold protecting PR #141 was coordinated by messages between
live sessions — and failed twice: routine-fired 4-hourly wakes boot with
zero chat context, and **#143 and #146 were merged mid-hold** by sessions
that never saw the hold (PR #148's body records #141 knocked to
`mergeable_state: behind` by exactly those merges). Session messages reach
only sessions that exist when the message is sent; a file at HEAD reaches
every future session by construction — the same insight that makes
`control/claims/` work for work-claims. The claim checker's existing
parse/stale machinery could even nag on a stale HOLD file for free.

## Sketch

- `control/claims/HOLD-<scope>.md`, same one-file-per-claim convention
  (single bullet, backticked scope token, ISO date + a `lift-when:` line).
- Session ritual addition (one line in `control/README.md`): before merging
  ANY PR, `ls control/claims/` and respect `HOLD-*` files that name your
  target's surfaces.
- Routing half: this convention belongs to the kit/manager layer — flag it
  on the heartbeat so the fleet adopts one shape, not per-repo forks.

Source: `docs/retro/archive-ready-2026-07-11.md` §3 (the coordination
lesson this idea makes durable + routable).
