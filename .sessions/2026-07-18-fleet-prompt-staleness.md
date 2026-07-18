# 2026-07-18 — Fleet prompt-state panel: snapshot-age warning + fleet-manager outbox asks

> **Status:** `in-progress` — branch `claude/fleet-prompt-staleness`, PR
> **#[[fill:pr]]**. Truth-in-labeling fix for the /owner "Prompt state" panel:
> the failsafe snapshot's `captured_at` is frozen upstream (fleet-manager
> telemetry, a manager-wake artifact) — the panel reads live and is correct,
> but a bare stale timestamp reads as our bug. Adding the snapshot AGE + a
> `>24h stale, awaiting an upstream refresh` warning that attributes the freeze
> upstream; plus drafting the 4 cross-repo fleet-manager asks that fix the
> underlying data.

- **📊 Model:** [[fill:model]]

**What this session is about:** the /owner console "Prompt state" panel
(`app/owner.py` `owner_board` → `prompts.console_rollup` → the drift-row model)
renders the fleet-manager `telemetry/triggers-snapshot.json` failsafe snapshot
LIVE over raw. That snapshot only refreshes on a manager-seat wake (an MCP-only
`list_triggers` dump); with the manager seat parked it froze at
`2026-07-17T16:32:25Z` (>24h). Our panel is CORRECT — it reads live and honest.
What we improve here is truth-in-labeling: make the staleness unmistakable and
clearly ATTRIBUTED upstream so it is not misread as a Websites bug, and route
the actual data fix cross-repo via our outbox. Rung: coordinator-dispatched
UX + cross-repo remediation (decide-and-flag, fully reversible — code + control
docs only).

## Plan

- **Part A (code):** compute the snapshot age from `captured_at` against an
  injectable `now` (the repo's `app.clock` discipline — never naive wall-clock),
  expose `age_hours` / `age_human` / `is_stale` on the console rollup's snapshot,
  and render in `owner.html` the age (e.g. "(30h ago)") plus, past 24h, a
  warning banner attributing the freeze upstream (mirrors fleet-manager's own
  roster-regen >24h warning). Deterministic test (pinned clock): stale renders
  the warning, fresh does not.
- **Part B (control):** append 4 cross-repo asks to `control/outbox.md`
  (lane→manager channel) for menno420/fleet-manager to action: (1) refresh the
  frozen triggers snapshot + arm the documented CCR fallback routine; (2) update
  `projects/websites/meta.md` Deployed-state table to the current v3.7 paste;
  (3) optional stub-table note for superbot-world / superbot-2.0; (4) a
  self-healing per-seat "stamp deployed prompt version at session-ender" rule.

## What was done

- [[fill:done]]

⚑ Self-initiated: no — coordinator-dispatched (fleet-prompt-state remediation).

## 💡 Session idea

[[fill:idea]]

## ⟲ Previous-session review

[[fill:review]]
