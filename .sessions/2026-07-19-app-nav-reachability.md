# 2026-07-19 — app/: NAV reachability GET guard (control-plane)

> **Status:** `in-progress` — branch `claude/app-nav-reachability`. Born red:
> this card's in-progress Status holds the `quality` gate red until the new
> reachability guard lands green; the flip to `complete` is the LAST step and
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

- (pending flip — filled at completion.)

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
