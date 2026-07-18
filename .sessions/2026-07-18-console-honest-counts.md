# 2026-07-18 — Console honest counts (C1)

> **Status:** `complete` — branch `claude/console-honest-counts`; the
> `/work`, `/history`, `/console` category landing pages now render a FAILED
> count distinctly from a genuine `0`. Four under-guarded `_count_*` helpers
> in `app/main.py` used to report a fetch-failure as a faked `0`; they now
> return `None` (the template's honest `—` marker) whenever the source signals
> the count could not be honestly computed, while a real `0` still renders as
> `0`. +13 tests.

- **📊 Model:** Claude Opus · high · feature build (console honest counts)

**What this session is about:** the IA v2 category landing pages (`/work`,
`/history`, `/console`) decorate each subcategory row with a live count chip.
The template already renders `None` as an honest `—` and an int as the number,
but four of the eight `_count_*` providers (`queue`, `orders`, `ideas`,
`activity`) trusted their source's roll-up unconditionally — so a fetch failure
that zeroed the roll-up rendered as a misleading `0` (a lie: "0 open" when the
truth is "unknown"). C1 (backlog) closes that: a failed counter renders `—`,
distinct from a genuine `0`. Additive, read-only GET render — no state-changing
route, no CSRF/Origin surface, no new credential, no serialized JSON payload.

⚑ Self-initiated: no — coordinator-dispatched backlog slice (C1).

## Close-out

**Evidence:**

- files touched this branch: `app/main.py` (the four under-guarded `_count_*`
  providers — `_count_queue`, `_count_orders`, `_count_ideas`, `_count_activity`
  — now short-circuit to `None` using the honesty signal each source ALREADY
  computes, no new fetch and no new field: queue on `unreadable_lanes`
  non-empty, orders on `summary["errored"]`, ideas on `ideas.totals`'s
  `errors`, activity on `timeline`'s `errors` list; the other four counters —
  `reviews`/`projects`/`directory` already returned `None` on non-ok and
  `prompts` is a fetch-free static registry size — were left untouched);
  `tests/test_console_honest_counts.py` (new, +13: for each of the four fixed
  counters a genuine-0 / failed-source / non-zero triad, plus an end-to-end
  `_category_rows` render proving a failed counter carries the `None` sentinel
  the template shows as `—` while a genuine 0 carries an actual `0`); this
  card + `control/status.md` heartbeat.
- git: branch `claude/console-honest-counts` from `origin/main` @ `ef53dd1`
  (#388); commits `a04901c` (born-red card), `0811077` (build), `e8713f6`
  (tests), `89ec819` (heartbeat status), + this flip.
- verify: `python3 -m pytest tests/ botsite/tests dashboard/tests review/tests
  -q` — **1742 passed, 1 warning** (exit 0); `python3 bootstrap.py check
  --strict` (and `--require-session-log`, the CI form) — the only red during
  the session was the DESIGNED born-red hold on this card, released at this
  flip (the lone advisory warning is a pre-existing model-line-class nudge on
  `2026-07-17-arcade-owner-action-queue.md`, never exit-affecting, not mine);
  no serialized JSON payload/contract changed — the category counts render
  HTML-only (`category.html` via `_category_page` → HTMLResponse), so no
  contract-pin (`test_json_contracts` / `test_fleet_json_contract` /
  `test_hostile_env_smoke` / `test_env_poison_pin`) moved and no new env read
  was added.
- B1 live-check (merge==deploy honesty, reported not blocking): dashboard
  `/version` returned sha `ef53dd1c…` (== `ef53dd1`) and `/status` returned
  200 — B1 (#388) is live.

**Judgment:**

- Decisions made: (1) the display layer was ALREADY honest — `category.html`
  renders `None` as `—` (+ "count unavailable" tooltip) and an int as the
  number, and `_category_rows` already catches counter exceptions to `None`;
  the lie lived one layer up, in four providers that trusted a source roll-up
  that a fetch failure silently zeroes, so the tight fix is per-counter guards
  at the provider boundary, not a template or wrapper change. (2) The guard for
  each counter reuses the source's EXISTING error signal rather than inventing
  a new one — zero new fetches, zero new fields, idiomatic to each module's
  own fail-soft envelope. (3) Honesty over completeness on partial failure: a
  single errored repo/lane degrades the whole chip to `—` (the count is an
  undercount, and the page itself shows the per-repo error detail the tooltip
  points at) — the same never-report-an-undercount-as-truth posture
  `_count_reviews`/`_count_projects` already carry. (4) A genuinely empty but
  READABLE source still reports a real `0` (ideas `missing` dir is an honest
  absence, not an `error`); the distinction failed-vs-zero is the whole point.
  (5) Additive read-only GET — no state-changing route, no CSRF/Origin surface,
  no new credential, no cross-service import.
- Next session should know: `_COUNTERS` now has a consistent contract — a
  provider returns `None` (never a faked number) when its source could not be
  honestly counted. A NEW counter added to `_COUNTERS` must uphold that by
  hand; there is no structural guard yet (see the 💡 below). A4 (arcade JSON
  schema CI guard) is the recommended next slice per the heartbeat baton.

## 💡 Session idea

**An offline-honesty contract test over every `_COUNTERS` provider.** This
slice fixed four counters one-by-one, but the honest-vs-faked-zero contract
lives only in each provider's body — a fifth counter added to `_COUNTERS` later
can silently reintroduce the faked-`0` lie and nothing fails. A single
parametrized test that drives the whole `_COUNTERS` dict under a
fully-failed-source harness (every `github.*` fetch mocked to fail, like
`test_category_ia._offline`) and asserts each provider returns `None` — never a
`0`/int — would turn "counters must degrade honestly" from a per-author
convention into a mechanically-enforced contract, catching the next faked-count
regression at the boundary the same way the four new triad tests catch this
one. Small, test-only, dovetails with the row-idiom pins already in the suite.

## ⟲ Previous-session review

`.sessions/2026-07-17-dashboard-arcade-counts.md` (B1) set the exact
never-fake-a-0 posture this C1 slice extends from the dashboard `/status`
banner to the control-plane category chips — its "honest degrade reuses the
module's existing ok-envelope discipline" decision is the same reuse-the-source's-
own-signal move applied here; confirmed live this session (`/version` == ef53dd1).
