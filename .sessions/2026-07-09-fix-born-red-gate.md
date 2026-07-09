# Session 2026-07-09 — fix the leaky born-red session gate (adopt kit v1.0.0)

> **Status:** `complete` — born-red gate fix, [D-0017]. Card opened `complete`
> with the work present (the gate is being fixed here — an `in-progress` card
> could premature-merge this very PR empty until the fix lands).

- **📊 Model:** claude-opus-4-8 (pre-v1.2.0 backfill; builder-session subagent, inherited — not independently confirmed)

## What I did

Closed the born-red session-gate leak that let **PR #19 auto-merge an
effectively-empty PR on its `in-progress` card alone**, by **adopting** the
upstream substrate-kit **v1.0.0** fix — not by hand-patching the vendored engine.

- **Diagnosed two holes** (both confirmed present in the vendored pre-1.0.0
  `bootstrap.py`, absent at kit-main HEAD `eb540d9`):
  - **Hole #1** — `check --strict --require-session-log` verified only that the
    session-card MARKERS were present, never the Status VALUE, so a born-red
    (`in-progress`) card passed strict (`grep -c status_in_progress` → 0 in the
    vendored copy).
  - **Hole #2** — the "current" card was picked newest-by-mtime, which a fresh CI
    checkout flattens to checkout time, so an OLD `complete` card could mask THIS
    PR's `in-progress` one.
- **Re-vendored** kit-main HEAD `dist/bootstrap.py` (kit **v1.0.0**): old md5
  `85884a8c…` (no `KIT_VERSION`) → new md5 `af8418e0…` (`KIT_VERSION = "1.0.0"`).
  The v1.0.0 checker adds `status_in_progress()` (`in-progress`/`in progress`/
  `wip`/`hold`/`drafted` → fail under `--strict`, **not allowlistable**) and a
  `check --session-log <file>` option (explicit, diff-aware card selection).
- **Config:** recorded `"kit_version": "1.0.0"` in `substrate.config.json` — the
  only change the new engine needs; `check --strict` otherwise reads the existing
  config clean (**no migration**, verified).
- **Wired enforcement into the single `quality` gate.** Rather than add the kit's
  separate `substrate-gate.yml` (which would create a second, conflicting
  session-log path), I folded the kit's **exact generated** diff-aware step
  (byte-faithful to the engine's `live_ci_workflow`, captured from a throwaway
  `adopt --wire-enforcement` run) into `.github/workflows/quality.yml`: derive
  `card` from `git diff` under `.sessions/` and pass `${card:+--session-log
  "$card"}`, with `fetch-depth: 0` on checkout. **One required enforced path, no
  double logic.** The Railway-ID guard + pytest steps are untouched.
- **Regression test** `tests/test_born_red_session_gate.py` (4 tests) drives the
  real CLI so a re-opening of either hole reddens the suite.
- **Upstream note:** the substrate-kit repo fix itself is handled by a **separate
  session** — substrate-kit is read-only reference here; untouched (no collision).

## Verification — both directions proven (verbatim)

Reproduced #19 in a scratch install: a stale `complete` card made newest-by-mtime
+ a born-red `in-progress` card the PR "added".

- **Hole #2 demo (the leak):** mtime fallback (no `--session-log`) picks the stale
  complete card → `check: session log .sessions/2026-07-01-old-done.md complete.` /
  `check: all checks passed.` → **EXIT=0** (wrongly passes — this is what let #19
  merge).
- **Direction A (FAIL):** diff-aware `--session-log .sessions/2026-07-09-born-red.md`
  → `check: session log …born-red.md is missing: a completed Status (badge still
  says in-progress)` → **EXIT=1**.
- **Direction B (PASS):** same card flipped `complete`, same command → `check:
  session log …born-red.md complete.` / `check: all checks passed.` → **EXIT=0**.

Full suite green: `python3 -m pytest tests/ botsite/tests dashboard/tests -q` →
**84 passed** (incl. the 4 new); `python3 bootstrap.py check --strict
--require-session-log` green on this branch; Railway-ID guard green.

## 💡 Session idea

**A "vendored-engine freshness" check.** The whole leak existed because the
vendored `bootstrap.py` silently drifted behind kit-main across a major fix. A
tiny CI/journal check that reads `config.kit_version` (now recorded) and compares
it to the vendored engine's `KIT_VERSION` constant — warning when the repo is more
than one minor behind kit-main's latest release — would surface this class of drift
before it bites, the same way the ambient-Railway-ID guard surfaces its class.
(Captured as a follow-up, not built this session.)

## ⟲ Previous-session review

PR #21 (botsite content depth) was strong content work and correctly kept the
never-fake-data rail (thin real changelog surfaced honestly, not padded with
invented releases). What the whole recent chain **missed** is exactly this bug:
the born-red gate was treated as working (PRs #19/#20 leaned on it) when it was
structurally leaky — a gate that reads as protection but doesn't hold is worse than
none. **System improvement it surfaces:** enforcement guards should ship with a
*both-directions* proof at adoption time (a FAIL case, not just a PASS), because a
guard is only trustworthy once you've seen it actually reject the thing it targets —
this session added that missing FAIL-direction test, and that discipline
(negative-case proof for every guard) should be the default for future guards.

## Rails held

Only `menno420/websites` touched (substrate-kit + superbot/superbot-next read-only
reference, untouched). Forward-only (fresh branch, no force-push/amend of pushed
refs, no branch-delete). CI/tooling/docs only — no app code, so no Railway redeploy
needed for behavior. No ambient production `RAILWAY_*` IDs read; no secret added; no
production mutation. Own PR opened with card `complete` + work present so the
now-strict gate can't premature-merge it empty.
