# 2026-07-17 — Self-cleaning owner queue (C14)

> **Status:** `complete` — branch `claude/self-cleaning-owner-queue`; the gated
> `/owner/queue` now auto-clears an open ⚑ owner-action into a separate
> "self-cleaned this pass" section the moment `app/askverify.py` POSITIVELY
> re-verifies its underlying condition resolved (the done-detected rung only).
> Fail-soft: still-open / unknown / probe-error / exception / ambiguous /
> unreachable all keep the ask active. Public `/queue` untouched. +8 tests.

- **📊 Model:** Claude Opus · high · feature build (self-cleaning owner queue)

**What this session is about:** the launch-preflight machinery
(`app/askverify.py`, 2026-07-15) already probes each open owner-action and
attaches a read-only verdict chip — `done-detected` / `still-open` /
`not-machine-checkable` / `unknown`. But a `done-detected` ask still sat in the
gated `/owner/queue` nagging: the probe knew the condition was resolved, yet the
queue never shrank. C14 (console menu **C14**, NEXT-TASKS §1 · P1) closes that
loop — a positively re-verified ask auto-clears into a separate "self-cleaned
this pass — ledger update pending" section, out of the active nag list, so the
queue shrinks itself and less owner attention is burned.

⚑ Self-initiated: no — coordinator-dispatched backlog slice (C14) of the standing
overnight ORDER 032.

## Close-out

**Evidence:**

- files touched this branch: `app/askverify.py` (`annotate()` stamps each item
  `auto_cleared` True ONLY on the positive `DONE` rung, adds `rollup["auto_cleared"]`,
  and a new `split_self_cleaned(items) -> (active, cleared)` helper — the
  probe/registry machinery is untouched, not rewritten); `app/owner.py`
  (`_render_owner_queue` splits the annotated items into `active_items` /
  `auto_cleared_items`, gated view only); `app/templates/owner_queue.html` (main
  loop iterates the active asks; a new dim "self-cleaned this pass" section lists
  the cleared ones with their done-detected chip + a kept mark-complete form, and
  the header gains a "· N self-cleaned" count); `tests/test_askverify.py` (+8:
  the four C14 cases — positive-resolved auto-clears, still-open stays,
  fetch-error stays, raised-exception stays — plus ambiguous/not-checkable stay,
  the order-preserving split, the un-annotated-item guard, and a gated-render
  test that a resolved ask moves to the self-cleaned section while a still-open
  one stays active; two exact-rollup pins updated for the new key); this card +
  `control/claims/self-cleaning-owner-queue.md` (first commit; claim retired at
  the successor session) + `control/status.md` heartbeat.
- git: branch `claude/self-cleaning-owner-queue` from `origin/main` @ `f21bbdf`
  (#385); commits `f4709ea` (born-red card), `095e8d1` (build + tests),
  `9da0ca8` (heartbeat status + claim), + this flip.
- verify: `python3 -m pytest tests/ botsite/tests dashboard/tests review/tests
  -q` — **1725 passed, 1 warning**; `python3 bootstrap.py check --strict` (and
  `--require-session-log`, the CI form) — the only red during the session was the
  DESIGNED born-red hold on this card, released at this flip; the two
  `/queue.json` + `/fleet.json` contract pins stayed green (no serialized JSON
  payload changed — the public overview is byte-identical).

**Judgment:**

- Decisions made: (1) the fail-soft invariant is encoded at one point —
  `item["auto_cleared"] = v["verdict"] == DONE` — so ONLY a positive probe
  observation clears an ask; every other rung (still-open, not-machine-checkable,
  the claim-once ambiguity, unknown, a fetch error, a timeout, a raised probe
  exception) leaves the ask active by construction, and `test_self_cleaning_*`
  pins each of those paths; (2) the self-clean is a RENDER concern on the gated
  console only — `annotate()` just adds a flag, so the public `/queue` (which
  never calls askverify) and its contract pin are untouched; (3) a self-cleaned
  ask keeps its done-detected chip ("ledger update pending") and its mark-complete
  form, because the probe observes the world while the human ledger row is still
  the record to move — the queue shrinks the NAG, it does not silently close the
  ledger; (4) reused the existing chip/card idiom and CSS, no new route, no state
  change, the CSRF/same-origin writeback floor untouched.
- Next session should know: the done-detected verdict now drives a real
  queue-shrinking behaviour, not just a chip — the natural follow-on is the idea
  below (auto-draft the ledger move on self-clean) and C15 (durable ask IDs,
  already partly in place via `ASK-NNNN`).

## 💡 Session idea

**Auto-draft the ledger mark-complete when an ask self-cleans.** The moment
askverify flags an ask `auto_cleared` (done-detected), pre-fill a writeback
"mark complete" DRAFT (draft-only, the owner still approves) citing the probe's
evidence line + URL, so moving the human ledger row is one approve-click instead
of a retype — closing the exact "ledger update pending" gap the chip names.
Reuses the `owner_assist` draft machinery already wired into `/owner/queue`; the
self-cleaned section is the obvious home for the pre-filled draft. Captured for
the backlog at flip.

## ⟲ Previous-session review

`.sessions/2026-07-16-console-dispatch-readiness.md` surfaced already-computed
coverage data (`pkg.coverage`) on the dispatch screen where the owner acts —
reuse of a signal, no new fetch. This C14 slice extends that exact discipline:
the askverify verdict was already computed for the chip; C14 now ACTS on it to
shrink the queue, still with zero new network surface. Same miss carries over,
worth flagging: neither card threaded its "reuse a computed signal where the
owner acts" pattern into `docs/SKILLS.md`, so the next author re-derives it
per-page rather than from one routed recipe.
