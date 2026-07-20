# 2026-07-19 — app/: NAV reachability GET guard (control-plane)

> **Status:** `complete` — branch `claude/app-nav-reachability`, PR #450. Born
> red: this card's in-progress Status held the `quality` gate red until the new
> reachability guard landed green; this flip to `complete` is the LAST step and
> releases the `[session-card-hold]`.

- **📊 Model:** opus-4.8 · low · test writing

**What this session is about:** the four services each carry a router-derived
NAV guard that proves every top-level GET route is *classified* — botsite,
dashboard, and review use `test_nav_completeness.py` (NAV / NON_PAGE_PATHS /
PAGES_NOT_IN_NAV), and `app/` uses `tests/test_nav_manifest.py`, which holds
every route's `active` key to the `app/nav.py` manifest. Three of the four then
also got a *reachability* GET guard (PRs #416/#418/#421): a `TestClient` GET
over their page routes asserting the page still responds (non-5xx), so a route
that stays registered while throwing at request time fails loudly instead of
slipping past CI. `app/` never got that second guard — `test_nav_manifest.py`
asserts classification only (no `TestClient`/`client.get`/`status_code`), and
while `tests/test_category_ia.py` GETs the *manifest* hrefs, the 21 top-level
GET routes that are NOT in the manifest (JSON/XML feeds, `/journal/search`,
`/owner/login`, the gated `/owner/*` twins and action previews) are never
reachability-probed at all. This session closes that gap for `app/`, completing
the reachability property across all four services (plan slice 2 of
`docs/plans/next-cycle-2026-07-19.md`).

## Plan

- Extend `tests/test_nav_manifest.py` (the `app/` classification file — the
  analog of the siblings' single `test_nav_completeness.py`, which carries both
  classification and reachability) with one router-derived reachability test.
- Mirror the sibling `_iter_get_routes` / `_top_level_get_paths()` helpers so
  the guard derives its truth from the FastAPI router (not the hand-maintained
  manifest) — this is what lets it probe routes the manifest omits.
- Offline-mock `app.github` (mirroring `test_category_ia._offline`) so the
  guard is hermetic and fast, then `TestClient(app).get(...)` each top-level
  GET route with `follow_redirects=False` and assert `status_code < 500` (the
  non-5xx reachability floor). For the gated `/owner/*` pages, additionally
  assert the status is in the documented `{401, 503}` set (`require_owner`
  fail-closed: 503 when `SITE_PASSWORD` is unset — the CI default — 401 on
  bad/missing creds), with `/owner/login` documented as the public 200 door
  that renders before the gate.
- Test-only: no `app/` route, template, or workflow touched.

⚑ Self-initiated: no — coordinator-assigned slice, promoting the
`2026-07-18-nav-reachability-guard.md` card's 💡 ("Reachability guard for
`app/` control-plane pages") from a flagged gap into shipped tests.

## What was done

- Extended `tests/test_nav_manifest.py` with one router-derived reachability
  test, `test_every_top_level_get_route_is_reachable` (test-only; the existing
  four classification tests are unchanged). It enumerates every top-level GET
  route from the FastAPI router via `_iter_get_routes` / `_top_level_get_paths()`
  (copied verbatim from the sibling `test_nav_completeness.py`), offline-mocks
  `app.github` via a local `_offline` helper (mirroring `test_category_ia`), and
  `TestClient(app).get(path, follow_redirects=False)` each of the 42 top-level
  GET routes. Three mutually-exclusive branches: a public route must return
  `status_code < 500` (the non-5xx floor); a gated `/owner/*` route must return
  a status in the documented `GATED_ALLOWED_STATUS = {401, 503}` set; and the
  one documented `/owner`-prefixed public page, `/owner/login` (the login door
  that renders before the gate), must return 200 via `GATED_STATUS_OVERRIDES`.
- Derived every allowed status by GETting the routes first, never invented:
  offline + no auth, the **31 public routes all return 200**; the **10 gated
  `/owner/*` routes all return 503** (`require_owner` fail-closed with neither
  `SITE_PASSWORD` nor Discord OAuth configured — the CI default; a set with
  `401` too because that is what the same gate returns when a password IS set
  but the creds are wrong/missing, confirmed against `app/owner.py:183-232`);
  `/owner/login` returns **200** (the door renders before the gate). No route
  5xxed unexpectedly — the guard surfaced no real bug, it pins the healthy
  baseline.
- One design note vs the sibling: the sibling probes only its small
  `PAGES_NOT_IN_NAV` off-nav bucket, but `app/` has no such hand-list — its IA
  is a manifest, and `tests/test_category_ia.py` already GETs the 21 *manifest*
  hrefs. So this guard derives from the **router** (the sibling's own
  truth-source) rather than the manifest, making it a strict superset that also
  probes the 21 top-level routes the manifest omits (JSON/XML feeds,
  `/journal/search`, `/owner/login`, the gated `/owner/*` twins + action
  previews) — the routes that would otherwise 5xx unwatched. The core `503 is
  itself a 5xx` wrinkle (the gated pages' documented fail-closed status) is why
  the gated branch is checked for exact `{401,503}` membership rather than the
  blunt `< 500` floor.
- No production code change — `app/` routes, templates, `app/nav.py`, and
  workflows are untouched. `control/claims/app-nav-reachability-2026-07-19.md`
  is removed in this flip commit so it merges away clean (no drift-gate orphan).
- Verified (CI-equivalent, `DATABASE_URL` unset):
  `env -u DATABASE_URL python3 -m pytest tests/ botsite/tests dashboard/tests review/tests -q`
  → **2084 passed** (exit 0; 2083 baseline + 1 new reachability test);
  `python3 bootstrap.py check --strict` → the only gating red is this card's
  born-red `[session-card-hold]`, released at this flip (the other output is
  pre-existing model-line advisories on unrelated cards, never exit-affecting).

## 💡 Session idea

**Fold the `app/` reachability guard's router-derivation into
`test_category_ia.py`'s manifest walk so there is ONE reachability truth for
`app/`, not two.** After this slice, `app/` has two reachability probes that
overlap: `test_category_ia::test_every_manifest_route_responds` GETs the 21
manifest hrefs (asserting 200/non-404), and this new guard GETs all 42
router routes (asserting non-5xx). The router-derived guard is the strict
superset — it already covers every manifest href plus the 21 the manifest
omits. A successor could retire the narrower manifest-only walk in favor of the
router-derived one (keeping `test_category_ia`'s *content* assertions — the
landing-page row/link checks — which are a different property), so the fleet
has exactly one "does every route respond" guard per service instead of a
partial one plus a full one. Test-only, reversible, and it removes a latent
"which reachability test owns this?" ambiguity. Deduped against
`docs/ideas/backlog.md` + the NEXT list: not present. To capture in
`docs/ideas/backlog.md`.

## ⟲ Previous-session review

`.sessions/2026-07-19-submissions-store-shim.md` (#449, plan slice 1) did the
right thing by proving a shared module has *two real consumers* rather than
declaring the extraction done at one — a shim with a single consumer is only
half-shared, and the second consumer is where the "did the dedupe actually
dedupe?" proof lives; it also ended on a precisely-scoped 💡 (an executable
single-owner drift guard) instead of stretching its behaviour-preserving
re-route to also add the guard. The lesson this card carries forward into the
sibling nav work: a *classification* guard that never GETs the route is the
same half-proof shape — it shows a route is registered but not that it
responds — so this slice adds the missing behavioural half for `app/`, and
(like slice 1's 💡) flags the follow-on consolidation rather than folding it in
here.
