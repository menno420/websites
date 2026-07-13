# 2026-07-13 — healthcheck: probe review service + true current-state figures

> **Status:** `complete` — branch `claude/healthcheck-review-truing-0713`,
> PR #291 opened READY (not draft) against main; merge is the auto-merge
> lane / owner's call — this worker opens, never merges.

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

- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — `1255 passed, 1 warning in 67.34s` (was 1252; +3 new
  pins); `python3 bootstrap.py check --strict` — green apart from this
  card's designed born-red hold, released at this flip. The truing edits
  briefly tripped the kit's orientation-budget gate (boot set 7120 > 7000
  words); resolved by compressing the two already-Done "Next steps" items
  and the verbose kit-version upgrade chain in the same file.
- Pre-session note: the workspace carried uncommitted
  `.substrate/state.json` churn at boot; banked on rescue branch
  `claude/rescue-2026-07-13-healthcheck-presync` (`d64a537`) before the
  hard-sync to `origin/main` @ `6360263`.

⚑ Self-initiated: no — assigned two-task change; contained + reversible
(one list entry + a pin test + doc truing; revert the PR to undo).

## 💡 Session idea

**Service-URL inventory consistency pin** — the four production base URLs
now live hand-kept in at least four places (`scripts/healthcheck.py`
`SERVICES`, `app/config.py` `SERVICE_DEPLOY_TARGETS`, `app/railway.py`
`SERVICES`, `app/data/web_presence.json`); a small cross-check test in the
`tests/test_inventory_consistency.py` mold (assert every deploy-target
service appears in the healthcheck table with the same host, fc91
parallel-copy excluded) would have caught this session's exact gap — the
review service was documented in config on 2026-07-12 yet the healthcheck
table lagged a full day. Worth having because hand-kept URL copies drift
silently and the estate keeps adding services. Deduped against
`docs/ideas/backlog.md` (healthcheck bullets probe live URLs; the
inventory-consistency bullet covers env-var names, not service URLs) and
`.sessions/` cards — no existing capture.

## ⟲ Previous-session review

The webhook-analyzer session (.sessions/2026-07-13-webhook-analyzer.md,
PR #266) did well: its born-red → build → flip ritual and honest
grounding-tier discipline transplanted cleanly here; what it left behind
is still open — its own card flags that the 💡 backlog bullet was never
added to `docs/ideas/backlog.md`, and as of this session that follow-up
has still not landed.
