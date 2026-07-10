---
state: built
origin: consumer:menno420/superbot
shipped_pr: null
shipped_repo: null
merged_date: null
outcome: open
---

# Scheduled healthcheck workflow — standing liveness verification (2026-07-10)

> **Status:** `ideas`
>
> **State:** built — shipped 2026-07-10 as `.github/workflows/healthcheck.yml`
> (continuous-mode wake slice 3; decision stamped in the decision ledger).

**One line:** a cron GitHub Actions workflow (e.g. every 6 h) that runs the repo's own
`scripts/healthcheck.py` against the three live services and fails loudly on any non-200
— turning liveness from a thing a session remembers to probe into a thing the repo
verifies on its own clock.

**Why:** the gen-1 final retro handed over with "liveness unverified at handover — a
successor should run healthcheck.py before trusting liveness," and the grand-review
session had to close that flag manually (2026-07-10 01:02Z probe: all three 200/PASS,
including the dashboard that had real build failures at 03:46Z the same day). The A3
finding (a `/fleet` parse degrading silently to fallback with no alert) is the same
class: silent degradation needs a scheduled observer, and no platform scheduler exists
for sessions (retro F3) — but Actions cron does exist and is the one scheduler agents
can arm themselves.

**First step:** one workflow file (cron + workflow_dispatch), non-required, notifying
via the failed-run email the owner already receives. Optionally append a
last-checked line to a committed badge file later — keep step 1 read-only.

**Size:** small (one workflow file).
