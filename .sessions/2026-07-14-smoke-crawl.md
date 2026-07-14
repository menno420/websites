# 2026-07-14 — scheduled Playwright smoke-crawl in CI (the browser-level healthcheck)

> **Status:** `in-progress` — branch `claude/smoke-crawl-0714`; flips to `complete`
> + PR number as the deliberate LAST code step.

- **📊 Model:** Claude Fable 5 · worker · backlog promotion

**What this session was about:** backlog promotion — the `docs/ideas/backlog.md`
bullet "Scheduled browser-level smoke-crawl in CI — a Playwright job that
cold-crawls the three live sites the way the manual cold passes do" (captured
2026-07-13 by the cold-browser-review session, PR #311). The existing
`healthcheck.yml` smoke is curl-level (`/healthz` + `/` status codes); both
2026-07-13 cold passes found real regressions it can never see (dead chrome
wiring, a blank hamburger, a lost footer gutter, a favicon 404) because they
only exist in a rendering browser. This session builds the standing gate:
`scripts/smoke_crawl.py` (headless-Chromium crawl of the three public sites +
the control-plane root — same-site link discovery, desktop 1280 + mobile 375
viewports, console-error / page-status / link-status assertions, bounded page
caps and a global deadline) on a 6-hourly Actions schedule
(`.github/workflows/smoke-crawl.yml`), offset from healthcheck.yml's cron.

## What was done

- [[fill: files + load-bearing specifics]]
- Verified: [[fill: pytest count + bootstrap check verdict]]

⚑ Self-initiated: no — backlog promotion (the #311 cold-browser session's 💡
bullet in `docs/ideas/backlog.md`).

## 💡 Session idea

[[fill: idea + worth-having-because + dedupe result]]

## ⟲ Previous-session review

[[fill: one line on 2026-07-13-venture-vetting-catalog.md]]
