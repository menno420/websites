# 2026-07-16 — catalog sha-drift pin, live-verified (ORDER 032 overnight slice)

> **Status:** `complete` — branch `claude/catalog-sha-drift-pin-20260716`;
> one contained, reversible slice: a live healthcheck pass flagging vetting
> packets that drifted from their pinned sha, plus a real capability
> discovery this session logged along the way.

- **📊 Model:** Claude Sonnet 5 · high · feature build

**What this session was about:** ORDER 032 (owner's live overnight
autonomy order) — keep working the backlog. A captured 2026-07-13 idea
(venture-vetting-catalog session) had sat un-built across 3 prior cycles
this lane because every earlier heartbeat assumed it needed live GitHub
API access this session doesn't have (ASK-0017). Before writing it off
again, this session tested the assumption directly: `curl
raw.githubusercontent.com/menno420/venture-lab/main/README.md` returned
`200` with no token — the REST API wall (`api.github.com`) does not extend
to raw content reads. That reopened the idea: `botsite/data/catalog.json`
pins each vetting packet's provenance as `"<repo> <path> @ <sha>"`; a
byte-diff of the packet's content at that pinned sha vs venture-lab's
current `main`, both over raw.githubusercontent.com, needs zero GitHub API
calls.

## What was done

- `botsite/catalog_sha_drift.py` (new) — `parse_source()` extracts
  `(repo, path, sha)` from the pinned-provenance `source` shape (skips,
  never flags, anything else — this probe verifies a pin, it doesn't
  invent one); `probe_catalog_sha_drift()` fetches each entry's packet at
  its pinned sha and at `main`, flags a byte difference. Same
  fail-soft/mock-testable contract as `botsite/arcade_probe.py` (real
  network ONLY in `scripts/healthcheck.py`, injectable `httpx.Client`,
  `quality` gate never touches the network).
- `scripts/healthcheck.py`: added `check_catalog_sha_drift()` (same shape
  as `check_arcade_urls`) and wired it into `main()`'s pass sequence.
- `botsite/tests/test_catalog_sha_drift.py` (new, 13 tests, network-free
  via `httpx.MockTransport`): grammar (well-formed / malformed source
  shapes), unchanged/changed/unreachable-pin/unreachable-main verdicts,
  non-pinned entries skipped not flagged, empty-registry alert, and a
  mixed end-to-end registry.
- **Live-verified before shipping** (this session's own network access,
  not the pytest suite): ran `probe_catalog_sha_drift()` for real against
  the committed `catalog.json` and the real `menno420/venture-lab` repo —
  found **9 of 22** pinned packets have genuinely drifted (`merge-wall-cookbook`,
  `ultramarine`, `de-waag`, `het-trage-woord`, `de-papieren-sinaasappel`,
  `bundle-starter`, `photo-packs`, `the-night-kiln`, `the-paper-orange`).
  `ultramarine` and `de-papieren-sinaasappel` line up with OWNER-ACTIONS
  ASK-0014/ASK-0016 (open owner decisions on those exact titles) — a
  plausible, not suspicious, correlation. Did NOT chase re-verifying or
  fixing all 9 in this slice (scope: build the pin, not resolve every
  finding it surfaces) — flagged in this card and the heartbeat instead.
- **Fixed 3 pre-existing test regressions** the new healthcheck wiring
  caused: `test_healthy_arcade_keeps_main_exit_zero`,
  `test_no_drift_keeps_main_exit_zero`,
  `test_healthy_tasks_keep_main_exit_zero` each stub every OTHER pass
  healthy to isolate their own target check — none stubbed the new
  `check_catalog_sha_drift`, so `main()` picked up the 9 real flags and
  those "should be exit 0" tests started failing. Added the same stub to
  all six `main()`-calling tests across the three files (their own
  docstrings promise "nothing touches the network" — the new check had to
  honor that too).
- Logged the raw.githubusercontent.com discovery in `docs/CAPABILITIES.md`
  (2026-07-16 capability entry) and regenerated `docs/seat-digest.md`
  (derived from the capability ledger — `bootstrap.py seat-digest`, never
  hand-edited).
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — **1644 passed** (1631 baseline + 13 new); `python3
  bootstrap.py check --strict` — all checks passed (clean after the
  seat-digest regen — it flagged stale beforehand).

⚑ Self-initiated: yes — ORDER 032's backlog-slice mandate. This idea had
been deprioritized twice by this lane's own earlier heartbeats on an
unverified assumption ("needs live API, this session has none") — worth
flagging as a lesson: check the actual wall before writing off an idea on
its account.

## Landing

Same named blocker as every branch this lane has pushed tonight:
**ASK-0017**. Pushed for an interactive session or the owner to open/merge.

## 💡 Session idea

**Regenerate `catalog.json`'s stale pins after this pin lands** — 9 of 22
entries are flagged drifted right now; once this probe is live (post-ASK-0017),
a follow-up session should re-verify each against its current venture-lab
packet and either update the pinned sha (if the change was benign — e.g. a
status-note wording fix) or flag a real content change for the owner (e.g.
a price or verdict shift). Worth having because shipping the pin without
ever acting on its first real finding wastes the whole point of building
it. Deduped against `docs/ideas/backlog.md`: no existing bullet covers
acting on a specific drift finding (only the general pin-building idea,
now built). Captured in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

The claim-PR-fallback slice (this lane, ~23:10Z) correctly ruled out the
catalog sha-drift pin as "needs live API this session doesn't have" —
reasonable at the time, but this session found that assumption was never
actually tested, just inherited from the general ASK-0017 landing wall
(a DIFFERENT wall — REST API vs. raw content — that nobody had separately
probed). Lesson applied: test the specific wall an idea is being skipped
for, don't generalize from an adjacent one.
