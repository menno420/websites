# websites — curated next tasks (for the recreated project)

> **Status:** `plan` — the short, ranked, de-duplicated next-task set for the
> **recreated** websites project. Distilled 2026-07-17 (fresh-start cleanup)
> from the two overnight veto menus and `docs/ideas/backlog.md`:
> - `docs/planning/arcade-dashboard-menu-2026-07-16.md` (24 arcade/dashboard
>   proposals, on `main`);
> - the console + review menu (37 proposals C1–C21 / R1–R14 + 2 cross-cutting),
>   authored on the closed PR #375 branch `claude/console-review-menu-20260716`.
>
> **NOT SOURCE OF TRUTH** — source files win. The full menus keep the long tail;
> this file is the curated top slice grouped by the four Railway services. Effort
> **S/M/L**; risk **✅** safe · **↩️** reversible · **⚠** needs a decision/credential.

## Already shipped from the menus (do not re-propose)

Landed during the 2026-07-17 clearance and just after — prune these on sight:
- **A1** → games front-door launch-readiness summary (**#371**).
- **A3** → arcade owner-action queue, full list not just a count (**#381**).
- **B5** → dashboard `/ideas` filtered by lifecycle state (**#382**).
- **R-side evidence tally** → Successes/Problems hero evidence count (**#383**).
- **C10** → single-source guard test for Railway `/version` deploy-probe URLs (**#377**).
- Also-shipped idea files to prune from `docs/ideas/`: `activity-atom-feed`,
  `activity-per-repo-filter`, `scheduled-healthcheck-workflow`. Still live:
  `merge-hold-at-head`, `open-pr-awareness-at-wake`.

---

## Ranked next tasks (5–8 best), grouped by service

### 1 · control-plane (`app/`)

- **[P1] Self-cleaning owner queue — askverify re-checks the underlying condition**
  (console menu **C14**, M · ✅). Extend `app/askverify.py` to re-verify that an
  ask's *underlying* condition still holds at each board render (secret still
  unset, Postgres still unprovisioned) so a resolved ⚑ auto-clears instead of
  nagging. *Unblocks:* an owner queue that shrinks itself; less owner attention burned.
- **[P2] Durable ask IDs** (console menu **C15**, M · ↩️). Owner asks are
  positionally identified (`askverify.py`), so reordering the ledger breaks
  writeback targeting. Assign stable IDs. *Unblocks:* C14 above and any
  cross-session ask reference; foundational, do it before C12/`/owner/history`.
- **[P3] Honest counts — distinguish "counter failed" from "genuine zero"**
  (console menu **C1**, S · ✅). The `_count_*` helpers fail-soft to `—`, so a
  failed fetch is indistinguishable from a real zero on `/work` `/history`
  `/console`. Add an "unavailable" glyph/tooltip. *Unblocks:* trustworthy
  at-a-glance counts. (Cheap first win.)

### 2 · review (`review/`)

- **[P1] Make the `/questions` surface earn its code** (review menu **R1**, S · ✅).
  `questions.json` is empty and the page is not in NAV — the `story.py`
  answer-debt/latency engine + `gen_questions.py` currently surface nothing. Add
  `/questions` to NAV and seed it from the anticipated Q&A in `QUESTIONNAIRE`.
  *Unblocks:* a whole built subsystem becomes visible to reviewers.
- **[P2] Continuous reviews — auto-draft the next edition from snapshot deltas**
  (review menu **R10**, M · ↩️; needs **R8** stats-history first). The editions
  system + Atom feed are built for a single 2026-07-11 file; a bake step that
  drafts a new edition body from snapshot/stats deltas makes the "continuous
  review channel" actually continuous. *Unblocks:* the review site shows momentum,
  not a still frame. *(Any bake-step / workflow change lands as its OWN PR.)*
- **[P3] Unit-test the three untested bake generators** (review menu **R6**, M · ✅).
  `gen_snapshot.py` / `gen_fleet.py` / `gen_stats.py` have no dedicated unit tests.
  *Unblocks:* trustworthy bake output — pairs with any bake change above.

### 3 · botsite (`botsite/`)

- **[P2] Arcade JSON schema CI guard** (arcade menu **A4**, S · ✅). Add a
  test/CI assertion that every `arcade.json` entry passes full schema + enum +
  blocker validation, so a malformed new game fails the build instead of
  silently dropping. *Unblocks:* safe game onboarding by non-authors.
- **[P3] Cross-link `/games` ↔ `/arcade`** (arcade menu **A2**, S · ✅). Neither
  template points at the other; add a one-line pointer strip in each so the two
  overlapping surfaces stop being dead ends. *Unblocks:* discoverability.

### 4 · dashboard (`dashboard/`)

- **[P2] Arcade live/blocked counts on `/status`** (dashboard menu **B1**, S · ↩️).
  Source arcade fleet-readiness counts from botsite's committed `arcade.json`
  over `raw.githubusercontent.com` (same mechanism as `console.json`), so one
  dashboard glance covers games too. *Unblocks:* single oversight surface for
  bots **and** games. Honors read-only, forward-only — never a live import.
- **[P3] Config-drift flags on `/env`** (dashboard menu **B6**, M · ↩️).
  Cross-check `/env` usage against a committed manifest and flag
  referenced-but-unset / set-but-unused vars — the same class as the two
  password-variable cleanups in `docs/OWNER-STEPS.md`. *Unblocks:* config drift
  is visible before a deploy surprises someone.

### Cross-cutting quick win

- **Bundle the pure test/guard adds into one green PR** (console menu **X2**):
  the remaining **C9** (pagination-truncation tests) + **C11** (cache-eviction
  test) + **R6** + **R7** are behavior-free coverage — landable together the
  moment the recreated project is live.

---

## Wind-down / retirement (do during / at recreation)

The autonomous apparatus is being retired (EAP read-only 2026-07-21; the
~2026-07-15 classifier froze autonomous merges). Retire on recreation — **none
of this is app/ source or a live site; do NOT delete workflow files or `app/`
in this cleanup PR**, only inventory them:

- **Workflows** — `.github/workflows/auto-merge-enabler.yml`,
  `host-automerge-extras.yml`, `quality-main-sweep.yml` (auto-merge/sweep
  apparatus); `review-bake.yml` (nightly bake — keep only if `BAKE_PAT` is
  provisioned, see `docs/OWNER-STEPS.md`); `healthcheck.yml`, `smoke-crawl.yml`
  (scheduled cron probes). Keep `quality.yml` — the required check stays.
- **Message bus** — `control/inbox.md`, `control/outbox.md`, `control/status.md`,
  `control/README.md`, `control/claims/` (no active claims).
- **Wake/seat apparatus docs** — `docs/ROUTINES.md`, `docs/seat-digest.md`,
  `docs/succession/`; and the external failsafe routine
  `trig_01VRT9F6jYNXym3nn18vVQQK` ("Websites failsafe wake").
- **Hand-kept fallbacks** — `app/roster.py` + `app/config.py` `FLEET_LANES`
  (fallback copy of the fleet-manager auto-generated roster/registry).
- **Boot docs** — on recreate, keep the lean triad (`.claude/CLAUDE.md` →
  `HANDOFF.md` → `docs/current-state.md`) but strip references to the retired
  routine/heartbeat/coordinator apparatus.

## Owner-gated (not agent tasks)

The 16 ⚑ asks in `docs/owner/OWNER-ACTIONS.md`; the console-only subset for this
repo (SITE_PASSWORD gate, BAKE_PAT, the two unused/unwired password variables)
is in `docs/OWNER-STEPS.md`. The bigger product calls — where live bot-control
lives (Q-0004), the botsite submissions ring (Postgres + PayPal), Discord OAuth
— stay owner decisions and gate the ambition items above (C20, R12, A11/A14).
