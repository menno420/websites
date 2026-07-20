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

> **Current groomed queue:** `docs/plans/next-cycle-2026-07-19.md` — the
> HEAD-stamped (`7dfdca2`, #447) executable frontier (6 value-ranked slices +
> routed-out tail), superseding `docs/plans/next-cycle-2026-07-18.md` (the prior
> pass, fully executed). This file is the ranked menu; that doc is the dated
> planning pass on top of it.

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

## Verified shipped (as of #421)

The 2026-07-18 planning pass verified these ranked items against the tree — all
landed. Moved out of the open ranked list so no future session re-proposes them;
one-line evidence each:
- **C14** — self-cleaning owner queue (askverify re-checks the underlying
  condition). Shipped: `app/askverify.py` `auto_cleared`.
- **C15** — durable ask IDs (stable ids, not positional). Shipped:
  `tests/test_durable_ask_ids.py`.
- **C1** — honest counts (distinguish "counter failed" from "genuine zero").
  Shipped: `tests/test_console_honest_counts.py`.
- **A4** — arcade JSON schema CI guard. Shipped:
  `botsite/tests/test_arcade_registry_integrity.py`.
- **A2** — cross-link `/games` ↔ `/arcade`. Shipped: `games.html` ↔ `arcade.html`
  cross-links.
- **B1** — arcade live/blocked counts on dashboard `/status`. Shipped:
  `dashboard/app.py` `arcade_counts` on `/status`.
- **R6** — unit-test the three bake generators. Shipped:
  `review/tests/test_gen_snapshot.py` + `test_gen_fleet.py` + `test_gen_stats.py`.
- **C9** — pagination-truncation tests. Shipped: `tests/test_pr_truncation_cap.py`.
- **C11** — cache-eviction test. Shipped: `tests/test_github_cache_eviction.py`.

---

## Ranked next tasks (open), grouped by service

Post-prune, the executable seat frontier is one feature (B6) plus two review
items kept with status notes. Full grooming + routed-out tail:
`docs/plans/next-cycle-2026-07-18.md`.

### 1 · control-plane (`app/`)

Drained — C14 / C15 / C1 all shipped (see "Verified shipped" above). No open
seat-buildable item; new console work now needs owner product intent.

### 2 · review (`review/`)

- **R1 — `/questions` surface** (S · ✅). **NAV half DONE** — `/questions` is in
  NAV (router-introspection NAV-completeness guard, #416). The **seeding half of
  the original ask is declined**: seeding the ledger from the anticipated
  QUESTIONNAIRE Q&A *contradicts the honest-empty design choice* (`questions.json`
  is intentionally `[]` until real questions are answered). Superseded by the
  groomed-queue item "**`/questions` empty-state polish**" (verify/add a graceful
  "no questions answered yet" empty state) — see `docs/plans/next-cycle-2026-07-18.md` §4.
- **R10 — continuous reviews auto-draft the next edition from snapshot deltas**
  (M · ↩️; **routed out — bake-gated**). Needs **R8** stats-history first and a
  bake-step / workflow change, so it lands as its **own PR at the hub venue**, not
  a seat PR. Kept here as the tracked routed-out item.

### 3 · botsite (`botsite/`)

Drained — A4 / A2 both shipped (see "Verified shipped" above).

### 4 · dashboard (`dashboard/`)

- **B6 — config-drift flags on `/env`** (M · ↩️). **The sole open seat-buildable
  feature.** Cross-check `/env` usage against a committed manifest and flag
  referenced-but-unset / set-but-unused vars — the same class as the two
  password-variable cleanups in `docs/OWNER-STEPS.md`. `dashboard/app.py`
  `env_page` currently renders only `data_source.env_usage(data)` with no manifest
  cross-check. *Unblocks:* config drift is visible before a deploy surprises
  someone. Gate: none (`/env` is a read-only GET). Groomed detail:
  `docs/plans/next-cycle-2026-07-18.md` §1.

### Cross-cutting quick win

- **X2 test/guard bundle — largely landed.** The pure test/guard adds **C9**
  (pagination-truncation) + **C11** (cache-eviction) + **R6** (bake-generator
  tests) are all shipped (see "Verified shipped"). Any remaining behaviour-free
  coverage (e.g. R7) can still ride a single green PR.

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
