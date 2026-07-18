# 2026-07-18 — Overview count badges → drill-downs + mobile legibility

> **Status:** `in-progress` — branch `claude/overview-mobile-ux`, PR **#[[fill:pr]]**.
> The owner tapped 7 times on `/fleet` count badges (`18 lanes`, `12 stale`,
> `9 outstanding orders`, …) that LOOKED tappable but had no handler, and long
> monospace values in the per-seat status cards clipped off the right edge on a
> phone. This session makes each count a real server-rendered drill-down to the
> lanes behind it, flattens the purely-informational pills so only drill-downs
> read as interactive, and wraps + contrast-bumps the mobile value/label cells.

- **📊 Model:** Claude Opus 4.8 · medium · feature build

**What this session is about:** `/fleet` (control-plane overview, live at
control-plane-production) renders a fleet-heartbeat card whose summary strip is a
row of count pills and, below, one status card per lane. Two owner problems:
(1) the count pills look like filters/buttons but do nothing — the owner wants to
tap `12 stale` and SEE WHICH lanes are stale; (2) at 480px the per-seat status
cards clip long values (heartbeat prose, `done=` lines, trigger IDs, branch/tool
names) behind a horizontal scrollbar, and the grey label column is hard to read.
Both are GET views — the CSRF/same-origin floor is untouched.

⚑ Self-initiated: no — coordinator-dispatched (owner-live UX ask).

## Close-out

**Evidence:**

- [[fill:evidence]]

**Judgment:**

- [[fill:judgment]]

## 💡 Session idea

[[fill:idea]]

## ⟲ Previous-session review

[[fill:review]]
