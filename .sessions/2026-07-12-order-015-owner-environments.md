# 2026-07-12 — /owner/environments: gated live-env-visibility page (ORDER 015 slice)

> **Status:** `complete` — branch `claude/order-015-owner-environments`,
> PR #166 (parks READY awaiting the owner's merge click — no auto-merge on
> this repo).

- **📊 Model:** claude-fable-5 · worker (ORDER 015 execution) · feature-build

**What this session was about:** Execute the merged plan
`docs/planning/live-env-visibility-plan-2026-07-11.md` (slice 1) under
ORDER 015 ("find all website related plans across the multiple repos and
execute all the important ones" — filed on PR #160's branch
`claude/order-012-records-reconcile`, provenance: owner live directive
2026-07-12): a password-gated `/owner/environments` page on the
control-plane that shows each service's environment surface, reads live
variable NAMES from Railway via a project-scoped `RAILWAY_TOKEN` when one
is configured, and degrades honestly while that owner errand is pending.
Rung: order (ORDER 015).

## What was done

- `app/railway.py` (new) — committed per-service facts (`SERVICES`: the
  three deployed Railway services with package / Dockerfile / URL and each
  service's documented env-var NAMES + purpose + prefix-matched "manage →"
  console deep links) and a read-only Railway GraphQL layer keyed on a
  PROJECT-SCOPED `RAILWAY_TOKEN` — plan option (A): names + presence only,
  values dropped at the client boundary (`_names_only`); TTL cache mirroring
  `app/github.py`; honest `not-configured` (owner errand pending) /
  `unavailable` degradation; no mutation strings; never reads the ambient
  production IDs (`scripts/check_no_ambient_railway_ids.py` stays green).
- `app/owner.py` — `GET /owner/environments` behind the existing
  `require_owner` gate (read-only; the ORDER 013 CSRF hardening is for
  POSTs) + the `manage_link` template filter. `app/config.py` —
  `RAILWAY_TOKEN` (documented: project-scoped, never the account key).
- `app/templates/owner_environments.html` — live section (banner per
  degraded state; names + manage links when live) + one committed-facts
  card per service with a presence column (control-plane: set/unset from
  its own runtime, presence only; siblings: honest "needs live Railway
  read").
- `tests/test_owner_environments.py` (+8) — gate 401/503, degraded
  no-token owner-errand state, live names-render/VALUES-NEVER (HTML and
  snapshot dict), unavailable degradation with the exact reason,
  presence-only runtime column, manage-link prefix map.
- Docs: `docs/site.md` (owner-area route bullet + `RAILWAY_TOKEN` env row +
  the "deliberately NOT wired" paragraph now names the one read-only
  exception), `docs/RAILWAY-SAFETY.md` (the exception, scoped + read-only),
  `docs/CAPABILITIES.md` (RAILWAY_TOKEN wall finding per the discovery
  rule), `docs/ideas/backlog.md` (idea below).
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — **362 passed** (was 354); `python3 bootstrap.py check
  --strict` — green (only the designed born-red hold before this flip);
  `python3 scripts/check_no_ambient_railway_ids.py` — OK.

⚑ Self-initiated: no — ORDER 015 + the owner-directed plan doc
(`docs/planning/live-env-visibility-plan-2026-07-11.md`).

⚑ Needs-owner (existing ask, unchanged by this PR): mint the
project-scoped `RAILWAY_TOKEN` (superbot-websites) and set it on the
control-plane service — the page's live half stays honestly degraded until
then, and the GraphQL query shape is UNVERIFIED against the real API until
a token exists.

## 💡 Session idea

**/owner/environments drift check: documented vs live variable names** —
once the token lands the page holds both halves of a diff it does not yet
compute (committed documented names vs live Railway names); one comparison
column (documented-but-unset / set-but-undocumented badges) turns two lists
into a drift detector like the board's deploy-drift cell. Worth having
because undocumented live variables are invisible config debt and
documented-but-missing ones are outage foot-guns. Deduped against
`docs/ideas/backlog.md` + the queue-state NEXT list: nothing touches
env-var drift. Captured in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

The projects-dispatch session (#158) validated package names against the
live registry before fetching and render-verified via TestClient — both
imitated here (values-never asserted on the emitted HTML); what it missed:
nothing structural for this task — but its card's claim-file ritual
(`control/claims/`) could not be followed here since this worker is barred
from `control/**` writes; flagged so the coordinator can reconcile claims.
