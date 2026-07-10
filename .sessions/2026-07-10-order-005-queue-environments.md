# 2026-07-10 — ORDER 005: /queue + /environments (+ ORDER 007 steps 3–5)

> **Status:** `in-progress`

- **📊 Model:** withheld per session policy
- **Start (UTC):** 2026-07-10T02:27:31Z

**What this session is about to do:** execute ORDER 005 (claimed on main via
fast-lane PR #52 — `claimed-by: 005 gen2-order-005 2026-07-10T02:24Z`): build the
control-plane **`/queue`** (owner to-do surface aggregating every lane's
⚑ needs-owner + `menno420/fleet-manager docs/owner-queue.md`) and
**`/environments`** (render `fleet-manager environments/` with copy-to-clipboard)
pages, both with honest degradation (GITHUB_TOKEN is UNSET in production — the
fleet-manager halves ship degraded by design; the ⚑ is already filed in
`docs/owner/OWNER-ACTIONS.md`). Plus ORDER 007 step 4 (`scripts/env-setup.sh`
wrapper) and step 5 (ledger flips). Tests for degraded + happy paths. Status
`done=` flip follows in a separate control fast-lane PR after live verification.
