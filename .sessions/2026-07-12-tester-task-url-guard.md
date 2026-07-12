# 2026-07-12 — botsite: tester-task product URL liveness guard

> **Status:** `complete` — PR #221, branch `claude/tester-task-url-guard`;
> lands via the auto-merge-enabler on green.

- **📊 Model:** claude-fable-5 · worker · feature-slice

**What this session was about:** backlog promotion — the captured bullet
"Tester-task URL liveness guard" (`docs/ideas/backlog.md`, source
`.sessions/2026-07-12-order-018-testing-platform-pr1.md` 💡). Every `open`
task in `botsite/testing_tasks.json` points a paying tester at a
`product_url`; if that URL dies, the program burns real testers' time and
its own credibility before anyone notices. This session grew
`scripts/healthcheck.py` a testing-catalog pass mirroring the arcade URL
drift probe (`botsite/arcade_probe.py`, PRs #214/#220): GET every open
task's `product_url`, final-200 semantics, fail-soft findings.

## What was done

- **Probe** `botsite/testing_probe.py`: `probe_task_urls()` iterates the
  committed catalog, probes `status: "open"` tasks' `product_url`s and
  skips `coming-soon`/`closed` honestly (id + status, printed as explicit
  "not probed" lines). Verdict logic is IMPORTED, not forked —
  `probe_url`/`TIMEOUT_S` come from `arcade_probe` (final-200, redirects
  followed, timeout/connection/malformed-URL findings). Fail-soft
  throughout: an open task with no `product_url` is a flagged finding, a
  zero-task catalog is a flagged alert (mirrors the arcade zero-entries
  alert), and even a catalog that fails to LOAD degrades to a flagged
  summary — `probe_task_urls` never raises.
- **Loader extraction** `botsite/testing_catalog.py`: `load_tasks` +
  `TASKS_PATH` moved out of the route module (byte-identical semantics);
  `botsite/testing.py` re-exports them, so `/testing` and the probe read
  through the SAME loader (the arcade probe's coverage-agreement rule) and
  the probe never imports routes. The committed `status` field is what is
  probed — live slot fill-up (`effective_status`) lives in the SQLite
  store the healthcheck host cannot see, and a filled-but-open task keeps
  deserving its liveness check.
- **Healthcheck** `scripts/healthcheck.py`: `check_testing_urls()` folded
  in exactly like `check_arcade_urls()` (defensive try around the probe,
  per-row PASS/FLAGGED lines with `[status]`, exit-1-on-any-failure);
  header/exit-code docstring updated.
- **Tests** (all offline — the `quality` gate stays network-free):
  `botsite/tests/test_testing_probe.py` (17, `httpx.MockTransport`): open
  200 healthy / 308→200 chain healthy / 404 flagged / timeout + connection
  error flagged fail-soft / malformed URL flagged with NO fetch / missing
  URL flagged (parametrized "" and null) / coming-soon+closed skipped and
  never fetched / mixed catalog buckets honestly / zero-task, missing-file
  and corrupt-file alerts / committed-catalog coverage pin (probed set =
  open set, via the shared loader; all four open URLs probeable) /
  `probe_url`-is-the-arcade's pin / route-loader-is-probe-loader pin.
  `tests/test_healthcheck_testing.py` (7): pass/fail lines, `[status]` in
  rows, not-probed lines, probe-bug→FAIL-line, main() exit 1/0 fold-in.
  `tests/test_healthcheck_arcade.py`: the two existing main() exit-code
  tests now stub the new testing pass too (they'd otherwise hit the real
  network after the fold-in).
- **Backlog** `docs/ideas/backlog.md`: source bullet flipped
  `captured → built` (PR #221), noting the render-time-probe and
  auto-flip-to-`coming-soon` variants were deliberately NOT taken (no
  request-path network calls, no data writes); claim file deleted at close.
- Real probe run locally: all 4 open-task URLs live — site-review-botsite,
  site-review-dashboard, site-review-control-plane-projects,
  walkthrough-botsite-first-visit each 200 PASS; 4 coming-soon tasks
  honestly skipped; `ok: true`, nothing flagged, no data changed.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — 880 passed (+24 new), 0 failed, 1 warning;
  `python3 bootstrap.py check --strict` — green apart from this card's own
  designed born-red HOLD (flipped by this commit) and the pre-existing
  `owner-action-fields` advisory on control/status.md (never
  exit-affecting, not owned here).

**Decisions made:** probe the committed `status`, not `effective_status` —
the healthcheck host has no SQLite store, and a slots-filled task's URL
still needs to be alive; import `probe_url` from `arcade_probe` instead of
copying it (the #220 session's single-source idea, applied one module
early).

⚑ Self-initiated: no — coordinator-assigned slice executing an existing
backlog bullet.

## 💡 Session idea

**Pin open tester-task `product_url` hosts to the healthcheck `SERVICES`
table** — the repo now hand-keeps the fleet's public hosts in TWO committed
places (`scripts/healthcheck.py` `SERVICES` and the open tasks'
`product_url`s in `botsite/testing_tasks.json`; today all four open-task
URLs sit on the three SERVICES hosts), and a service rename that updates
one but not the other leaves testers on a dead host for up to 6 hours until
the cron fires. One zero-network suite test asserting every open task's
`product_url` host is a SERVICES host (or declared-exception) catches that
at PR time. Worth having because the liveness guard just shipped is a
runtime net — this is the cheaper compile-time net for the most likely way
those URLs die. Deduped against `docs/ideas/backlog.md` + the queue-state
NEXT list: the committed-inventory pin bullet covers env-var NAMES
(`railway.SERVICES` vs envhub registry), not hosts; nothing touches
testing-catalog hosts. Captured in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

The arcade-download-probe session (#220) did well — its refusal to loosen
final-200 semantics despite the capture's "200-or-302" phrasing is the
discipline this session inherited for free by importing `probe_url` instead
of forking it; one miss: its 💡 (single source of truth for the
availabilities tuple) stopped at the arcade pair, not noticing the same
duplicated-literal pattern was about to be born again one module over in
the testing catalog (this session's 💡 is that sibling).
