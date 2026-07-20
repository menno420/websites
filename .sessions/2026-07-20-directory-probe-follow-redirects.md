# 2026-07-20 — /directory .gba download probe: follow redirects

> **Status:** `in-progress` — branch `claude/directory-probe-follow-redirects`;
> flips to `complete` + PR number as the deliberate LAST code step. Born red:
> this card's in-progress Status holds the `quality` gate red
> (`[session-card-hold]`) until the fix + probe test land green.

- **📊 Model:** opus-4.8 · low · feature build

**What this session was about:** plan slice 6 of
`docs/plans/next-cycle-2026-07-19.md` — the `/directory` web-presence page
(`app/web_presence.py`, ORDER 021) probes each row's URL live via the shared
tokenless raw client (`github._get(url, raw=True)`), and that client does NOT
follow redirects. The Lumen Drift `.gba` release-download URL 302-redirects to a
CDN, so its row is parked `probe:false` in `app/data/web_presence.json` to avoid
a false "degraded (HTTP 302)" badge. This slice adds `follow_redirects=True`
scoped to the `/directory` probe path so a 302 → CDN → 200 chain reads as
`live`, then flips the Lumen Drift row back to `probe:true`. Work-ladder rung:
coordinator-assigned build — plan slice 6, the 💡 of
`.sessions/2026-07-18-arcade-directory-sync.md`.

## What was done

- `app/github.py` `_get`: added a `follow_redirects: bool = False` parameter,
  threaded to the per-request `.get(url, follow_redirects=...)`. Default `False`
  preserves the existing no-follow contract that `app/askverify.py`'s
  Discord-login probes depend on (they read the raw `302` status itself as the
  "configured" signal — following the redirect would destroy that signal). The
  change is opt-in per call, so no other `_get` caller is affected.
- `app/web_presence.py` `overview`: the `/directory` liveness probe now calls
  `github._get(r["url"], refresh=refresh, raw=True, follow_redirects=True)` — the
  ONLY caller that opts in. A redirect-hosted download (release asset → CDN) now
  health-probes to its FINAL status instead of false-negativing on the 302.
- `app/data/web_presence.json`: flipped the `lumen-drift` row to `probe:true`
  and rewrote its note to record that the `/directory` probe now follows
  redirects (the false-negative that forced `probe:false` is gone).
- `tests/test_directory_probe_redirects.py` (new): drives the REAL `_get`
  against `httpx.MockTransport` (the `test_github_cache_eviction` idiom) and
  pins the contract both ways — a 302 → 200 chain with `follow_redirects=True`
  yields a reachable `200` envelope, a 302 → 404 chain surfaces the final `404`,
  and the DEFAULT (no follow) still returns the bare `302` (askverify's signal
  preserved). A `web_presence.overview`-level test asserts the redirect-hosted
  download row renders `data-health="live"`.
- Updated the `github._get` fakes in `tests/test_web_directory.py` and
  `tests/test_row_idiom.py` to accept the new `follow_redirects` kwarg overview
  now passes (mechanical signature accommodation; no behavior change).
- Verified: `env -u DATABASE_URL python3 -m pytest tests/ botsite/tests
  dashboard/tests review/tests -q` — <N passed>; `python3 bootstrap.py check
  --strict` — <verdict>.

⚑ Self-initiated: no — coordinator-assigned slice 6, promoting the
arcade-directory-sync card's 💡 (a redirect-following `/directory` download
probe) from a captured idea into shipped code.

## 💡 Session idea

**Probe the redirect-hosted download's FINAL URL identity, not just status.**
The `/directory` probe now follows redirects and trusts a final `200`, but it
does not assert the final URL still points at the expected asset host — a
release that 302s to an unexpected CDN (or a hijacked redirect) would still read
`live`. A successor could record the expected final-host suffix per download row
and flag a redirect that lands somewhere else. Worth having because the whole
directory doctrine is honest liveness, and "reachable" should mean "reachable AT
the recorded target", not merely "some 200 answered". Deduped against
`docs/ideas/backlog.md` + the queue-state NEXT list: no final-URL-identity probe
entry exists (the arcade-directory-sync 💡 this slice closes was only about
following the redirect). To capture in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

`.sessions/2026-07-20-vendored-ast-core-guard.md` (#454, plan slice 5) landed
the auto-discovering vendored-copy guard with the right instinct — every
manifest entry VERIFIED against the tree, not merely listed. This slice carries
that forward by verifying the redirect fix does not silently break a sibling
consumer of the shared client: `app/askverify.py` reads the raw `302` directly,
so the fix is scoped per-request (opt-in) rather than at the client, and a test
pins that the default no-follow path still returns `302`.
