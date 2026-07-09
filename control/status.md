# Fleet control — builder status

> **Status:** `builder-status`
>
> Canonical progress record for the **websites** Project builder. The owner talks
> to a manager Project, not to the builder directly; they coordinate through
> committed files under `control/`. The manager writes orders to `control/inbox.md`
> (builder **never** edits it); the builder reports progress **only** here.
> Overwrite this file every session.

## Timestamp
2026-07-09 (session)

## Phase
Websites improvement/hardening pass — post-launch.

## Health
- **control-plane** — 🟢 GREEN (live)
- **botsite** — 🟢 GREEN (live)
- **dashboard** — 🟢 GREEN (live)

3 live services; last verified **6/6 endpoints returned HTTP 200**.

> Note: superbot-next `report/golden-parity` is **red-BY-DESIGN** — it is a parity
> tracker that is intentionally red until parity closes, **not** a broken build.

## Last-shipped PR
- **#21** — Botsite content depth: per-command detail pages + enriched changelog (merged, `d839710`).

Recent merges:
- **#20** — Hardening + verification batch: Railway-ID guard, stub labels, healthcheck, OWNER-ACTIONS.
- **#18** — Journal browser: sanitized markdown render + cross-repo search; mobile polish.
- **#14 / #15** — `/owner` area.

## In flight
- Born-red **session-gate fix** — re-vendoring kit-HEAD bootstrap + `adopt --wire-enforcement`
  to close two holes (PR pending). A separate worker is finishing it **this session**.

## Blockers
- None currently.
- Environment note: no scheduling primitive (`send_later`) available in the sandbox.
- Environment note: the CI gate can't be set **required** via API from the sandbox —
  owner set it manually (**done**; see OWNER-ACTIONS row A).

## Orders acked / done
- **Acked** the fleet-coordination protocol adoption — this status write confirms adoption.
- `control/inbox.md` currently **does not exist** (no `new` orders to dispatch).

## ⚑ needs-owner
Open OWNER ACTIONS (`docs/owner/OWNER-ACTIONS.md`):
1. Dashboard `/admin` live-bot control — build/wire vs. keep labeled stub.
2. Botsite `/submit` — provision submissions Postgres + moderation mirror vs. keep stub.
3. Redeploy-from-browser scoped Railway deploy hook — yes/no.
4. Custom domains for the three sites (deferred to cutover).
5. Preserve v1 visual design vs. the shipped restyle.
6. OLD-site cutover / retirement in superbot — go/no-go.

**⚑ Contract file absent:** `control/README.md` does **not** exist in the repo. The
fleet-coordination contract (expected format/sections for `status.md` and `inbox.md`,
order status values, cadence) has not been committed. This `status.md` uses a sensible
default format pending the contract. Owner/manager: please add `control/README.md`.
