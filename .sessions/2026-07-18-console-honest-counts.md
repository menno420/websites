# 2026-07-18 — Console honest counts (C1)

> **Status:** `in-progress` — branch `claude/console-honest-counts`; the
> `/work`, `/history`, `/console` category landing pages now render a FAILED
> count distinctly from a genuine `0`. Four under-guarded `_count_*` helpers
> in `app/main.py` used to report a fetch-failure as a faked `0`; they now
> return `None` (the template's honest `—` marker) whenever the source signals
> the count could not be honestly computed, while a real `0` still renders as
> `0`.

**What this session is about:** the IA v2 category landing pages (`/work`,
`/history`, `/console`) decorate each subcategory row with a live count chip.
The template already renders `None` as an honest `—` and an int as the number,
but four of the eight `_count_*` providers (`queue`, `orders`, `ideas`,
`activity`) trusted their source's roll-up unconditionally — so a fetch failure
that zeroed the roll-up rendered as a misleading `0` (a lie: "0 open" when the
truth is "unknown"). C1 (backlog) closes that: a failed counter renders `—`,
distinct from a genuine `0`. Additive, read-only GET render — no state-changing
route, no CSRF/Origin surface, no new credential, no serialized JSON payload.

⚑ Self-initiated: no — coordinator-dispatched backlog slice (C1).

## Close-out

**Evidence:**

[[fill: files touched, git commits, verify output — filled at flip]]

**Judgment:**

[[fill: decisions + what the next session should know — filled at flip]]

## 💡 Session idea

[[fill: one idea you genuinely believe in — filled at flip]]

## ⟲ Previous-session review

[[fill: one-line remark on the previous card — filled at flip]]
