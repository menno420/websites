# Continuous-mode chain lessons — 2026-07-10/11 (websites lane)

> **Status:** `audit` — durable record of the transferable lessons from the
> Q-0265 continuous-mode chain (35 slices #64→#148 + 3 rescues, one
> send_later nudge chain, 2026-07-10 20:00Z → 2026-07-11 ~19:40Z). These
> lived only in chat reports and overwritten heartbeats; archived here at
> the owner-ordered close-out so no lesson depends on a session transcript.
> Per-slice detail: `.sessions/` cards; running facts: `docs/current-state.md`
> chain entry; owner items: `docs/owner/OWNER-ACTIONS.md`.

## 1 · Fired-session reliability watch (final record)

The self-armed 4-hourly wake (`trig_017H9Qb9oxtLgUy6sw2gnSHg`, ORDER 008)
fired four observable windows on 2026-07-11:

| slot | outcome | evidence |
|---|---|---|
| 04:03Z | ran, ritual-only, heartbeat STRANDED → relayed | rescue #98 |
| 08:00Z | SILENT (no trace ever) | slices 19–20 rituals |
| 12:05Z | ran, ritual-only, heartbeat STRANDED → relayed | rescue #124 |
| 16:00Z | SILENT (no trace at +18 min or later) | slice 32 ritual |

**Verdict:** 2 stranded-relayed / 2 silent — routine-fired sessions are
honest workers but unreliable landers (often no PR tooling: `tooling:
ritual-only`). The containment that worked: the relay doctrine
(`control/README.md` § landing others' control-only work) + the
`tooling:`/`landing:` heartbeat tokens — a foreign fired session dogfooded
all three unprompted at 12:05Z and its work landed within minutes. The
failure mode is contained, not fixed; a send_later chain remained the
lane's only consistent producer.

## 2 · The cron-correction saga (how a wrong verdict propagated, twice)

Two separate wrong-time claims this chain made and later corrected:

- **Cron arithmetic (fixed at #96):** `17 */6 * * *` anchors to wall-clock
  hours 00/06/12/18 — five consecutive heartbeats said "~02:17Z" before
  the self-catch. Pin: `scripts/cron_slots.py` carries the incident test.
- **"Never delivered" (corrected 18:2xZ):** heartbeats #134–#144 declared
  the 12:17Z healthcheck slot "never delivered / longest gap" and armed a
  schedule-drop flag — but run 4 was `event: schedule`, created 13:52:38Z,
  success (~95 min late). The listing checked at 14:03Z did not show a run
  created 13:52Z (API lag or misread); the verdict then propagated through
  five heartbeats by inheritance.

**Lessons:** (a) GitHub Actions cron is best-effort with 0–2h observed lag
— never gate on a slot, never call a single slot missed until >2h past;
(b) a wrong claim in a heartbeat propagates by INHERITANCE — each
overwrite copies watches forward — so re-verify a carried claim against
the source when it becomes decision-relevant, not just when first made.
Final cron record: 4/4 scheduled slots delivered, all success.

## 3 · Build-and-hold under a merge freeze (and the idle-pass miss)

When the #141 owner-click hold froze merging (~16:4x–19:2xZ), this chain
idled two full passes before the manager's clarification: **the hold
blocked only the LAST ceremony step.** The correction that then worked:
branch → build → push → READY PR (hold banner + held-list position in the
body) → flip → drive quality green → wait unmerged; report carries the
held list because landing the heartbeat is itself a merge. Two slices
(#147, #148) shipped this way and landed in order on the lift, exactly as
queued (one planned backlog reconciliation at land time).

**Lesson:** when a constraint blocks one step of a ceremony, run the
ceremony up to that step — an idle pass under a partial constraint wastes
the window.

## 4 · Guard-quality patterns that repaid themselves same-day

- **Time discipline:** the 08:45Z wall-clock time-bomb (fixture stamps
  aging through `fleet.overview()`) → defuse (#111) → class-wide AST guard
  (#114, 17 latent sites found) → single clock read + route-level freeze
  (#130) with a source guard. Wrong-by-construction beats wrong-caught.
- **Prototype-then-pin:** driving the real CLI in a scratchpad before
  writing `tests/test_control_gates.py` (#127) surfaced a FIFTH gate lane
  (`[inbox-order-grammar]`) the port-time hand-validation missed.
- **Guards must not carry their own failure mode:** two self-referential
  drifts found in guards (nav markup/tuple duplication #122; the membership
  scan's hand-kept module list #137); a sweep then proved the class clear
  (#142). Hand-kept lists rot precisely where drift hurts most.
- **Consumer-first protocol rollout:** ship the parser before the
  convention has writers (tooling:/landing: tokens #67 → first foreign
  writer same-day; pickup history #148 → seeded by this chain's own
  catch-up heartbeat as writer #1, live-verified).
- **Premise-check before capturing an idea:** 20-second greps killed two
  false premises (dashboard nav already manifest-driven; botsite/dashboard
  have no wall-clock reads) before they became backlog noise.

## 5 · Coordination mechanics that held (35 slices, zero collisions)

- Claim-first + born-red-first-commit + flip-after-real-PR-number: no
  double-builds across ≥5 concurrent sessions.
- The stranded-work protocol's BOTH clauses are load-bearing: rescue what
  is stranded (#94, #98, #124), and check-don't-assume for what is not
  (#132, #141, #143, #145 were all active, never touched); #147's NO-DIFF
  classifier now automates the noisiest false-alarm class.
- Manager-brokered file boundaries (the #141 hands-off list) beat
  discovery-time conflict resolution — the one mid-slice sibling merge
  (#132) absorbed cleanly through a routine 405 + branch update.
- 405 "branch not up-to-date" is the normal cost of parallel lanes
  (~6 occurrences): merge origin/main, re-green, merge — never force.

## 6 · Standing state at park (2026-07-11 ~19:40Z)

- Owner items: PR #141 click (+branch update; watchdog session keeps it
  fresh), botsite DATABASE_URL, control-plane GITHUB_TOKEN, review/
  Railway service, branch prune list — all click-level in
  `docs/owner/OWNER-ACTIONS.md`.
- Manager asks on the bus: lanes.json; meta.md convention;
  provenance-token convention to the kit lane; review-queue rows owed;
  pickup-persistence convention (consumer live, writer #1 seeded).
- Backlog: buildable-now empty; Q-0264 candidates catalogued in
  `docs/ideas/backlog.md`.
