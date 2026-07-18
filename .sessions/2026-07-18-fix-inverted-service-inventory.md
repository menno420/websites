# 2026-07-18 — Fix inverted canonical/duplicate service inventory to match live Railway

> **Status:** `in-progress` — branch `claude/fix-inverted-service-inventory`;
> flips to `complete` + PR number as the deliberate LAST code step.

- **📊 Model:** Claude Opus 4.8 · high · runtime bugfix

**What this session was about:** a proven data-integrity bug. The repo's
service inventory had the OLD/NEW (canonical vs duplicate) project membership
INVERTED relative to live Railway ground truth (verified coordinator-side via
the Railway API + live `/version` reads — authoritative). The repo labeled the
`superbot-websites` project deploys (`abb0`/`a91b`/`cfd7`/`fc91`) as the
duplicates and the `reliable-grace` ones (`f027`, `superbot-dashboard`,
`superbot-app`) as canonical — backwards, so a consolidation cutover run off
this data would retire the estate we KEEP and the review redirect + deploy-drift
healthchecks would probe/point at the retire target. Rung: coordinator-dispatched
data-integrity fix (decide-and-flag, fully reversible — all in git; prerequisite
for the safe consolidation cutover).

Ground truth (KEEP = `superbot-websites`, `70198ece…`): control-plane
`control-plane-production-abb0`, dashboard `dashboard-production-a91b`, botsite
`botsite-production-cfd7`, review `review-production-fc91`. OLD/retire
(`reliable-grace`, `285dfbcd…`): review `review-production-f027` (`menno420/websites`
code), dashboard `superbot-dashboard.up.railway.app` (`menno420/superbot`),
botsite `superbot-app.up.railway.app` (`menno420/superbot`), worker (no domain,
the live Discord bot — NOT a website, never retire).

## What was done

- **`dashboard/app.py`:** `REVIEW_REVIEWS_URL` default `review-production-f027`
  → `review-production-fc91` (the redirect must forward to the KEEP service, not
  the retire target); the misleading comment that called `f027` the keep target
  and `fc91` the retired copy corrected to match ground truth. `BOTSITE_GAMES_URL`
  default `cfd7` was already correct (canonical botsite) — left as-is.
- **`app/config.py`:** `SERVICE_DEPLOY_TARGETS["review"]` `f027` → `fc91` (the
  deploy-drift board must probe the KEEP service's `/version`).
- **`app/railway.py`:** review SERVICES `url` `f027` → `fc91` (kept consistent
  with config.py so `test_deploy_target_single_source` stays green); the
  dashboard manifest's `REVIEW_REVIEWS_URL` description default `f027` → `fc91`.
- **`app/data/web_presence.json`:** un-inverted the directory registry —
  canonical rows now carry the `superbot-websites` domains (`review`→`fc91`,
  `botsite`→`cfd7`, `dashboard`→`a91b`, all `live-service`) and the
  duplicate/old rows carry the `reliable-grace` domains (`review-dup-f027`→`f027`,
  `botsite-dup-superbot-app`→`superbot-app`, `dashboard-dup-superbot-dashboard`→
  `superbot-dashboard`). Dup ids renamed off the now-canonical hashes so the id
  no longer contradicts the url; `duplicate_of` still points at the canonical
  row ids; notes/kind/project corrected to match; reliable-grace project blurb
  reworded (the dashboard/botsite olds are `menno420/superbot` code, only the
  f027 review is a websites-code copy).
- **`app/data/environments.json`:** same inversion fixed —
  `superbot-websites/review` url `f027`→`fc91`; reliable-grace `review-dup-fc91`
  → `review-dup-f027` (url `f027`) and `botsite-dup-cfd7` →
  `botsite-dup-superbot-app` (url `superbot-app`); notes corrected.
- **`scripts/healthcheck.py` + `scripts/smoke_crawl.py`:** review probe URL
  `f027` → `fc91` and the header comments that pinned `f027` as canonical / `fc91`
  as the parallel copy corrected.
- **`review/story.py`:** the `SERVICES` review url `f027` → `fc91`.
- **tests:** `tests/test_healthcheck_services.py` (expected review url + the
  `test_review_service_probes_canonical_*` pin + the no-`fc91` assertion flipped
  to no-`f027`), `tests/test_web_directory.py` (`DUPLICATE_IDS` set + SEED_URLS),
  `tests/test_envhub.py` (railway SERVICES review url + rendered-text pin) —
  all updated to the corrected ground truth.
- **Verified:** [[fill: pytest four-suite result + exit]]; [[fill: bootstrap
  check --strict verdict]]; [[fill: --require-session-log HOLD only on this card]].
  Commits: [[fill: hashes]].

⚑ Self-initiated: no — coordinator-dispatched data-integrity fix (duplicate-sites
consolidation track prerequisite).

## 💡 Session idea

**A committed `railway-ground-truth.json` + a test that pins the inventory to
it.** This inversion survived because canonical-vs-duplicate lived as scattered
url literals and prose across eight files with nothing tying them to the one
authoritative fact — which project each live hostname deploys from. A single
committed map (`hostname → {project, repo, role: keep|retire}`), sourced from a
dated Railway API read, plus one test asserting `web_presence.json` /
`environments.json` / `config.py` / `railway.py` / the healthcheck tables agree
with it, would make the next inversion a red test instead of a latent
estate-retiring bug. Worth having because the whole consolidation cutover's
safety rests on this canonical/duplicate split being right, and today it is only
kept by hand across many files. Deduped against `docs/ideas/backlog.md` + the
NEXT list: not present (the backlog's consolidation entry is the cutover
plan-doc / retirement step, not a ground-truth-pin test). Captured in
`docs/ideas/backlog.md`.

## ⟲ Previous-session review

`.sessions/2026-07-18-dashboard-consolidation-redirects.md` (PR #406) shipped
the `/games` + `/reviews` consolidation redirects cleanly and did well to make
the targets env-overridable and honest-degrade when unresolved — but it hard-set
the `/reviews` default to `f027` on the good-faith but INVERTED belief that
`f027` was the canonical review service (it even flagged the divergence from the
coordinator's `fc91` hint as a deliberate choice). The coordinator's live-Railway
ground truth shows `fc91` is canonical; this session corrects that default and
the inventory it rested on — the right lesson is that a self-consistent repo can
still be uniformly wrong against reality, which is exactly what a ground-truth pin
would catch.
