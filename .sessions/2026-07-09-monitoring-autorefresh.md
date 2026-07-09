# 2026-07-09 — auto-refresh the live-monitoring pages (/fleet + board /)

> **Status:** `in-progress` — born-red session card; flips to `complete` as the final step.

- **📊 Model:** Opus 4.8 · worker · monitoring-autorefresh

**What this session is doing:** self-directed improvement on the control-plane
site. (A) Verify the `quality` CI job actually runs the full test suite on a
normal PR (a recent run finished in ~17s — confirm it is not short-circuiting).
(B) Add unobtrusive client-side **auto-refresh** to the two live-monitoring
surfaces — `/fleet` and the board `/` — so the owner's single control glance
stays current without a manual reload; content/journal pages stay static.

## What is being done (fill in as it lands)

- TASK A — audit `quality.yml` against real run logs.
- TASK B — auto-refresh on `/fleet` + `/`: a small vanilla-JS soft in-place
  refresh, visible indicator + pause toggle, config-driven interval.

_(Details, verification, session enders, and Status flip added before the final push.)_
