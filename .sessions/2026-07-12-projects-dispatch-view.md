# 2026-07-12 — /projects dispatch view: seat-first index + per-seat copy-ready prompt screen

> **Status:** `complete` — branch `claude/projects-dispatch-view`, PR #158
> (parks READY + green awaiting the owner's merge click — no auto-merge on
> this repo).

- **📊 Model:** claude-fable-5 · worker (owner dispatch directive) · feature-build

**What this session was about:** Owner single-screen dispatch ask (2026-07-12):
dispatching all 8 fleet seats today means clicking through to GitHub raw files
and hand-copying prompt text. Build the Owner Launch Console on control-plane.
Rung: owner-directed; scope verified unclaimed (`control/claims/` empty of
overlaps, no open PR touching /projects at branch time).

## What was done

- `app/projects.py` — `start_rank()` (owner start order: fleet-manager/
  project-manager → venture-lab → superbot-world → superbot-2.0/superbot-next
  → ideas-lab → game-lab → self-improvement → websites; unmatched after,
  alphabetical), `is_stub()` (fail-ACTIVE: only unambiguous retired /
  merged-into / stub declarations in the meta state line or early meta.md
  body demote a package — prose like "PR #12 merged" never hides a seat),
  `extract_env()` + `extract_project_url()` (same honest-absence contract as
  `extract_state`), and NEW `detail()` — one seat's dispatch data: package
  membership validated against the live registry listing (traversal shapes
  and unknown names → `not-found`), every recognized role file (instructions
  / coordinator / failsafe / setup / meta / routine) fetched in FULL through
  the TTL-cached `github` layer, per-file `fetch_error` degradation, same
  empty / not-configured / unavailable ladder as `overview()`. Packages sort
  seats-first in start order, stubs last; each carries `stub` + `detail_url`.
- `app/main.py` — NEW `GET /projects/{package}` (404 only on `not-found`;
  degraded registry states render 200 banner pages).
- `app/templates/projects.html` — Seats section first (cards link to the
  dispatch screen), retired/merged stubs collapsed in a `<details>` below
  (visible, never hidden); `app/templates/project_detail.html` — meta table
  (deployed-state badge / environment / "open Project ↗" link, absent =
  unknown / none recorded), static 3-step dispatch checklist (failsafe file
  anchor-linked; honest note when no failsafe is recognized), one card per
  role file with the FULL text in a `<pre>`, other files link-only.
- `app/static/copycode.js` — kept as the shared copy-button mechanism (the
  /environments pattern) and extended with a hidden-textarea
  `document.execCommand("copy")` fallback for non-secure contexts; silent
  degrade to selectable text when neither API exists.
- `tests/test_projects.py` (+11) — start-order/alias ranks, stub tolerance
  both directions, seats-first overview ordering, index split render
  (`<details>` + dispatch links), detail full-content + meta fields, honest
  unknown/none-recorded/absent-failsafe render, unknown + traversal names →
  404, copy-ready markup (`copycode.js` + `<pre>`), per-file fetch-error
  degradation, not-configured / unavailable / empty registry states.
  `tests/test_json_contracts.py` — PROJECTS_PACKAGE pin +`stub`+`detail_url`
  moved SAME-PR per protocol.
- Docs: `docs/site.md` §3d + route table (dispatch console + new route),
  `docs/current-state.md` entry (header date bumped), backlog idea filed.
- Verified: `python3 -m pytest tests/ -q` — **213 passed** (was 202);
  `python3 -m pytest tests/ botsite/tests dashboard/tests review/tests -q`
  — **354 passed**; `python3 bootstrap.py check --strict` — green (only the
  designed born-red hold before this flip). Also render-verified live via
  TestClient with a mocked registry: seats-before-stubs order and
  prompt-text HTML escaping confirmed in the emitted HTML.
- Claim `control/claims/claude-projects-dispatch-view.md` created in the
  first commit (in-flight signal on the open PR) and deleted at this flip
  per the claims README; it could not land on main separately because agent
  merges are owner-gated on this repo.

⚑ Self-initiated: no — owner dispatch directive (2026-07-12).

## 💡 Session idea

**Seat role-coverage chips on the /projects dispatch index** — one chip row
per seat card (instructions ✓ / coordinator ✗ / failsafe ✓, derived from the
role-classified listing the page already fetches — zero extra API calls) so
an incomplete package is visible at a glance instead of at paste time. Worth
having because the single-screen dispatch flow's remaining blind spot is a
seat missing its coordinator prompt or failsafe, discovered mid-dispatch.
Deduped against `docs/ideas/backlog.md` + the queue-state NEXT list: nothing
touches projects-registry completeness. Captured in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

The order-pickup-latency slice (#133) did the sibling-branch check before
picking work and pinned its latency math to a real ride (19.0 min) — both
worth imitating; what it missed: nothing structural. One workflow
improvement this session surfaces: the JSON-contract pin file says "say so
in the PR body" but nothing checks that — a tiny advisory in `check` (pin
constants changed + PR body silent) would make the contract-change ritual
self-enforcing.
