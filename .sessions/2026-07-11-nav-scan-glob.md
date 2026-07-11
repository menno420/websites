# 2026-07-11 — Nav-scan glob: the guard drops its own hand-kept list (rung 3)

> **Status:** `in-progress` — branch `claude/nav-scan-glob`; flips to
> `complete` + the real PR number after the PR exists.

- **📊 Model:** claude-fable-5 · worker · routine-fired build slice (continuous mode, slice 30 — 15:07Z nudge) — family from this session's own harness, per ORDER 010.

**What this session was about:** the 15:07Z nudge; ritual clean (no new
orders, no collision; sibling PR #132 re-checked: open, green, updated
13:42Z ~87 min ago — under the 2h threshold, hands off), so rung 3 with
the small designated pick: **nav-scan glob** — the slice-24 self-caught
irony: `tests/test_nav_manifest.py` guards against hand-kept nav lists
via a hand-kept `ROUTE_SOURCES = [main.py, owner.py]` module list, so
splitting routes into a new module would silently exit the scan.
Premise-checked before editing: globbing `app/*.py` matches ONLY the ten
real keys in main.py (no false positives anywhere in the package), and
owner.py contributing zero keys keeps the no-dead-entries direction
intact.

## What was done

- (work in progress — filled at close-out)
