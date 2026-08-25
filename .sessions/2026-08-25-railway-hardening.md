# 2026-08-25 — reduce Railway traffic and restore the scheduled smoke signal

> **Status:** `complete` — branch `codex/railway-hardening`; PR #519.

- **📊 Model:** GPT-5 · high · production upkeep

**What this session was about:** Owner-directed Railway hardening. The live
usage audit tied most website cost to control-plane CPU and egress. Live logs
then corrected the first hypothesis: the continuing request flood was an
external crawler enumerating `/orders` filters, not the bounded scheduled
browser crawl. Preserve the crawl's real desktop/mobile rendering coverage,
stop the external flood at Railway's edge, and fix only the exact
masked-private destination that made the smoke signal red.

## What was done

- Added the exact verified-private `pokemon-mod-lab/control/README.md` URL to
  the crawler's path-level 404 exception set. A same-repository near miss still
  fails; the exception does not weaken ordinary public-link failures.
- Generalized the private-404 test budget from a stale literal to the size of
  the exact exception set, and extended the classifier regression coverage.
- Kept the six-hourly smoke schedule and its desktop/mobile rendering checks:
  run `32899593848` proved its only failure was this exact private link, while
  live Railway logs showed the continuing `/orders?...` traffic after that run
  was an unrelated external crawler.
- Railway-side hardening completed alongside this code change: the public
  control-plane now challenges `/orders*` at the edge; all three website
  services have explicit healthchecks, resource ceilings, CDN caching, and an
  observability dashboard. The separate worker projects received ceilings and
  dashboards too; three detached no-backup SuperBot volumes were removed while
  the attached database volume remained online.
- Local verification on the checked interpreter completed with **2233 passed**
  across all four service suites (5 existing deprecation warnings, 481.75 s),
  and the ambient Railway-ID guard reported OK. The strict gate runs against
  this completed card; a fresh scheduled smoke run is the post-merge live
  proof.

⚑ Self-initiated: no — direct owner instruction to execute the Railway audit
recommendations, excluding two-factor authentication.

## 💡 Session idea

No new product idea yet: this is narrowly scoped operational upkeep, and the
useful follow-on is measured 24-hour usage comparison rather than another
backlog item. Deduped against `docs/ideas/backlog.md` + the queue-state NEXT
list: not applicable.

## ⟲ Previous-session review

The prior records-refresh session correctly trued the living ledger and opened
orientation headroom; it predated the later production traffic pattern and
therefore could not record this Railway-specific upkeep.
