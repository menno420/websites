# 2026-07-09 — ORDER 001: deploy-state drift cell (readiness board websites row)

> **Status:** `complete` — the manager's ORDER 001 shipped forward-only through
> the required `quality` gate. The control-plane readiness board's **websites
> row** now carries a **deploy-state drift** cell (deployed SHA vs `main` HEAD),
> and all three services expose an unauthenticated `/version` JSON. Card opened
> together with the real work (the STRICT gate fails a born-red card, so this is
> not opened empty).

## Fleet ritual (STEP 1)

- Pulled latest `main` (`276b93e`). **`control/README.md` and `control/inbox.md`
  are BOTH ABSENT** — 404 on raw GitHub after 3 retries over ~60s, and the prior
  `status.md` already flags the contract file as absent. Proceeded on the existing
  sensible `status.md` format and flag the absence under ⚑ needs-owner (unchanged
  from last session). **No inbox to ack into → ORDER 001 acked in `status.md` only**
  (did NOT create/edit `control/inbox.md`, since no README authorizes builders to).

## What shipped (ORDER 001)

**Goal:** the readiness board's websites row shows deploy-state drift — the
DEPLOYED commit SHA vs `main` HEAD — so the owner sees at a glance whether the
live site runs the latest merged code.

1. **Each service knows its deployed SHA.** New `/version` JSON endpoint
   (unauthenticated, like `/healthz`) on **all three** apps —
   `app/main.py` (control-plane), `botsite/app.py`, `dashboard/app.py` —
   returning `{"service", "sha", "short"}`. Read order (live from env, no
   network): **`RAILWAY_GIT_COMMIT_SHA`** (Railway injects the deployed commit —
   PRIMARY) → **`GIT_SHA`** (baked at Docker build — FALLBACK) → `"unknown"`.
   control-plane's shape lives in `app/config.py` (`deployed_sha()` /
   `version_info()`); botsite/dashboard each carry a small self-contained
   `_version_info()` (separate Railway services, separate build contexts).
2. **Dockerfile build-arg fallback.** All three Dockerfiles gain
   `ARG GIT_SHA="" ` → `ENV GIT_SHA=$GIT_SHA`. Optional — the runtime primary is
   `RAILWAY_GIT_COMMIT_SHA`, which Railway provides automatically, so the feature
   works with **no Railway build-arg wiring**. No secret added.
3. **Board deploy-state cell (websites row).** `app/readiness.py`:
   `_service_deploy_state()` + `_deploy_board()` compute, for each websites
   service, DEPLOYED short-sha vs the `main` HEAD short-sha the board already
   fetches live (`head_sha` from check-runs). control-plane reads its own
   deployed sha directly from env (no network); botsite/dashboard are fetched
   over their public `/version` through the existing TTL-cached raw client. The
   cell renders `in sync` (deployed == head), `DRIFT` (deployed ≠ head, both
   shown), or `unknown` (fetch failed / sha unset — honest, never faked). Only
   the websites row gets the cell (`deploy_state` is `None` for the other three
   repos, template-guarded). `app/templates/board.html` renders the new row;
   mobile-safe (inside the existing `min-width:520px` scroll card).

## Verification (STEP 3)

- **Tests:** `pytest tests/ botsite/tests dashboard/tests -q` → **95 passed**
  (was 84; +11: control-plane deploy-state in-sync / DRIFT / unknown-clean +
  `/version` env + unknown; botsite & dashboard `/version` env / fallback /
  unknown).
- **Kit gate:** `python3 bootstrap.py check --strict --require-session-log
  --session-log .sessions/2026-07-09-order-001-deploy-drift.md` → green.
- **Local live-verify** (api.github.com is proxy-blocked in the sandbox, so a
  tiny local mock returned the REAL `main` head `f2e2a1d5…`; botsite/dashboard
  `/version` legitimately 404 pre-deploy → shown `unknown` honestly):
  - `GIT_SHA=deadbeefdeadbeef` → `/version` `{"service":"control-plane","sha":"deadbeefdeadbeef","short":"deadbeef"}`; board cell **DRIFT** — `control-plane DRIFT deployed deadbeef ≠ head f2e2a1d5`.
  - `GIT_SHA=f2e2a1d5…` (== real head) → `/version` short `f2e2a1d5`; board cell **in sync** — `control-plane in sync f2e2a1d5`, head `f2e2a1d5`.
  - Unknown path (no env var) renders cleanly (`deploy state` + `unknown`), no crash.
- **Post-merge live-verify** (all three redeploy from `main`): recorded in this
  card + `control/status.md` after merge — control-plane `/version` real sha,
  board websites row `in sync` (deployed == head), botsite + dashboard `/version`
  shas, all `/healthz` 200, `scripts/healthcheck.py` all green.

## Rails held

Forward-only (fresh branch, no force-push/amend of pushed refs). Only the
`websites` repo touched. **No** `RAILWAY_API_KEY` / secret added; **no** ambient
production `RAILWAY_*` IDs read (the CI guard stays green). No destructive Railway
ops. `/version` is unauthenticated public data (a git sha), consistent with the
public-surface posture.

## ⚑ Self-initiated

None beyond the directed order — ORDER 001 is manager-directed. (Kept the overall
"working now?" badge honest: it reads `in sync` only over services whose sha is
*known*; unknown services show `unknown` per-cell rather than being counted as
green or red.)

## 💡 Session idea

**Make the deploy-state cell time-aware — surface a "drifting for N min" age when
DRIFT persists.** A momentary DRIFT right after merge is normal (a redeploy in
flight); a DRIFT that *stays* for many minutes means a **failed or stuck deploy**
— a genuinely different, alert-worthy state. The board already fetches `head_sha`
live; recording the first-seen timestamp of a given `(service, deployed≠head)`
pair (in the existing in-memory cache) lets the cell distinguish "deploying…"
from "stuck" without any new dependency or credential — turning a status readout
into an early failed-deploy signal, the same enforce-don't-exhort instinct the
estate favors.

## ⟲ Previous-session review

The born-red-gate fix (PR #24, [D-0017]) did the right, durable thing: it didn't
hand-patch the vendored `bootstrap.py` but **adopted the upstream kit v1.0.0**
that fixes both leak holes and ships regression tests both directions — keeping
this repo a faithful kit *consumer* rather than a fork. What it (correctly, by
scope) left: the `control/README.md` coordination contract is still **absent**,
so every builder session re-derives the `status.md` format and re-flags the gap
(this session included) — a recurring per-session friction. **Workflow
improvement surfaced:** the fleet-coordination contract is itself a
friction→guard candidate — until `control/README.md` lands, the ack convention
and status format are tribal knowledge each session must reconstruct. Flagged
again under ⚑ needs-owner in `status.md` so the manager/owner commits the
contract; once it exists, a tiny `scripts/` checker could assert `status.md`
conforms, closing the drift class.
