# Release-drift parity

> **Status:** `complete`

**Goal:** Surface review's already-baked release-drift signal
(`review/data/releases.json`) on two other owner surfaces — the dashboard
`/status` page and the console public board (`/`) — read-only over raw content,
with NO cross-service package imports and NO recomputing of drift. This session
re-renders the producer's baked `drift` flag; it never re-derives it.

## Previous-session review

The prior session (`claude/release-drift-banner`, ORDER 033,
`.sessions/2026-07-18-release-drift-banner.md`) baked the release-drift signal
into `review/data/releases.json` and rendered it site-wide in the **review/**
service. That work is sound and untouched here — this session is the parity
follow-on that fans the same committed signal out to the dashboard and console
surfaces without recomputing it.

## Slice 1 — /questions (verified live, skipped — honest null)

The review `/questions` surface was verified live at
https://review-production-fc91.up.railway.app/questions — HTTP 200, rendering
its graceful deliberate empty state ("No external reviewer questions on record
yet."). It is already covered by `review/tests/test_questionnaire.py` and
`review/tests/test_review_filters.py`, so no change was made (honest null — the
surface already does the right thing).

## Slice 2 — dashboard /status + console board

- **dashboard/data_source.py** — `RELEASES_JSON_URL` (env-overridable, defaults
  to `menno420/websites@main`, mirrors `ARCADE_JSON_URL`), a `fetch_releases()`
  wrapper, and a pure `release_drift(data)` shaper (filters to producer-flagged
  `drift` entries; missing/empty/None degrades to count 0, never raises).
- **dashboard/app.py** — `status_page()` fetches + shapes the mirror and adds
  `release_drift_entries`/`release_drift_count`/`releases_ok`/
  `releases_generated_at` to the route context (defensive: fetch-not-ok → count
  0 / no card). `_base_ctx` untouched.
- **dashboard/templates/status.html** — a drift card (existing `sb-status-banner`
  + `sb-cmdlist` styling) that renders ONLY when `release_drift_count > 0`; no
  drift → no card.
- **app/releasedrift.py** (new; distinct from the pre-existing unrelated
  `app/release_drift.py`) — fetches the committed mirror over the shared
  token-free raw path (`github._get(url, raw=True)`), shapes it, honest-degrades
  to count 0 on any fetch/parse failure. URL derives from the already-declared
  `config.GITHUB_RAW_BASE` — NO new env-var read, so no control-plane manifest
  change (avoids the PR #426 collision).
- **app/main.py** — `board()` fans the helper into its `asyncio.gather` and adds
  `release_drift_count`/`release_drift_entries` to the board context.
- **app/templates/board.html** — a `badge('warn', …)` chip in the `attn` block,
  rendered ONLY when drift is present.
- Tests: `dashboard/tests/test_release_drift.py`,
  `tests/test_release_drift_parity.py`; primed the releases URL in the existing
  dashboard `/status` fixtures so no test does a live fetch.
- Governance follow-through: dashboard's `RELEASES_JSON_URL` declared in
  `app/railway.py` (dashboard section) + `app/data/environments.json`, and the
  `app/data/env_coderefs.json` snapshot regenerated — the code↔declared drift
  and inventory-consistency gates stay green.

- **📊 Model:** Opus 4.x · high · feature build

## 💡 Idea

The four services now bake three cross-repo signals into `*/data/*.json`
(dashboard/console feeds, arcade registry, release-drift) and re-render them on
sibling surfaces — a tiny committed "signal registry" (name → baker → raw URL →
consumers) would make each new parity fan-out a data edit instead of a code hunt.
