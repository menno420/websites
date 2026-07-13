# 2026-07-13 — environments rollup on the authed owner readiness JSON

> **Status:** `complete` — PR #246, branch `claude/readiness-env-rollup`;
> `GET /owner/api/readiness.json` now carries the board chip's
> `envhub.board_rollup` dict under a top-level `environments` key, contract
> pinned per the #217 precedent; lands via the auto-merge enabler on green.

- **📊 Model:** Claude Fable 5 · worker · backlog-promotion

**What this session was about:** promote the captured backlog bullet
"Environments rollup in the authed /owner readiness JSON"
(`docs/ideas/backlog.md`, captured 2026-07-12 by the owner-board env-chip
session 💡) under ORDER 022's night-run quality floor: the board chip's
rollup (`envhub.board_rollup`, PR #223) renders on the `/owner` HTML only,
so a script or agent wanting the "N groups incomplete" signal must scrape
HTML. Attach the same rollup dict to `GET /owner/api/readiness.json` as a
top-level key with the honest `unknown` passthrough intact, and pin the
JSON contract (keys, states enum, never-values) per the #217
`/fleet.json` contract-pin precedent (`tests/test_fleet_json_contract.py`).

## What was done

- **`app/owner.py` `owner_board_json`**: the authed JSON becomes an object
  — the board rows (unchanged shape, `reveal_secrets=True`) under `rows`
  plus the SAME `envhub.board_rollup` dict the HTML chip renders under
  `environments`, gathered concurrently. Same TTL-cached
  `railway.live_overview` read the board/hub already make — zero new
  network surface, zero new routes; Basic auth gate untouched, GET-only.
  Conscious top-level contract change (bare list → object) flagged in the
  PR body per the #217 pin rule — a list cannot carry the rollup key.
- **Honest unknown passthrough**: registry unreadable / `RAILWAY_TOKEN`
  unset / live read failed → `state: "unknown"` WITH the exact reason,
  never a fabricated green or "incomplete: 0"; out-of-scope groups count
  as unknown — all inherited from `board_rollup`, zero forked semantics.
- **`tests/test_owner_readiness_json_contract.py`** (new, 8 tests): the
  #217 contract-pin style — top-level key set pinned (`rows`,
  `environments`), `environments` key set pinned verbatim, states enum
  pinned (`{ok, unknown}`), honest-unknown-with-reason for token-unset and
  live-read-failure, ok-state bucket exhaustiveness
  (`complete + incomplete + unknown == groups`), never-values (no live
  value sentinel / Railway token / owner password in the body), 401 gate,
  405 on POST. Fully offline.
- **`docs/ideas/backlog.md`**: the source bullet flipped `captured` →
  `built` (PR #246).
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — 1042 passed, 1 warning; `python3 bootstrap.py check
  --strict` — green apart from this card's own designed born-red HOLD
  (flipped by this close-out) and the pre-existing `owner-action-fields`
  advisory on control/status.md (never exit-affecting, not owned here).

**Decisions made:** the top level wraps as `{"rows", "environments"}`
rather than growing a parallel route — the bullet asks for a top-level key
and a bare list cannot carry one; the rollup key is named `environments`
(what the chip is about, matching /fleet.json's `coverage` naming style)
and the dict ships verbatim — no re-shaping, so the JSON and HTML chip can
never disagree.

⚑ Self-initiated: no — backlog promotion (`docs/ideas/backlog.md`
"Environments rollup in the authed /owner readiness JSON") under ORDER 022
item 2 (keep executing the existing plan; quality floor).

## 💡 Session idea

**Surface the environments rollup in `scripts/healthcheck.py`** — the
backlog bullet's own "why" names the scheduled healthcheck as the machine
that should consume this JSON when the owner is not looking, but the cron
probe today checks service liveness only; one authed read of
`/owner/api/readiness.json` (password already in the service env) could
report `environments.state`/`incomplete_names` alongside the liveness
rows. Worth having because the rollup now exists machine-readably yet
nothing scheduled actually reads it — the honesty ladder still only helps
while someone is looking. Deduped against `docs/ideas/backlog.md` + the
queue-state NEXT list: the env-drift and inventory-consistency bullets pin
committed inventories, nothing consumes the live rollup from the cron
probe. Captured in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

The repo-freshness-page session (#235) did well — its conscious
manifest-pin updates landing in the same commit as the route they pin is
the discipline this session copied by pinning the new JSON shape in the
same PR that changes it; what it missed (its own 💡 admits it) was wiring
the existing autorefresh into the new page — reuse the machinery that
already exists, which here meant shipping `board_rollup` verbatim instead
of re-shaping it.
