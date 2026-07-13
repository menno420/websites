# 2026-07-13 — bound error reasons: sanitize envelope error text at the source

> **Status:** in-progress

- **📊 Model:** Claude 5 family · worker · hardening-slice

**What this session is about:** finishing what PR #237 started. That PR
bounded raw upstream error bodies page-side on `/freshness` only; the
SOURCE — `app/github.py` `_get`/`api_post`/`api_request`, which set
`error=str(data)[:200]` for non-JSON response bodies — still hands
unbounded raw text (live-observed: a full transient GitHub HTML error
page) to every other consumer: `/fleet` banners (`fleet.lane_status`
`fetch_error`, `resolve_lanes` fallback reason), the owner UI
(`rerun_latest_failed` messages), `/directory` probe details, and every
module that renders `res["error"]`. This session moves the guard to the
one honest choke point — the `_result()` envelope constructor in
`app/github.py` — so every consumer inherits a short, single-line,
markup-free reason for free (the exact follow-up the #237 session card
filed as its 💡 idea).

**Scope / plan:**

- `app/github.py`: `short_reason()` (whitespace collapse, markup body →
  generic `HTTP <status> — non-JSON error body`, hard 140-char ellipsis
  cap per the #237 precedent, short plain reasons verbatim) applied
  inside `_result()` so `_get` / `api_post` / `api_request` and the
  exception paths all mint bounded `error` fields.
- Keep `/freshness`'s page-side `_short_reason` (PR #237) as harmless
  defense-in-depth — it also bounds reasons that never pass through a
  github envelope (registry-parse phrases, composed cell text).
- Tests in `tests/`: HTML error page, tens-of-KB body, multiline body,
  already-short plain reason — envelope `error` bounded (≤140) and
  markup-free — plus a rendered `/fleet` pass asserting no raw error
  document reaches the page.
- Flip the captured backlog idea (envelope-level reason hygiene) to
  built if a bullet exists.

⚑ Coordinator-assigned slice under ORDER 022 (night-run quality floor).
