# 2026-07-12 — arcade probe: extend URL drift probe to download-availability entries

> **Status:** `complete` — PR #220, branch `claude/arcade-download-probe`;
> lands via the auto-merge-enabler on green.

- **📊 Model:** Claude Fable 5 · worker · feature-slice

**What this session was about:** backlog promotion — the captured bullet
"Probe download-availability arcade URLs too" (`docs/ideas/backlog.md`,
source `.sessions/2026-07-12-arcade-url-drift-probe.md` 💡). The /arcade
page renders an outbound link for both `live` AND `download` entries with a
URL (`has_link` in `botsite/arcade.py`), but the drift probe shipped in
PR #214 (`botsite/arcade_probe.py`) only cold-fetched `live` entries — the
moment lumen-drift's card flips to `download`, its link re-enters the
unverified-drift class the probe was built to close. This session extends
the probe's filter to `download`, keeping final-200 semantics.

## What was done

- **Probe** `botsite/arcade_probe.py`: new `PROBED_AVAILABILITIES =
  ("live", "download")` drives the filter (membership test replaces the
  `!= "live"` check); probed rows now carry the entry's `availability`; a
  probed-availability entry with no URL is flagged with per-availability
  wording (`availability "download" but no URL to probe`);
  `probe_live_urls` renamed `probe_registry_urls` (the old name became a
  lie); module docstring + summary note updated to report honestly: N
  URL(s) probed (live+download), M flagged, K other-availability entries
  not probed. `probe_url` deliberately UNCHANGED — `follow_redirects=True`
  already makes a 302→200 chain end at 200 (healthy), a FINAL redirect
  status stays flagged, and a redirect loop raises
  `httpx.TooManyRedirects` → caught → flagged. No status-logic loosening.
- **Healthcheck** `scripts/healthcheck.py`: `check_arcade_urls()` calls the
  new name, per-row output shows `[availability]`, docstring and the
  `main()` label updated to "arcade URL drift probe (live+download)".
- **Tests** `botsite/tests/test_arcade_probe.py` (all offline via
  `httpx.MockTransport` — the `quality` gate stays network-free): old
  live-only pins reworked (skip-list + note string; committed-registry
  coverage pin now asserts probed set = live+download via
  `PROBED_AVAILABILITIES`); new coverage: download 200 healthy, download
  302→200 chain healthy, download 404 flagged, download timeout flagged,
  redirect loop flagged (`TooManyRedirects`), mixed live+download registry
  buckets each entry honestly, no-URL flagged parametrized over both
  availabilities; final-302-flagged parametrized pin kept.
  `tests/test_healthcheck_arcade.py`: monkeypatch target + label substrings
  updated; new test pins `[availability]` in per-row output (7 tests, was 6).
- **Backlog** `docs/ideas/backlog.md`: source bullet flipped
  `captured → built` (PR #220); claim file deleted at close.
- Real probe run locally: mineverse (live) → 200 PASS; zero download
  entries exist yet (lumen-drift + games-web honestly skipped as
  `unavailable`); `ok: true`, nothing flagged, no availability flipped.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — 856 passed (+8 new), 0 failed, 1 warning;
  `python3 bootstrap.py check --strict` — green apart from this card's own
  designed born-red HOLD (flipped by this commit) and the pre-existing
  `owner-action-fields` advisory on control/status.md (never
  exit-affecting, not owned here).

**Decisions made:** no 302-as-healthy loosening despite the original
capture's "expecting 200-or-302" phrasing — the client already follows
redirects, so a release-asset 302→CDN→200 chain is healthy under the
EXISTING final-200 rule, while accepting a FINAL 302 would bless a URL
whose destination was never verified; the capture's intent (redirecting
release assets count healthy) is met without weakening the check.

⚑ Self-initiated: no — coordinator-assigned slice executing an existing
backlog bullet.

## 💡 Session idea

**Single source of truth for link-bearing arcade availabilities** — the
page's `has_link` hardcodes `("live", "download")` in `botsite/arcade.py`
line 86 and the probe now duplicates that tuple as
`arcade_probe.PROBED_AVAILABILITIES`; move it to one constant in
`botsite/arcade.py` consumed by both, plus a pin test that probe coverage
equals the linked set. Worth having because the probe's whole guarantee is
"coverage never disagrees with the page", and today that agreement is a
coincidence of two literals — the next link-bearing availability value
would silently under-cover exactly like the `download` gap just closed.
Deduped against `docs/ideas/backlog.md` + the queue-state NEXT list: the
two arcade-probe bullets there are both `built` and neither covers the
duplicated-tuple drift. Captured in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

The envhub-group-chips session (#219) did well — feeding a manifest-shaped
stub through the unchanged `annotate_completeness` instead of forking the
counting logic is the reuse pattern this session copied (extend the
existing filter, don't fork `probe_url`); one miss: its card's ender
checklist promises a `control/status.md` heartbeat overwrite as the final
step, but the current status.md still carries the `owner-action-fields`
advisory the checker nags about every session — the ask was never
restructured or withdrawn.
