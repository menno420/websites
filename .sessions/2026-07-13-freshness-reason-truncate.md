# 2026-07-13 — freshness reason truncate: sanitize failure reasons on /freshness

> **Status:** `in-progress`

- **📊 Model:** Fable 5 · worker · bugfix-slice

**What this session is about:** hardening the just-shipped `/freshness`
page (PR #235) against raw upstream error bodies. Live observation: during
a transient GitHub failure, the fetch envelope's `error` text — a full
HTML error page — rendered unabridged into a table cell
(`unknown — <!DOCTYPE html> <!-- Hello future GitHubber!...`). The
honest-degradation contract says "unknown — \<reason\>", but the reason
must be a short human-readable string, not a wholesale error document.
Fix: a `_short_reason()` helper in `app/freshness.py` that collapses
whitespace, replaces markup-looking bodies with a generic
`HTTP <status> — non-JSON error body` message, and hard-truncates to
140 chars with `…`; every user-visible reason (commit / card / PRs /
heartbeat cells, and the `/freshness.json` twin via the shared builder)
routes through it. Short meaningful errors like `HTTP 404` stay verbatim.
Tests in `tests/test_freshness.py` cover the HTML-body, long-plain-text,
and short-reason cases.

⚑ Self-initiated: yes — follow-up hardening of the /freshness page shipped in PR #235 (live-observed defect)
