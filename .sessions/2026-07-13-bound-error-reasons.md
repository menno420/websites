# 2026-07-13 — bound error reasons: sanitize envelope error text at the source

> **Status:** complete — PR #240, branch `claude/bound-error-reasons`;
> every result envelope's `error` field is now bounded at the mint
> (`github._result` → `short_reason`: 140-char ellipsis cap, single
> line, markup bodies → generic `HTTP <status> — non-JSON error body`),
> so /fleet banners, the owner UI, /directory probes and every other
> consumer inherit the guard; lands via the auto-merge enabler on green.

- **📊 Model:** Claude 5 family · worker · hardening-slice

**What this session is about:** finishing what PR #237 started. That PR
bounded raw upstream error bodies page-side on `/freshness` only; the
SOURCE — `app/github.py` `_get`/`api_post`/`api_request`, which set
`error=str(data)[:200]` for non-JSON response bodies — still handed
unbounded raw text (live-observed: a full transient GitHub HTML error
page) to every other consumer: `/fleet` banners (`fleet.lane_status`
`fetch_error`, `resolve_lanes` fallback reason), the owner UI
(`rerun_latest_failed` messages), `/directory` probe details, and every
module that renders `res["error"]`. This session moved the guard to the
one honest choke point — the `_result()` envelope constructor in
`app/github.py` — the exact follow-up the #237 session card filed as
its 💡 idea.

## Results

- code touched (1): `app/github.py` — `REASON_MAX_CHARS = 140` +
  public `short_reason()` (whitespace collapse; body that looks like
  markup → `HTTP <status> — non-JSON error body` with the envelope
  status as the preserved head; hard 140-char ellipsis cap keeping the
  first meaningful words; short plain reasons verbatim; empty stays
  empty). Applied inside `_result()` — the single place every envelope
  from `_get` / `api_post` / `api_request` and their httpx-exception
  paths is minted — plus the `fetch_file` decode-failure override.
  Consumers needed zero changes: all ~20 modules that render
  `res["error"]` (fleet, freshness, prompts, projects, orders,
  owner_queue, environments, envhub, journal, activity, reviews, ideas,
  writeback, web_presence, prompt_history, prompt_artifacts, …) inherit
  the bound because the envelope is bounded before they see it.
- kept (deliberate): `/freshness`'s page-side `_short_reason` (PR #237)
  as harmless defense-in-depth — it also bounds reasons that never pass
  through a github envelope (registry-parse phrases, card-date text,
  composed cell reasons). `app/railway.py` mints its own GraphQL error
  strings (already `[:300]`-capped + non-JSON replaced) — out of scope,
  noted as a possible follow-up alignment to 140.
- tests touched (1 new): `tests/test_error_reason_bound.py` — 7 tests
  run against the REAL `_get` via `httpx.MockTransport` (monkeypatching
  `_get`, the usual idiom, would bypass the code under test): HTML
  error page → generic phrase; ~64 KB plain body → 140-char ellipsis
  with head preserved; multiline body → single line; short JSON/plain
  reasons verbatim; ok-path empty error; helper edges; and a rendered
  `/fleet` pass under a simulated full 503-HTML outage asserting the
  page carries the bounded generic phrase and none of the raw document.
- backlog: no captured-idea bullet existed to flip — the #237 card
  itself recorded "no existing bullet covers envelope-level reason
  sanitization"; the idea lived only in that card's 💡 section, now
  built.
- git: branch `claude/bound-error-reasons` off 92ad918 → 3dde521
  (claim + born-red card) → a004b68 (fix + tests) → merge of
  origin/main 0a8171d → this flip. PR #240.
- verify: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` → 985 passed pre-merge, 995 passed after merging
  origin/main (ORDER 041 prompt-surfacing landed +10);
  `python3 bootstrap.py check --strict` → green except this card's own
  designed born-red HOLD (flipped by this commit) and the pre-existing
  never-exit-affecting `owner-action-fields` advisory on
  control/status.md (not owned here).

⚑ Coordinator-assigned slice under ORDER 022 (night-run quality floor).

## ⟲ Previous-session review

The freshness-reason-truncate session (#237) diagnosed the disease
correctly and even prescribed the cure — its 💡 idea named the envelope
source as the right home for the guard — but scoped its fix page-side
to keep a bugfix PR small. Right call for that session, and the trail
it left (precedent constants, the markup heuristic, the test shapes)
made this source-level pass mostly a relocation job. One improvement
this session adds to the pattern: test the sanitizer through the real
`_get` with a mock transport rather than monkeypatching `_get` —
page-level tests that stub the envelope can never prove a source-level
bound.
