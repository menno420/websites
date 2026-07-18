# 2026-07-18 — NAV-completeness guards for botsite + dashboard

> **Status:** `in-progress` — branch `claude/nav-guard-siblings`; flips to
> `complete` + PR number as the deliberate LAST code step. Born-red hold: this
> in-progress Status keeps the `quality` gate red until the two guard tests
> land green.

- **📊 Model:** [[fill: family-level model — resolve on last commit]]

**What this session is about:** extend the router-introspection
NAV-completeness guard to the `botsite` and `dashboard` services. The review
service shipped this guard earlier today (`2026-07-18-review-nav-guard.md`,
PR #416) and `app/` already has route coverage via `tests/test_nav_manifest.py`
over its single `app/nav.py` manifest — but botsite and dashboard both carry
hand-maintained `NAV` lists in their `app.py` that drift silently: a new page
route left out of NAV ships orphaned from the header, and a NAV entry pointing
at a dead path fails nothing at runtime.

## Plan

- New `botsite/tests/test_nav_completeness.py` + `dashboard/tests/test_nav_completeness.py`,
  each self-contained per service (introspects only its own `app.routes`,
  recursing included routers — no cross-service imports). Test-only, no
  production code change.
- Design difference from the review guard: botsite and dashboard both have
  real HTML pages deliberately OUTSIDE the top nav (home `/`, the design /
  submission surface, the gated `/admin` / owner-queue pages). So each guard
  uses an explicit `PAGES_NOT_IN_NAV` allowlist ALONGSIDE `NON_PAGE_PATHS`:
  every top-level GET route must be classified as a nav page (`NAV`), a
  non-page endpoint (`NON_PAGE_PATHS` — feeds/probes/assets/redirects), or an
  intentional off-nav page (`PAGES_NOT_IN_NAV`). Three assertions per service:
  NAV paths all resolve to routes, every page route is classified, and the
  classification lists have no stale entries.

⚑ Self-initiated: no — coordinator-dispatched, promoting the review guard
card's session idea (extend the router-introspection NAV guard to botsite +
dashboard) from a flagged gap into shipped tests.

## What was done

- [[fill: verify results — four-suite passed count + kit-strict verdict; resolve on last commit]]

## 💡 Session idea

[[fill: one successor idea + why + dedupe; resolve on last commit]]

## ⟲ Previous-session review

[[fill: one-line remark on 2026-07-18-review-nav-guard.md; resolve on last commit]]
