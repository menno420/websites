# 2026-07-11 — open_work.py: content-diff classification (rung 4, build-and-hold)

> **Status:** `in-progress` — branch `claude/open-work-content-diff`; flips
> to `complete` + the real PR number after the PR exists. BUILT UNDER THE
> #141 MERGE HOLD: this PR goes READY + green and WAITS UNMERGED for the
> hold-lift relay.

- **📊 Model:** claude-fable-5 · worker · routine-fired build slice (continuous mode, slice 33 — post-18:13Z pass under the build-not-merge clarification) — family from this session's own harness, per ORDER 010.
- **⚑ Self-initiated** (rung 4, contained + reversible; the owner welcomes
  these): scripts/open_work.py has a kill-switch header and nothing depends
  on it — worst case, delete the file.

**What this session was about:** the manager's hold clarification (build,
don't idle) with the buildable-now backlog empty. Rung-4 pick this chain
genuinely believes in: `scripts/open_work.py` classifies any branch whose
tip is not an ancestor of main as "unmerged commits" — but a branch can
carry commits and STILL have zero content diff vs main (an empty probe
commit like claude/probe-dash-mgmt, or content that landed via another
PR's squash like the relayed heartbeat and the merged review-site
branches). That misfired FOUR times today: every wake ritual since ~12:10Z
showed 4–7 "⚠ stranded" branches, of which up to three were ignorable —
each costing an MCP PR-state check to clear. The tool's whole purpose is
"one glance"; false alarms erode exactly that.

## What was done

- (work in progress — filled at close-out)
