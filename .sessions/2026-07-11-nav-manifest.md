# 2026-07-11 — Nav manifest: one list drives the nav and its membership test (rung 3)

> **Status:** `in-progress` — branch `claude/nav-manifest`; flips to
> `complete` + the real PR number after the PR exists.

- **📊 Model:** claude-fable-5 · worker · routine-fired build slice (continuous mode, slice 24 — 11:30Z nudge) — family from this session's own harness, per ORDER 010.

**What this session was about:** the 11:30Z nudge; ritual clean (no 12:00Z
fire visible, no new orders, no collision), so rung 3 with the designated
pick: **nav manifest** — the slice-19 idea. The "which pages live under
more ▾" decision existed twice by hand (template markup in base.html +
GROUPED/PRIMARY tuples in tests/test_nav_overflow.py); page 12 could be
added top-level with nobody noticing the overflow guard was the point.
One `(href, label, key)` manifest now drives both the template and the
membership test, and a test asserts every `active` key the routes
actually pass appears in the manifest.

## What was done

- (work in progress — filled at close-out)
