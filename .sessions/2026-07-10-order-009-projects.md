# 2026-07-10 — ORDER 009 increment (1): /projects — the fleet-manager project-package registry page

> **Status:** `complete` — PR #72 (`claude/order-009-projects`),
> squash-merge on `quality` green. (Flipped after the PR existed — number
> real, not predicted.)

- **📊 Model:** Claude Fable 5 · worker · routine-fired build slice (continuous mode, slice 4)

**What this session was about:** slice 4 of the 20:00Z continuous-mode wake —
work-ladder rung 1: **ORDER 009** (inbox, appended 2026-07-10T20:58:44Z via
PR #70, claimed on main via PR #71 `claimed-by: 009 websites-continuous-wake
2026-07-10T21:07Z`). Increment (1): a `/projects` page rendering the
fleet-manager `projects/` registry — per-repo package cards (instructions /
coordinator-prompt / setup / failsafe files + deployed-state from each
package's `meta.md`), fetched from fleet-manager main via the same TTL-cached
github layer as every other page, with honest degradation — the registry
folder is being created RIGHT NOW upstream (verified this session:
`raw/.../projects/README.md` → 404 while the repo root README is 200), so the
honest empty state is the expected launch state; never a 500.

## What was done

- **`app/projects.py`** (new): bounded registry walk (`MAX_PACKAGES=30`,
  `MAX_FILES_PER_PACKAGE=20`) over the TTL-cached contents API; per-package
  cards with `classify_role` basename heuristics (meta / instructions /
  coordinator / setup / failsafe / routine → labeled roles, everything else
  an honest "other"), role-first ordering, `meta.md` rendered via the
  sanitized `journal.render_markdown`, `extract_state` best-effort
  `deployed:`/`state:`/`status:` badge (no line → `""` → "state unknown").
  Degradation ladder: **empty** (404 on `projects/` OR dir-exists-no-content
  — the expected launch state, a friendly "registry not landed yet" banner) /
  **not-configured** (token unset + fetch failed) / **unavailable** (reason
  surfaced) / per-package + per-meta error banners; route always 200.
- **`app/templates/projects.html`** + `app/main.py` routes (`/projects`,
  `/projects.json` with meta HTML stripped — the `/fleet.json` precedent) +
  nav link in `base.html` after `/environments`.
- **ORDER 009 increment (2)** — verified already-covered, skipped per the
  order: `/fleet` computes `updated:` age, stale badge, and attention sort
  for EVERY lane by construction (`lane_status` always attaches `freshness`;
  no lane is exempt) — no increment needed.
- **ORDER 009 increment (3)** — honestly ledgered per the done-when:
  `planned` backlog bullet (review-queue rows + findings links) plus a
  `captured` bullet for the audit's inbox-ORDER-visibility gap (pairs with
  the D-0028 outstanding-orders computation).
- **Docs:** D-0030 in the ledger; `docs/site.md` § 3d + Routes rows.
- **`tests/test_projects.py`** (+8, suites 157 → 165): role heuristics;
  tolerant state extraction + honest absence; empty-on-404,
  dir-exists-but-empty, not-configured vs unavailable; happy-path cards
  (role-first ordering, meta render, state badge); route smoke (200 +
  "registry not landed yet" banner + nav link); JSON shape (meta_html
  stripped).

## Close-out (auto-drafted 2026-07-10 — edit, don't author)

<!-- substrate:auto-draft -->

**Evidence (auto-collected — verify, then keep or correct):**

- files touched: `app/projects.py` (new), `app/templates/projects.html`
  (new), `app/main.py`, `app/templates/base.html`, `tests/test_projects.py`
  (new), `docs/site.md`, `docs/decisions.md` (D-0030),
  `docs/ideas/backlog.md`, this card.
- git: branch `claude/order-009-projects`, HEAD 0eb1b0f42 at draft time (the
  flip commit supersedes it).
- verify: `python3 -m pytest tests/ botsite/tests dashboard/tests -q` —
  **165 passed** (+8); `python3 bootstrap.py check --strict` — **all checks
  passed** with this card complete.

**Judgment (the half only the session knows — resolve every slot):**

- Decisions made: D-0030 (`/projects` registry render with a first-class
  `empty` degradation state — stamped in `docs/site.md` §§ 3d/Routes + the
  ledger); ORDER 009 increment (2) skipped as verified-already-covered;
  increment (3) ledgered to the backlog per the order's done-when.
- Next session should know: `/projects` will show "registry not landed yet"
  until fleet-manager's `projects/` folder actually lands upstream — that is
  CORRECT behavior, not a bug; re-curl the live page once the manager
  finishes the registry. ORDER 009 moves to done= in the heartbeat only for
  increment (1)+(2); increment (3) is the `planned` backlog bullet.

⚑ Self-initiated: no — ORDER 009 (P1), claimed before building per
`control/README.md`.

## 💡 Session idea

**`meta.md` state-line convention in the registry spec** — ask the manager
(via this heartbeat) to standardize ONE `deployed:` line format in
`projects/*/meta.md` while the registry is still forming, e.g.
`deployed: <where> · <ISO date>`. Worth having because `/projects` currently
extracts the state with tolerant heuristics against an unborn format — one
line agreed NOW (while zero packages exist) costs nothing and makes the
badge exact forever, where retrofitting a convention after ten packages land
costs a migration. Deduped against `docs/ideas/backlog.md` + queue-state
NEXT: nothing covers upstream registry conventions. Captured in
`docs/ideas/backlog.md` (routing half: flagged to the manager in the
heartbeat notes).

## ⟲ Previous-session review

Slice 3 (same wake, PR #69) closed its loop properly — it dispatched the new
workflow post-merge and recorded the real run conclusion (success, run
29123498090) instead of assuming a cron would fire someday; what it missed:
its born-red PR drew a coordinator CI-failure escalation for a red that was
the session gate working AS DESIGNED. Workflow improvement: when opening a
PR that will sit red by design, say so in the PR body up front (this slice
did) and still expect the watcher to flag it — the alternative (flip before
opening) re-creates the number-prediction bug, so the small noise is the
better trade.
