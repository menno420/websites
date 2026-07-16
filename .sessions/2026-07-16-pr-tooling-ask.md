# 2026-07-16 — failsafe-wake: heartbeat true-up + PR-tooling wall filed as ASK-0017

> **Status:** `complete` — branch `claude/pr-tooling-ask-20260716`; docs-only
> slice: files the org-level GitHub-App-not-connected wall as an owner ask
> and logs the sharper evidence in `docs/CAPABILITIES.md`.

- **📊 Model:** Claude Sonnet 5 · medium · docs-only

**What this session is about:** two consecutive failsafe wakes for this
project (2026-07-16, ~20:49Z and this one) found the work-loop chain dark
and, on the first, tried to land a trued `control/status.md` heartbeat by
pushing `claude/failsafe-heartbeat-20260716-2049` — landing failed twice:
this session has no GitHub API/PR-creation tooling (`add_repo` grants
repo-scope but the org's Claude GitHub App itself isn't connected — a 403
distinct from the already-documented 2026-07-10 per-repo wall), and a
direct `git push` to `main` was correctly rejected by branch protection
(GH013: PR + passing "quality" check required). Three branches are now
sitting pushed-unmerged for that reason: `claude/failsafe-heartbeat-20260716-2049`,
`claude/arcade-catalog-blockers`, `claude/games-availability-summary`. This
session files the root cause as **ASK-0017** in `docs/owner/OWNER-ACTIONS.md`
(connect the GitHub App, org-admin, one-time) and logs the sharper
evidence trail in `docs/CAPABILITIES.md` so future sessions don't re-attempt
`add_repo` expecting it to fix PR creation.

⚑ Self-initiated: yes — no new inbox order since #031, NEXT-2-TASKS baton
was empty, this is the next-highest-leverage fix on the board (it blocks
landing of three already-built branches, not just this one).

## Close-out

**Evidence:**

- files this branch: `docs/owner/OWNER-ACTIONS.md` (new `ASK-0017` six-field
  block), `docs/CAPABILITIES.md` (new 2026-07-16 wall entry with the
  verbatim 403 + GH013 errors), this session card.
- git: branch `claude/pr-tooling-ask-20260716`, based on `origin/main` @
  `da63857`.
- verify: `python3 bootstrap.py check --strict` — all checks passed. The
  four-service pytest suite was NOT runnable this session — a fresh clone
  with no `pip install` done (`ModuleNotFoundError: No module named
  'fastapi'` on collection); irrelevant here since the diff touches no
  Python.

**Judgment:**

- Decisions made: filed the wall as an owner ask rather than trying another
  in-session workaround — the 2026-07-10 CAPABILITIES entry already
  establishes there is none (push-and-leave is the correct move); the
  20:49Z heartbeat's `notes:` line already said as much, this just gives
  it a proper six-field ask so it surfaces on `/owner/queue` and the
  askverify join instead of living only in a status-line aside.
- What I did NOT do: did not touch the two pending feature branches
  (`arcade-catalog-blockers`, `games-availability-summary`) — their own
  session cards already say `complete` and their claims are already
  deleted; nothing left for this lane to do there but wait for landing.
- Landing: same wall as the 20:49Z heartbeat — pushed, cannot open a PR
  from this session. Left for an interactive session or the owner.

**Handoff:** next session — check whether ASK-0017 is Decided (GitHub App
connected); if so, this is probably the fastest lane to open PRs for all
four pending branches (this one, the two feature branches, and the
20:49Z heartbeat) in one pass. If not yet decided, pick fresh self-initiated
work; the baton is empty.

## 💡 Session idea

**Owner console "stuck landing" chip** — a `/owner/queue` chip listing
branches pushed-unmerged behind the PR-creation wall (ASK-0017), the same
glanceable pattern as the unblocks-N-cards and release-drift chips.
Worth having because the wall is structural and will keep recreating
pushed-unmerged branches until ASK-0017 is decided; a chip beats reading
every session's status.md prose to find them. Deduped against
`docs/ideas/backlog.md`: no existing idea reads branch-vs-main ancestry
state. Captured in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

The 20:49Z failsafe-wake heartbeat did the hard part well — it dug past a
misleading peer-session claim into real git evidence (empty claims dir,
dead trigger set, stale status.md) before concluding stalled, and it left
an honest, specific `landing:`/notes trail instead of fabricating a
merge. What it missed: it treated the PR-creation wall as this session's
problem to note in prose rather than routing it to the owner as a proper
ASK — this session's whole job was closing that gap.
