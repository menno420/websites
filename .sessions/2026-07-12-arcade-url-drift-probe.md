# 2026-07-12 — Arcade live-URL drift probe (healthcheck pass)

> **Status:** `complete` — branch `claude/arcade-url-drift-probe`, PR #214.

- **📊 Model:** claude-fable-5 · worker · feature-slice

**What this session was about:** `botsite/data/arcade.json` presents games
with `availability: "live"` URLs, but nothing re-verifies those URLs after
the card ships — a dead game link silently outlives its card (ORDER 022
flipped mineverse by hand to notice exactly this). This session builds the
probe: every live-availability URL is cold-fetched by the scheduled
healthcheck and flagged when it stops returning 200. Live network fetches
stay OUT of the required `quality` gate — probe logic is unit-tested against
`httpx.MockTransport`; the real fetch runs only via
`scripts/healthcheck.py` / `healthcheck.yml`. Coordinator-assigned slice;
executes the backlog bullet "Arcade live-URL drift probe" (captured
2026-07-12, ORDER 022 drift session).

## What was done

- `botsite/arcade_probe.py` — new probe module. Loads the registry through
  the SAME loader the /arcade page renders with (`arcade.load_games`), so
  probe coverage and page content can never disagree about "live".
  `probe_url` GETs one URL (httpx, 10s timeout, redirects followed — a live
  game behind a 301/308 is still live; the FINAL response must be 200) and
  never raises: non-200 status, timeout, connection error, malformed URL,
  and any surprise exception each degrade to a `(False, reason)` finding.
  `probe_live_urls` returns per-URL verdict rows + honest coverage (non-live
  entries listed as skipped, never silently ignored); a registry loading to
  ZERO entries is itself a flagged condition (mirrors the fleet-registry
  zero-lanes alert). Injectable `httpx.Client` for tests.
- `scripts/healthcheck.py` — new `check_arcade_urls()` pass wired into
  `main()` after the fleet-registry check, matching its structure (returns
  `(ok, lines)`, defensive try/except so a probe bug prints a FAIL line
  instead of a traceback). Flagged findings fold into `ok_all` → exit 1,
  the script's existing failure idiom (feeds the owner's failed-workflow
  email from the 6-hourly healthcheck.yml schedule).
- Tests, all network-free: `botsite/tests/test_arcade_probe.py` — 13 unit
  tests over `httpx.MockTransport` (200 OK; 404/500/302-final flagged;
  redirect→200 OK; timeout flagged; connection error flagged; malformed URL
  flagged without any fetch; unexpected exception → finding not crash;
  mixed-registry summary counts; live-with-no-URL flagged; zero-entry
  registry flagged; committed-registry coverage pin). New
  `tests/test_healthcheck_arcade.py` — 6 wiring tests (pass/flag/not-probed
  lines, probe-bug degradation, flagged URL → `main()` exit 1, healthy →
  exit 0), same module-load idiom as `tests/test_healthcheck_registry.py`.
- `docs/ideas/backlog.md` — the executed bullet flipped `captured` → `built`
  (PR #214, original capture preserved); this session's 💡 captured.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — 790 passed, 1 warning; `python3 bootstrap.py check
  --strict` — green apart from this card's designed born-red hold and the
  pre-existing `owner-action-fields` advisory (never exit-affecting).
- Real probe run (one-shot, GET-only, via `python3 scripts/healthcheck.py`):
  exit 0 — mineverse `https://web-production-97636.up.railway.app` → 200
  PASS; lumen-drift + games-web honestly reported "not probed
  (availability: unavailable)". No drift found, so no honesty flips to
  `arcade.json` were needed this session.

⚑ Self-initiated: no — coordinator-assigned slice executing an existing
backlog bullet.

## 💡 Session idea

**Probe download-availability arcade URLs too** — the /arcade page renders an
outbound link for `availability: download` entries with a URL (`has_link`
covers live AND download), but this probe only cold-fetches `live` entries;
one more availability value in the filter extends the drift guarantee to
download links. Worth having because the first `download` flip is already
queued (lumen-drift's GitHub Release is one owner click away) and it would
silently re-open the exact hole this session closed. Deduped against
`docs/ideas/backlog.md` + the queue-state NEXT list: no bullet touches
download-link liveness. Captured in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

The /prompts pinned-registry drift-chip session (PR #213) did well —
piggybacking drift detection on the SAME TTL-cached listing /projects
already fetches (zero new network surface) and pinning "never a fabricated
green" in tests; one watch-item it left: its autouse matched-registry
fixture now couples every pre-existing /prompts test to the `repo_api`
call shape, so a future `app/github.py` signature change will red that
whole file at once.
