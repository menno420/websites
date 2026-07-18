# 2026-07-17 — Dashboard arcade live/blocked counts (B1)

> **Status:** `complete` — branch `claude/dashboard-arcade-counts`; the dashboard
> `/status` page now shows a fleet-arcade line — total games · N live · M blocked —
> read from the committed `botsite/data/arcade.json` over raw.githubusercontent.com
> (the same TTL-cached fetch the bot feeds use), degrading to an honest "counts
> unavailable" when the feed can't be fetched (never a faked 0). +4 tests.

- **📊 Model:** Claude Opus · high · feature build (dashboard arcade counts)

**What this session is about:** the dashboard `/status` page shows inventory
counts for the bot (subsystems, cogs, commands, ideas, bugs …) but said nothing
about the fleet arcade. B1 (NEXT-TASKS §1) adds an arcade line to `/status`:
total games with a live count and a blocked count, read live from the committed
`botsite/data/arcade.json` over raw.githubusercontent.com — an additive,
read-only GET render, no state change, no new credential, no cross-service
import.

⚑ Self-initiated: no — coordinator-dispatched backlog slice (B1) of the standing
overnight ORDER 032.

## Close-out

**Evidence:**

- files touched this branch: `dashboard/data_source.py` (new `ARCADE_JSON_URL`
  env-overridable feed pointing at `menno420/websites@main/botsite/data/arcade.json`
  — the registry lives in THIS repo, not superbot; a `fetch_arcade()` fetcher
  over the existing `_fetch` TTL-cache/fail-soft envelope; and a pure
  `arcade_counts()` helper that re-derives live/blocked over the RAW feed shape —
  the enriched `has_link`/`is_live` fields are computed by botsite's loader and
  are NOT in the committed file — mirroring `botsite.arcade.availability_summary`
  without a forbidden cross-service import); `dashboard/app.py` (the `/status`
  route fetches the arcade feed and passes `arcade_ok` / `arcade_error` / `arcade`
  counts, gated so a failed fetch renders honestly); `dashboard/templates/status.html`
  (a new arcade status-banner row: "N games · N live · M blocked" when the feed is
  ok, "counts unavailable — arcade feed could not be fetched" otherwise);
  `dashboard/tests/test_dashboard.py` (+4: the pure helper on a known fixture, its
  fail-soft on bad input, a `/status` render showing the live/blocked counts, and
  an honest-degrade test that a failed fetch shows "unavailable" and never a faked
  "0 live" — plus an `ARCADE_FIXTURE` primed into both client helpers so the suite
  stays network-free); `tests/test_hostile_env_smoke.py` (pin the new
  `ARCADE_JSON_URL` read into the hostile-env import smoke — the poison-pin
  contract test `tests/test_env_poison_pin.py` requires every service env read be
  covered); this card + `control/status.md` heartbeat.
- git: branch `claude/dashboard-arcade-counts` from `origin/main` @ `1365a66`
  (#387); commits `8ec9779` (born-red card), `b4bf304` (build), `41a635b`
  (tests), `dd37ed3` (env-pin), `230cf8f` (heartbeat status), + this flip.
- verify: `python3 -m pytest tests/ botsite/tests dashboard/tests review/tests
  -q` — **1729 passed, 1 warning**; `python3 bootstrap.py check --strict` (and
  `--require-session-log`, the CI form) — the only red during the session was the
  DESIGNED born-red hold on this card, released at this flip; no serialized JSON
  payload/contract changed (the arcade line is HTML-only), so no contract-pin
  moved beyond the env-read poison pin.

**Judgment:**

- Decisions made: (1) the arcade feed is a THIRD raw feed, not a botsite import —
  the import rules forbid `dashboard/` importing `botsite/`'s package, so
  `arcade_counts()` re-derives the same live/blocked semantics
  (`live` = a reachable play/download link: availability live/download AND a url;
  `blocked` = the honest inverse) over the committed list shape, keeping the two
  surfaces consistent without coupling them; (2) the feed URL points at
  `menno420/websites@main` (arcade.json is hand-maintained in THIS repo), not
  superbot like the bot feeds — env-overridable so a fork/branch can repoint it;
  (3) honest degrade reuses the module's existing `ok`-envelope discipline — the
  route only computes counts when `arcade_ok`, and the template shows "counts
  unavailable" rather than a faked `0 live / 0 blocked`, the same never-fake-data
  posture the bot feeds already carry; (4) additive read-only GET — no
  state-changing route, no CSRF/Origin surface touched, no new credential.
- Next session should know: the arcade feed is now a pinned dashboard dependency
  (`ARCADE_JSON_URL`, poison-pinned). A natural follow-on is A4 (an arcade JSON
  schema CI guard so a producer-side shape change surfaces before it reaches this
  consumer), and the idea below (a render-time arcade schema-drift banner mirroring
  the console/dashboard feed pins).

## 💡 Session idea

**Pin the arcade feed's shape the way console.json is pinned.** The dashboard
already guards `console.json` and `dashboard.json` at render time against a
committed version/shape contract (`console_contract_issue` /
`dashboard_schema_issue`) and banners drift honestly. The new arcade feed has no
such pin — `arcade_counts()` is fail-soft but a producer-side field rename would
just silently shift the live/blocked split with no signal. A small
`arcade_contract_issue()` mirroring the existing pins (expected keys per entry:
`availability`, `url`, optional `blocker`) would make an upstream arcade.json shape
change visible on `/status` instead of quietly miscounting — the same cross-repo
drift-visibility discipline, extended to the third feed. Captured for the backlog
at flip (dovetails with A4, the arcade schema CI guard).

## ⟲ Previous-session review

`.sessions/2026-07-17-self-cleaning-owner-queue.md` (C14) held its "reuse a
computed signal where the owner acts, add zero network surface" discipline — but
its own ⟲ note flagged that pattern still isn't routed into `docs/SKILLS.md`, so
this B1 slice re-derived the "third raw feed, fail-soft, honest-degrade" recipe
from the console-feed code rather than from a routed skill; the recurring
feed-consumer recipe is worth planting there before a fourth consumer re-derives it.
