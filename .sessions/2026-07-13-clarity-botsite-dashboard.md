# 2026-07-13 — clarity bar for botsite + dashboard: every live page says what it is

> **Status:** `complete` — branch `claude/clarity-botsite-dashboard`; PR #231.

- **📊 Model:** Claude Fable 5 · worker · audit-and-fix-slice

**What this session was about:** order rung — ORDER 022 seat item 1, the
clarity-bar audit, dispatched by the coordinator as a worker slice scoped to
the **botsite/** and **dashboard/** services (sibling sessions own the app/
and review/ halves of the same order). Goal: every live page on the two sites
immediately shows what it is, what it does, and what its key features are — a
first-time visitor should never have to guess. Fixes stay inside the existing
Jinja2 server-rendered design idiom, with tests covering the new copy/structure.

## What was done

- Audited 43 live pages across botsite + dashboard against the clarity bar
  (every page must immediately show what it is, what it does, and its key
  features). 7 misses found; all 7 fixed at template level so every page
  they render inherits the fix (commit 5c309fd, PR #231):
  - botsite: 404 page gains a real h1; feature-detail pages gain a framing
    lede (covers 44 pages); command-detail pages gain a Discord-context lede
    (~330 pages); arcade page now defines what "fleet" means;
    testing_owner page gains a lede — a gated route (live route is 503
    while `SITE_PASSWORD` is unset), fixed from the template.
  - dashboard: admin settings-domain pages gain an action lede (covers 17
    pages); NAV gains Aliases + Console entries, and the duplicate drawer
    links those entries obsoleted were removed.
- 8 new pinning tests lock the fixed copy/structure in place.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — 905 passed (was 897); `python3 bootstrap.py check
  --strict` — green apart from this card's own designed born-red hold
  (cleared by this flip).

⚑ Self-initiated: no — coordinator-dispatched slice of ORDER 022 seat item 1.

## 💡 Session idea

**Make the clarity bar structural, not per-page** — today the bar is only
pinned page-by-page (this session added 8 such pins), so every new route
starts unprotected until someone hand-writes its test. A shared test helper
that walks every GET route on each service and asserts the rendered page
carries an h1 plus a `.sb-lead`-style lede would turn the bar into a single
structural invariant instead of per-page whack-a-mole. Worth having because
the 7 misses fixed this session all shipped through the exact gap such a
sweep would close — pages nobody thought to pin. Deduped against
`docs/ideas/backlog.md` + the queue-state NEXT list: no overlap (backlog's
nearest neighbors are env-inventory scans, nothing covers route-surface copy
structure). Capture in `docs/ideas/backlog.md` handed to the coordinator —
this flip commit is scoped to card + claim only per dispatch.

## ⟲ Previous-session review

The inventory-consistency-pin session (PR #225) did well — it proved its new
pin red on pre-fix main before trusting it green, and its card recorded exact
test counts; nothing it missed affects this lane.
