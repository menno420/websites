# 2026-07-16 — Owner-console release-drift chip

> **Status:** `in-progress`

- **📊 Model:** Claude Opus · high · console-feature build (owner-queue release-drift chip)

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
