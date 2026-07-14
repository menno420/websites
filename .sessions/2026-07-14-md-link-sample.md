# 2026-07-14 — smoke-crawl: sampled existence check of rewritten github.com links

> **Status:** `in-progress` — branch `claude/md-link-sample-0714`; flips to `complete`
> + PR number as the deliberate LAST code step.

- **📊 Model:** Claude Fable 5 · worker · backlog promotion

**What this session was about:** backlog promotion — the `docs/ideas/backlog.md`
bullet "Sample-verify rewritten source-link targets — a bounded existence check
on the github.com blob URLs the markdown rewriter mints" (captured 2026-07-14,
md-relative-links session 💡). PR #322 converted same-origin 404s inside
rendered remote markdown into EXTERNAL github.com/raw links, and the
smoke-crawl never follows or fetches external links by documented design — so
a wrong path resolution, or an upstream file rename after the TTL cache
refreshes, now yields a GitHub 404 nothing measures. This session adds a
deterministic, bounded (≤10 per crawl) sample of those rewritten targets to
`scripts/smoke_crawl.py`, checked HEAD-first with a short timeout: 2xx/3xx
pass, 403 passes with a private-repo note, 404 fails naming the URL and its
source page, network errors warn.

## What was done

- (in progress)

⚑ Self-initiated: no — backlog promotion (the md-relative-links session's 💡
bullet in `docs/ideas/backlog.md`).

## 💡 Session idea

(to be filled at close-out)

## ⟲ Previous-session review

(to be filled at close-out)
