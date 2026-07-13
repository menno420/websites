# 2026-07-13 — healthcheck: probe review service + true current-state figures

> **Status:** `in-progress`

- **📊 Model:** Claude 5 family · worker · build

**What this session is about:** two-task truing pass. Task 1: the
`scripts/healthcheck.py` SERVICES list omits the review service (found by
a prior session) — find the review service's DOCUMENTED production URL
(no guessing), probe it live once, and add it to SERVICES in the script's
existing per-service style; if genuinely undocumented, record the negative
finding instead of inventing a probe. Task 2: `docs/current-state.md`
cites a stale suite figure (1206) and pre-sitting state — run the full
four-suite pytest run, true the test count and today's merged PR range
(#277→#290, main at/past 6360263) with surgical edits only, keeping the
Status badge within the first 12 lines.

## What was done

- **Task 1 — healthcheck coverage gap closed.** Verified at HEAD `6360263`
  that `scripts/healthcheck.py` SERVICES still listed only control-plane /
  botsite / dashboard. The review service's production URL IS documented:
  `https://review-production-f027.up.railway.app` (docs/current-state.md
  "The Railway service is LIVE at…", `app/config.py`
  `SERVICE_DEPLOY_TARGETS`, `docs/owner/OWNER-ACTIONS.md` Decided row J).
  The fc91 URL in `app/data/web_presence.json` is the labeled "parallel
  copy" — not canonical, not added. Probed the f027 URL live once:
  `/healthz` → 200, `/` → 200. Added `("review", …f027…)` to SERVICES in
  the script's exact existing style (same /healthz + / probe pattern; no
  new env-var read, so no `_env_int` guard needed) and trued the script's
  three-services header prose to four. New pin
  `tests/test_healthcheck_services.py` (module loaded via the same
  importlib pattern as `tests/test_healthcheck_registry.py`): full
  four-service table, review = canonical f027 (never fc91), no trailing
  slashes.
- **Task 2 — docs/current-state.md trued.** Badge line: stale "suite 1206"
  → 1255 (this session's full four-suite run: `1255 passed`; 1252 at #290
  + 3 new pins) and the update note now names the post-ender wave
  #277→#290 with main at `6360263`. Healthcheck habit line: "3 live URLs"
  → 4 (with the gap provenance). New "Recently shipped" entry for the
  same-day post-ender wave #277→#290 (each PR verified on `main` via
  `git log`). Status badge stays on line 3 (within the first-12-lines
  docs-gate rule). Surgical — nothing else rewritten.

## 💡 Session idea

- (pending close-out)

## ⟲ Previous-session review

- (pending close-out)
