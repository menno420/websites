# 2026-08-20 — review site: static-export mechanism (slice 3a — exporter + Pages workflow + bake-schedule retirement)

> **Status:** `complete` — branch `claude/review-static-export`, PR #509.
> This flip releases the born-red hold under the two-round cap (R1 6/6 +
> R2 3/3 conceded and fixed; reviewed heads `f8af9a6` and `b43ba53`; the
> R2-fix commit `16bdfaa` lands dispositioned, stated not inferred — the
> kit #581 precedent). The flip commit changes only this card's close-out
> text (the session-close exemption, taken and named). Second PR of the
> keep-bot-only execution: 3a this mechanism; 3b the nav cutover follows
> once Pages actually serves.

- **📊 Model:** fable-5 · high · mechanical refactor

## previous-session review

The previous card (2026-08-20, gate-seat-era-routes, PR #508) closed clean
the same hour: merged `74410ff`, live-verified (healthz 5×200 < 0.62 s;
anonymous `/orders` 42 B; owner Basic 200 at 620,461 B — the exact audited
page size). Nothing it recorded contradicts this tree.

## Why

The program-review audience concluded 2026-07-21; the review service is a
24/7 Railway process server-rendering committed data (`review/data/**` +
committed editions — 20 GET routes, zero POST page routes). The owner's
2026-08-20 keep-criterion (*"only things actually related to the bot"*)
retires it after a static export (worklist § 2, decided § 3.3). The Pages
preflight ran this session: `GET /repos/menno420/websites/pages` → 404, then
`POST` (build_type `workflow`) → **201** over the direct PAT — the measured
2026-08-07 wall was a WORKFLOW token failing to create; the admin-PAT path
works. Venue: https://menno420.github.io/websites/.

## Scope (this PR)

- `review/gen_static.py` — walks every GET route offline (TestClient; the
  clarity suite's own expanders), writes the tree, rewrites root-relative
  URLs for the `/websites` base path + feed absolute URLs, exits 1 on any
  non-200 (a partial tree never deploys as whole).
- `.github/workflows/review-pages.yml` — build + deploy on
  `workflow_dispatch` and review/** pushes to main; no cron.
- `review-bake.yml` schedule retired (cron out, `workflow_dispatch` kept —
  sb #2446 pattern, note in header).
- Decision entry D-0037 (the whole slice-3 mechanism + the named losses).

NOT this PR (3b, after Pages verified serving): fleet-nav repoints ×4,
`web_presence.json` rows (review → Pages URL; mineverse row out — its
Railway service + project were deleted this session), `serviceDelete` of
`review` (id `511fd9eb…`), current-state truth update.

## Shipped

- `review/gen_static.py` (35 routes, exit-1-on-partial, explicit
  FILE_SUFFIXES mapping, href/src/**action** base-path rewrite + feed
  absolute-URL move, sets `REVIEW_STATIC_EXPORT`) ·
  `.github/workflows/review-pages.yml` (dispatch + review/** push;
  `GIT_SHA` into the export; the push trigger's REAL coverage documented —
  measured: zero push-event runs exist on main, so auto-merged landings
  never fire it) · `review-bake.yml` schedule retired + post-direct-push
  `gh workflow run review-pages.yml` (the GITHUB_TOKEN-suppression class).
- Static render mode: `_listfilter.html` (mirrored byte-identical to app/ +
  botsite per the vendored-copy guards) and `ask.html` drop the live-only
  surfaces with honest retirement notes; `base.html` aging-banner wording
  updated for on-demand refresh; seeded answers survive.
- `review/tests/test_static_export.py` (14 pins, both directions) + env-guard
  updates (coderefs snapshot, hostile-env poison list, railway.py +
  environments.json declarations). Decisions ledger D-0037.

## Verify

- Suites: tests/ + review/tests + dashboard/tests = **1496 passed, 0
  failed** (botsite's 171 local fails reproduce identically on the clean
  tree — the known venv-vs-CI drift; CI's pinned env is green on main).
- Exporter run four times across two venvs; final tree: 35 routes,
  `fleet/codetool-lab-opus4.8/index.html` a directory index, zero
  un-prefixed root-relative URLs, static notices rendered.
- Codex round 1: **6 findings, 6 [conceded] and fixed** (commit `b43ba53`) —
  bake-push suppression, form actions, GIT_SHA, static filters, static /ask,
  dotted-segment paths. Round 2 at `b43ba53`: **3 findings, 3 [conceded]
  and fixed** (commit `16bdfaa`) — export-anchor banner for frozen relative
  ages · per-page `noindex, nofollow` (a project site cannot claim the
  origin-root robots.txt) · `build_only` drift classification. Suites after
  R2: **1499 passed**; 19 exporter pins.

## Session idea

- 💡 The live review service carries a working `ANTHROPIC_API_KEY` — the
  `/ask/api` POST (the on-site AI assistant) is a functional path that DIES
  with the static export; the seeded evidence-backed answers survive as
  static content and the exported page renders the honest degraded state.
  Named in D-0037 and flagged to the owner rather than silently dropped.
