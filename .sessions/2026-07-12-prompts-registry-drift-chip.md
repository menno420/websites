# 2026-07-12 — /prompts pinned-registry drift chip

> **Status:** `complete` — branch `claude/prompts-registry-drift-chip`, PR #213.

- **📊 Model:** Claude Fable 5 · worker · feature-slice

**What this session was about:** the /prompts library pins its seat list
(`app/roster.py` `SEATS`) rather than discovering it, so a seat added or
renamed in the fleet-manager `projects/` registry silently drifts — dead 404
cells with no signal. This session cross-checks the pinned set against the
`projects/` registry listing the app already fetches (same TTL-cached
`github.repo_api` call /projects makes — zero new network surface) and
renders an honest drift chip on /prompts: match / drifted (+new − missing,
named) / registry-unavailable (drift unknown, never a fabricated green).
Coordinator-assigned slice; executes the backlog bullet
"/prompts pinned-registry drift chip" (source:
`.sessions/2026-07-12-prompt-library.md` 💡).

## What was done

- `app/prompts.py` — new `registry_drift()`: compares `set(SEATS)` against
  the directory names in the `projects/` contents listing, fetched via
  `github.repo_api(REPO, f"/contents/{ROOT}")` with `ROOT` imported from
  `app/projects.py` — the EXACT URL /projects lists, so within the TTL the
  two pages share one cache entry (no per-package walk, no new network
  surface). Fetched concurrently with the 26 artifacts in `overview()`;
  result exposed as the `drift` key. Honesty ladder: failed/404 listing →
  `unknown` (+reason, no green ever fabricated); listing ok but no package
  dirs → real drift (all pinned missing); otherwise sorted `added` /
  `missing` name lists.
- `app/templates/prompts.html` — drift chip in the header card using the
  existing `.b ok / .b warn / .b unknown` chip idiom (same as the /projects
  role-coverage chips): green "pinned list matches registry ✓" on match;
  amber "pinned list drifted" naming the actual seats ("+X new in registry
  (`name`, …)" / "−Y no longer present (`name`, …)") plus the
  `app/roster.py` re-pin pointer; dim "registry unavailable — drift
  unknown" (reason in the tooltip) when the listing cannot be fetched.
- `tests/test_prompts.py` — 6 new offline tests (match / +added / −missing
  / both at once / listing unavailable incl. the 404-not-landed shape,
  asserting NO false green / empty-but-listed registry is real drift), plus
  an autouse matched-registry fixture so every pre-existing /prompts test
  stays network-free now that the route calls `repo_api`.
  `tests/test_prompt_paste_body.py` route test pins `repo_api` likewise.
- `docs/ideas/backlog.md` — the executed bullet flipped `captured` →
  `built` (PR #213, original capture preserved); this session's 💡 captured.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — 769 passed, 1 warning; `python3 bootstrap.py check
  --strict` — green apart from this card's designed born-red hold and the
  pre-existing `owner-action-fields` advisory (never exit-affecting). The
  heartbeat-grammar failure noted at dispatch did not reproduce — its fix
  (#212) had already landed on main before this branch was cut.

⚑ Self-initiated: no — coordinator-assigned slice executing an existing
backlog bullet.

## 💡 Session idea

**Shared contents-listing honesty classifier** — `projects.overview`,
`projects.detail`, and now `prompts.registry_drift` each hand-roll the same
degraded-listing ladder over a `github.repo_api` contents result; one
`classify_listing(result) -> (state, reason)` helper with the 404
disposition as an explicit parameter would make the pages share one ladder.
Worth having because the honesty ladder is the site's core UI promise and
three hand-rolled copies have already begun to diverge — the next copy forks
it silently. Deduped against `docs/ideas/backlog.md` + the queue-state NEXT
list: nothing touches listing-degradation plumbing. Captured in
`docs/ideas/backlog.md`.

## ⟲ Previous-session review

The v1.15.0 kit-upgrade session (2026-07-12) did well: three-way sha256
verification, byte-verified banks, and an explicit lane-owed list made its
state trivially auditable from the card alone; nothing it missed affects
this lane — its lane-owed items (heartbeat `kit:` bump, diverged-doc merges)
remain open for the kit lane, not this one.
