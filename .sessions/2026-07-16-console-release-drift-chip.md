# 2026-07-16 — Owner-console release-drift chip

> **Status:** `complete` — branch `claude/console-release-drift-chip`;
> #365's release-drift verdict extracted to a pure `app/release_drift.py`
> and reused by BOTH the healthcheck pass and a new glanceable drift chip on
> the gated `/owner/queue`. Read-only; +16 tests.

- **📊 Model:** Claude Opus · high · feature build (owner-queue release-drift chip)

**What this session is about:** promote #365's release-drift signal from
CI OUTPUT to the owner's glance. PR #365 shipped `check_release_drift()` —
every registry blocker joined to its askverify probe by exact `ask_id`,
drift FLAGGED — but only in the 6-hourly healthcheck log. This slice
surfaces the SAME verdict as a chip on the gated `/owner/queue`, beside
the existing askverify preflight chip: when an open ask probes
done-detected while the ledger/registry still gates it, the owner sees
"⚠ drift: done-detected but still gated" without reading CI. The drift
logic is extracted into a pure `app/release_drift.py` `classify()` that
BOTH `scripts/healthcheck.py` and the console call, so there is one source
of truth and no copied ladder. Read-only throughout: no new route, no
state change, no CSRF surface; the chip is omitted when there is no drift.

⚑ Self-initiated: no — coordinator-dispatched slice, promoted from PR
#365's close-out baton (`.sessions/2026-07-16-release-drift.md`, "Next
session should know": the owner-console release-drift chip reusing this
pass's exact ask_id join).

## Close-out

**Evidence:**

- files touched this branch: `app/release_drift.py` (new — pure
  `classify()` covering #365's full ladder: id-less / ledger-drift /
  done-gated / still-open / not-checkable / unknown, plus a `chip()`
  projection returning the owner-console badge only for a drifting open
  ask); `scripts/healthcheck.py` (its `check_release_drift()` per-row
  ladder now renders from `release_drift.classify()` — the printed lines
  are byte-identical, so #365's 10 tests stay green; import line +1);
  `app/owner.py` (`_render_owner_queue` attaches `item["drift"]` from the
  probe verdicts `askverify.annotate` already returned — no new fetch,
  gated view only, public `/queue` untouched); `app/templates/owner_queue.html`
  (drift chip `<span class="b warn">` beside the preflight chip, omitted
  when `it.drift` is None); `tests/test_release_drift.py` (+13 unit tests
  — every classify kind + every chip branch); `tests/test_owner_queue_drift.py`
  (+3 render tests — drift chip shown for a done-detected ask, omitted for
  a still-open ask, absent on public `/queue`); this card +
  `control/claims/console-release-drift-chip.md` (first commit; claim
  deleted at this flip).
- git: branch `claude/console-release-drift-chip` from `origin/main` @
  `16a116c` (#365); commits `297f68c` (born-red card + claim), `857d078`
  (helper + chip + tests), + this flip.
- verify: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — **1604 passed, 1 warning** (+16 vs main's 1588);
  `python3 bootstrap.py check --strict --session-log <this card>` — the
  only red during the session was the DESIGNED born-red hold on this card,
  released at this flip. The console chip was driven offline (askverify
  probes stubbed) — a done-detected ask renders the chip once, a still-open
  ask renders none.

**Judgment:**

- Decisions made: (1) the drift *classification* is the shared single
  source, not the presentation — the healthcheck renders a CI text line and
  the console renders a badge from the same `classify()` kind, so neither
  copies the ladder and each keeps its own idiom; (2) the console reads NO
  botsite registry data — `app/` never imports another service's package
  (the architecture rule), so the chip reuses the probe verdicts already on
  each open ask and treats the open ledger row as the live gate, which is
  the same drift #365 flags from the registry side (every registry blocker
  keyed to an open ask is gating); (3) the chip surfaces only the
  actionable done-gated drift — still-open / not-checkable / unknown show
  nothing, never inventing state; (4) independent of #368's "unblocks N
  cards" chip — different data, additive markup, so the two coexist.
- Next session should know: the shared classifier now exists, so the
  backlog's structured `drift_report()` renderer is half-built — the
  remaining half is a thin `rows()` projection over the same join (see the
  idea below); the botsite banner (the third surface) still waits on the
  #355 SIM-REQUEST answer.

## 💡 Session idea

**One structured `drift_report()` row list feeding all three surfaces.**
This slice extracts the drift *classification* into `app/release_drift.py`
and shares it between the healthcheck line renderer and the console chip,
but each caller still assembles its own presentation (a CI text line vs a
badge). A next step is the structured-row renderer #365's card already
named: `classify` returns the verdict, a thin `rows()` helper returns
`(registry, slug, ask_id, verdict, reason)` tuples, and the healthcheck
block, the console chip, and any future botsite banner all render from ONE
join instead of three. Deduped against `docs/ideas/backlog.md`: the
backlog entry names the shared renderer as an idea; this card records that
the classification half now exists, so the remaining half is just the row
projection. Captured for the backlog at flip.

## ⟲ Previous-session review

`.sessions/2026-07-15-walls-cards-heartbeat.md` (PR #346) was a docs-only
truing pass — walls ledger append, card `📊 Model:` grammar fixes, status
refresh — and it did the quiet groundwork this slice leans on: it taught
the `📊 Model:` line grammar that `bootstrap.py check` now lints, so this
card's model line was written compliant on the first pass instead of
tripping the advisory `model-line-effort` warning. One miss worth noting:
that card fixed fourteen 2026-07-14 cards' model lines but left the same
grammar undocumented in `docs/SKILLS.md`, so the next author re-derives it
from the lint message rather than a routed doc.
