# 2026-07-18 — NAV-completeness guard for the review service

> **Status:** `in-progress` — branch `claude/review-nav-guard`; flips to
> `complete` + PR number as the deliberate LAST code step. This in-progress
> badge is the born-red hold: the `quality` gate keeps the PR red until the
> guard test lands green and this card is flipped.

- **📊 Model:** in-progress placeholder — filled on the completion flip.

**What this session is about:** add a guard test so the hand-maintained `NAV`
list in `review/app.py` cannot silently drift from the actual top-level page
routes. Today nothing fails when a page route is added to the router but left
out of NAV (an orphaned page), or when a NAV entry points at a path with no
route (a dead nav link). The previous `2026-07-18-review-questions-nav` card
(R1) fixed exactly one such orphan — a first-class `/questions` page that
returned 200 but was absent from the header NAV — and flagged this gap as its
session idea: a route-introspection completeness guard.

## Plan

- New `review/tests/test_nav_completeness.py`, three assertions, no production
  code change:
  1. every NAV path resolves to a registered top-level GET route (no dead nav
     links),
  2. every top-level GET route is either in NAV or on an explicit non-page
     allow-list (no orphaned pages),
  3. the non-page allow-list has no stale entries (all still routed).
- The test introspects `app.routes` (recursing included routers) and derives
  the truth from the FastAPI router rather than a second hand-maintained list.
- Test-only. No change to `review/app.py`, templates, data, or env.

⚑ Self-initiated: no — coordinator-dispatched, promoting the R1 card's session
idea (the NAV-completeness guard) from `docs/ideas` into a shipped test.

## What was done

- in-progress placeholder — the close-out evidence (files, verify counts) is
  filled on the completion flip.

## 💡 Session idea

- in-progress placeholder — the successor idea is filled on the completion
  flip.

## ⟲ Previous-session review

- in-progress placeholder — the one-line review of
  `2026-07-18-review-questions-nav.md` is filled on the completion flip.
