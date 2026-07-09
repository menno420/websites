# 2026-07-09 — Journal browser upgrade (rendered markdown + cross-repo search) + mobile polish

> **Status:** `in-progress` — control-plane journal browser gets safe
> server-side markdown rendering and a cross-repo search endpoint; the readiness
> board + journal + /owner get mobile-responsive CSS. First reviewable PR through
> the now-required `quality` CI gate. Card flips to `complete` as the last step.

## What is being done (in flight)

- (STEP 0) Verify the `quality` check is actually enforced on `websites` (via this
  PR's `mergeable_state` = blocked while `quality` pends), and fix the readiness
  board's `websites` row so it reflects `quality` as the required check.
- (A) Journal browser: lazy-import safe markdown rendering (fallback to `<pre>`),
  bleach sanitization, and a cross-repo `/journal/search` + `.json` search across
  all four repos' journal corpus (session logs + ledgers + routers).
- (B) Mobile polish: responsive CSS (media queries) so the board's wide tables
  scroll and controls stay tap-friendly at ~375px, without regressing desktop.
