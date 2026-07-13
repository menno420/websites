# 2026-07-13 — env hardening: int("") import-crash fix + SITE_PASSWORD docs

> **Status:** `in-progress` — branch `claude/env-hardening-0713`; flips to
> `complete` + PR number as the deliberate LAST code step.

- **📊 Model:** fable-class · worker · order-slice

**What this session was about:** order rung — ORDER 026 follow-through
(`control/inbox.md` § "ORDER 026 · 2026-07-13T10:45Z"). The ORDER 026
discovery recorded in `docs/CAPABILITIES.md` (2026-07-13 wall entry) found
that an empty-string env var crashes three services at import via `int("")`
on the TTL vars, and that Railway variable writes are harness-denied. This
session hardens every module-level numeric env parse across app/, botsite/,
dashboard/, review/ to fall back to the documented default on
empty/unset/malformed values, documents SITE_PASSWORD in the env-var docs
home, and records a bounded read-only finding on ANTHROPIC_API_KEY for the
parallel botsite Railway copy (variable NAMES only, never values).

## What was done

- (in progress — filled at close-out)
- Verified: (in progress — filled at close-out)

⚑ Self-initiated: no — ORDER 026 follow-through (env-hardening prework
dispatched by the coordinator).

## 💡 Session idea

(filled at close-out, deduped against `docs/ideas/backlog.md` first)

## ⟲ Previous-session review

(filled at close-out from `.sessions/2026-07-13-venture-vetting-catalog.md`)
