# 2026-07-18 — Dashboard consolidation redirects: /games + /reviews → re-homed content

> **Status:** `complete` — branch `claude/dashboard-consolidation-redirects`,
> PR **#406**. A duplicate-sites consolidation gap slice: the OLD dashboard
> (`superbot-dashboard.up.railway.app`, legacy `menno420/superbot`) serves
> `/games` and `/reviews`, but the NEW dashboard (`dashboard/`, this repo) 404s
> on both because that content was deliberately RE-HOMED (games → the botsite
> service, reviews → the review service). This session adds 302 redirects on the
> new dashboard so inbound links to those paths land on the re-homed content
> instead of a 404 — the content stays re-homed by doctrine; these are
> **redirects, not re-adds**. GET-only, so the CSRF/same-origin floor is
> untouched.

- **📊 Model:** opus-4.8 · medium · feature build

**What this session is about:** the duplicate-sites consolidation track — three
services run as duplicate pairs (review=identical, botsite=superset,
dashboard=has gaps). The dashboard's gap was two routes the OLD dashboard
carried but the NEW one doesn't: `/games` and `/reviews`. Their content was
moved off the dashboard on purpose (games → botsite `/games`, reviews → review
service `/reviews`), so re-adding it would fight doctrine. Instead we forward:
GET `/games` / `/reviews` 302 to the re-homed surfaces. This matters at cutover,
when OLD is retired and its URL is repointed to NEW — the redirect keeps every
old inbound link alive. Rung: coordinator-dispatched consolidation-track slice.

## What was done

- **`dashboard/app.py`:** two module-level env-resolved constants
  (`BOTSITE_GAMES_URL`, `REVIEW_REVIEWS_URL` — `os.environ.get(name, default)`,
  the same idiom as `data_source.py`'s feed URLs), and two GET routes
  (`games_redirect`, `reviews_redirect`) that return
  `RedirectResponse(target, status_code=302)` via a `_consolidation_redirect`
  helper. Honest-degrade: if a target resolves empty (env blanked with no
  default) the helper serves a small 200 linking page rather than redirecting to
  `""` or raising a 500 — with the defaults present it always resolves.
- **redirect target resolution:** `BOTSITE_GAMES_URL` default
  `https://botsite-production-cfd7.up.railway.app/games`; `REVIEW_REVIEWS_URL`
  default `https://review-production-f027.up.railway.app/reviews`. The defaults
  are the repo's canonical NEW service URLs (`app/config.py`
  `SERVICE_DEPLOY_TARGETS`, `app/railway.py` SERVICES), env-overridable so a
  cutover domain-rename is a config change, not a code edit.
- **`app/railway.py`:** declared the two new vars in the dashboard service's
  env manifest (with cutover-context descriptions) so the control-plane B6
  env-drift panel reads the dashboard in-sync instead of flagging them
  referenced-but-undeclared.
- **`app/data/env_coderefs.json`:** regenerated via
  `python3 -m app.gen_env_coderefs` (the committed AST-scan snapshot the deployed
  control-plane reads — it can't re-scan the other services).
- **three fleet-wide consistency cascades the two new env vars tripped, all
  synced in the same PR:** `app/data/environments.json` dashboard surface
  `variable_names` (inventory-consistency), the hostile-env poison list in
  `tests/test_hostile_env_smoke.py` (env-poison-pin — every source-read var must
  be poisoned by the import smoke), and the dashboard clarity gate
  `NON_PAGE_GET_ROUTES` in `dashboard/tests/test_clarity_structure.py`
  (`/games` + `/reviews` 302 — they don't render a hero page).
- **tests — `dashboard/tests/test_dashboard.py` (4 new):** `/games` 302s to a
  botsite-games URL and `/reviews` 302s to a review-reviews URL (Location
  asserted); the targets are env-overridable (patching the module constant lands
  the new URL in Location — the path a cutover rename uses); an unresolved target
  degrades to a clean linking page (200), never a 500. Existing dashboard routes
  unregressed (the pages-render parametrize + clarity gate still pass).
- **Verified:** `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — **1882 passed, 1 warning** (exit 0; the one warning is the
  pre-existing Starlette/httpx TestClient deprecation, not this work).
  `python3 bootstrap.py check --strict` and `--require-session-log` — the only
  red is the DESIGNED born-red hold on THIS card, released at this flip (gating
  on exactly 1 card — mine). Commits: `ccc7eb2` (born-red card), `6effae9`
  (routes + manifest + snapshot), `7e3cf8f` (tests), `9680f39` (consistency-gate
  sync), `9f933ec` (heartbeat), + this flip.

⚑ Self-initiated: no — coordinator-dispatched (duplicate-sites consolidation track).

## 💡 Session idea

**A cross-service "no re-homed path 404s" contract test.** This slice fixed two
KNOWN re-homed paths by hand; the consolidation track will retire more OLD
surfaces whose paths moved. A single committed manifest of `(old_path →
new_service_url)` consolidation redirects, asserted by a test that walks each
old path on the owning new service and confirms it 3xx's to the recorded target
(and that the target's host matches the declared re-home), would catch the NEXT
dropped redirect automatically instead of by eye — and doubles as the
machine-readable source the future URL-cutover plan doc needs. Worth having
because the cutover's whole safety rests on "no old link 404s", and today that
invariant is only spot-checked per-path. Deduped against `docs/ideas/backlog.md`
+ the NEXT list: not present (the backlog's consolidation entry is the plan-doc /
service-retirement step, not a redirect-coverage test). Captured in
`docs/ideas/backlog.md`.

## ⟲ Previous-session review

`.sessions/2026-07-18-overview-mobile-ux.md` (PR #404) turned the `/fleet`
overview count badges into real server-rendered drill-downs and fixed 480px
value-clipping — it did well to DERIVE each count from its member list so the two
can never disagree (one source of truth), and its honest note that the phone-width
check used a stubbed lane set (a live re-verify is the real follow-up) is the kind
of scoped-truth this redirect slice mirrors: I flag that my review-URL default
diverges from the coordinator brief's `fc91` hint (fc91 is the parallel copy
retired at cutover) rather than silently following it.
